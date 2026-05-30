import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/models/topic_category.dart';
import '../../domain/models/topic_item.dart';
import 'subscriptions_notifier.dart';

const int _topicPageSize = 20;

final topicQueryProvider = StateProvider<String>((ref) => '');
final selectedTopicCategoryProvider = StateProvider<String?>((ref) => null);
final topicsHasMoreProvider = StateProvider<bool>((ref) => true);
final topicsLoadingMoreProvider = StateProvider<bool>((ref) => false);
final topicsLoadMoreErrorProvider = StateProvider<Object?>((ref) => null);
final highlightedTopicIdProvider = StateProvider<String?>((ref) => null);
final topicActionLoadingIdsProvider = StateProvider<Set<String>>((ref) => <String>{});
final keywordSubscribingProvider = StateProvider<bool>((ref) => false);
final topicDiscoveryScrollOffsetProvider = StateProvider<double>((ref) => 0);
final topicsFirstPageCacheProvider =
    StateProvider<Map<String, TopicFirstPageCacheEntry>>((ref) => {});

final topicCategoriesProvider = FutureProvider<List<TopicCategory>>((ref) async {
  final repository = ref.watch(subscriptionsRepositoryProvider);
  return repository.getTopicCategories();
});

final topicsDiscoveryNotifierProvider =
    AsyncNotifierProvider<TopicsDiscoveryNotifier, List<TopicItem>>(
  TopicsDiscoveryNotifier.new,
);

class TopicsDiscoveryNotifier extends AsyncNotifier<List<TopicItem>> {
  int _offset = 0;
  Timer? _highlightTimer;
  CancelToken? _firstPageCancelToken;
  CancelToken? _loadMoreCancelToken;

  @override
  Future<List<TopicItem>> build() async {
    ref.onDispose(() {
      _highlightTimer?.cancel();
      _firstPageCancelToken?.cancel('provider disposed');
      _loadMoreCancelToken?.cancel('provider disposed');
    });

    _offset = 0;
    ref.read(topicsHasMoreProvider.notifier).state = true;
    ref.read(topicsLoadingMoreProvider.notifier).state = false;
    ref.read(topicsLoadMoreErrorProvider.notifier).state = null;

    final firstPage = await _fetchFirstPage(preferCache: true);

    _offset = firstPage.length;
    ref.read(topicsHasMoreProvider.notifier).state = firstPage.length == _topicPageSize;
    return firstPage;
  }

  Future<void> refresh({
    bool forceNetwork = false,
    bool preferCache = false,
  }) async {
    final previous = state;
    _offset = 0;
    _cancelLoadMoreRequest();
    ref.read(topicsLoadMoreErrorProvider.notifier).state = null;
    ref.read(topicsLoadingMoreProvider.notifier).state = false;

    state = const AsyncLoading();
    try {
      final firstPage = await _fetchFirstPage(
        forceNetwork: forceNetwork,
        preferCache: preferCache && !forceNetwork,
      );
      _offset = firstPage.length;
      ref.read(topicsHasMoreProvider.notifier).state = firstPage.length == _topicPageSize;
      state = AsyncData(firstPage);
    } on _CancelledRequest {
      state = previous;
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
    }
  }

  Future<void> search(String query) async {
    ref.read(topicQueryProvider.notifier).state = query.trim();
    _clearHighlight();
    await refresh(preferCache: true);
  }

  Future<void> setCategory(String? category) async {
    ref.read(selectedTopicCategoryProvider.notifier).state = category;
    _clearHighlight();
    await refresh(preferCache: true);
  }

  Future<void> hydrateFromUrl({
    String? query,
    String? category,
  }) async {
    final normalizedQuery = (query ?? '').trim();
    final normalizedCategory = (category ?? '').trim();
    final nextCategory = normalizedCategory.isEmpty ? null : normalizedCategory;

    final currentQuery = ref.read(topicQueryProvider);
    final currentCategory = ref.read(selectedTopicCategoryProvider);
    if (currentQuery == normalizedQuery && currentCategory == nextCategory) {
      return;
    }

    ref.read(topicQueryProvider.notifier).state = normalizedQuery;
    ref.read(selectedTopicCategoryProvider.notifier).state = nextCategory;
    _clearHighlight();
    await refresh(preferCache: true);
  }

  Future<void> loadMore() async {
    final hasMore = ref.read(topicsHasMoreProvider);
    final isLoadingMore = ref.read(topicsLoadingMoreProvider);
    final current = state.valueOrNull;
    if (!hasMore || isLoadingMore || current == null) return;

    ref.read(topicsLoadingMoreProvider.notifier).state = true;
    ref.read(topicsLoadMoreErrorProvider.notifier).state = null;

    final repository = ref.read(subscriptionsRepositoryProvider);
    final query = ref.read(topicQueryProvider);
    final category = ref.read(selectedTopicCategoryProvider);
    _loadMoreCancelToken?.cancel('new load more');
    final token = CancelToken();
    _loadMoreCancelToken = token;

    try {
      final nextPage = await repository.getTopics(
        query: query,
        category: category,
        limit: _topicPageSize,
        offset: _offset,
        cancelToken: token,
      );

      _offset += nextPage.length;
      ref.read(topicsHasMoreProvider.notifier).state = nextPage.length == _topicPageSize;
      state = AsyncData([...current, ...nextPage]);
    } on DioException catch (error) {
      if (error.type == DioExceptionType.cancel) {
        return;
      }
      ref.read(topicsLoadMoreErrorProvider.notifier).state = error;
    } catch (error) {
      ref.read(topicsLoadMoreErrorProvider.notifier).state = error;
    } finally {
      if (identical(_loadMoreCancelToken, token)) {
        _loadMoreCancelToken = null;
      }
      ref.read(topicsLoadingMoreProvider.notifier).state = false;
    }
  }

  Future<TopicActionResult> subscribeTopic(String topicId) async {
    final previous = state;
    final current = state.valueOrNull;
    if (current == null) return const TopicActionResult.failure();

    final loadingIds = ref.read(topicActionLoadingIdsProvider);
    if (loadingIds.contains(topicId)) {
      return const TopicActionResult.failure();
    }
    ref.read(topicActionLoadingIdsProvider.notifier).state = {
      ...loadingIds,
      topicId,
    };

    state = AsyncData(
      current
          .map(
            (item) => item.id == topicId && !item.isSubscribed
                ? item.copyWith(
                    isSubscribed: true,
                    subscriberCount: item.subscriberCount + 1,
                  )
                : item,
          )
          .toList(growable: false),
    );

    try {
      final repository = ref.read(subscriptionsRepositoryProvider);
      final result = await AsyncValue.guard(() => repository.subscribe(topicId));
      if (result.hasError) {
        state = previous;
        return TopicActionResult.failure(error: result.error);
      }

      ref.invalidate(subscriptionsNotifierProvider);
      _clearFirstPageCache();
      _setHighlight(topicId);
      return const TopicActionResult.success();
    } finally {
      final latest = ref.read(topicActionLoadingIdsProvider);
      ref.read(topicActionLoadingIdsProvider.notifier).state = {
        ...latest.where((id) => id != topicId),
      };
    }
  }

  Future<TopicActionResult> subscribeKeyword(String keyword) async {
    final normalized = keyword.trim();
    if (normalized.isEmpty) return const TopicActionResult.failure();
    if (ref.read(keywordSubscribingProvider)) {
      return const TopicActionResult.failure();
    }
    ref.read(keywordSubscribingProvider.notifier).state = true;

    try {
      final repository = ref.read(subscriptionsRepositoryProvider);
      final selectedCategory = ref.read(selectedTopicCategoryProvider) ?? 'custom';
      final result = await AsyncValue.guard(
        () => repository.subscribeByKeyword(
          normalized,
          category: selectedCategory,
        ),
      );

      if (result.hasError) {
        return TopicActionResult.failure(error: result.error);
      }

      final topicId = result.value;
      ref.read(topicQueryProvider.notifier).state = normalized;
      ref.invalidate(subscriptionsNotifierProvider);
      ref.invalidate(topicCategoriesProvider);
      _clearFirstPageCache();
      await refresh();
      _setHighlight(topicId);
      return const TopicActionResult.success();
    } finally {
      ref.read(keywordSubscribingProvider.notifier).state = false;
    }
  }

  void _setHighlight(String? topicId) {
    _highlightTimer?.cancel();
    ref.read(highlightedTopicIdProvider.notifier).state = topicId;
    if (topicId == null) return;

    _highlightTimer = Timer(const Duration(seconds: 3), () {
      ref.read(highlightedTopicIdProvider.notifier).state = null;
    });
  }

  void _clearHighlight() {
    _highlightTimer?.cancel();
    ref.read(highlightedTopicIdProvider.notifier).state = null;
  }

  Future<List<TopicItem>> _fetchFirstPage({
    bool forceNetwork = false,
    bool preferCache = false,
  }) async {
    final repository = ref.read(subscriptionsRepositoryProvider);
    final query = ref.read(topicQueryProvider);
    final category = ref.read(selectedTopicCategoryProvider);
    final cacheKey = _buildCacheKey(query, category);

    if (preferCache && !forceNetwork) {
      final entry = ref.read(topicsFirstPageCacheProvider)[cacheKey];
      if (entry != null) {
        ref.read(topicsHasMoreProvider.notifier).state = entry.hasMore;
        return entry.items;
      }
    }

    _firstPageCancelToken?.cancel('new first-page request');
    final token = CancelToken();
    _firstPageCancelToken = token;

    try {
      final firstPage = await repository.getTopics(
        query: query,
        category: category,
        limit: _topicPageSize,
        offset: 0,
        cancelToken: token,
      );
      final hasMore = firstPage.length == _topicPageSize;
      final cache = ref.read(topicsFirstPageCacheProvider);
      ref.read(topicsFirstPageCacheProvider.notifier).state = {
        ...cache,
        cacheKey: TopicFirstPageCacheEntry(
          items: firstPage,
          hasMore: hasMore,
        ),
      };
      return firstPage;
    } on DioException catch (error) {
      if (error.type == DioExceptionType.cancel) {
        throw _CancelledRequest();
      }
      rethrow;
    } finally {
      if (identical(_firstPageCancelToken, token)) {
        _firstPageCancelToken = null;
      }
    }
  }

  void _cancelLoadMoreRequest() {
    _loadMoreCancelToken?.cancel('first page request started');
    _loadMoreCancelToken = null;
  }

  String _buildCacheKey(String query, String? category) {
    return '${query.trim().toLowerCase()}::${(category ?? '').trim().toLowerCase()}';
  }

  void _clearFirstPageCache() {
    ref.read(topicsFirstPageCacheProvider.notifier).state = {};
  }
}

class TopicActionResult {
  const TopicActionResult._({
    required this.success,
    this.error,
  });

  const TopicActionResult.success() : this._(success: true);
  const TopicActionResult.failure({Object? error})
      : this._(
          success: false,
          error: error,
        );

  final bool success;
  final Object? error;
}

class _CancelledRequest implements Exception {}

class TopicFirstPageCacheEntry {
  const TopicFirstPageCacheEntry({
    required this.items,
    required this.hasMore,
  });

  final List<TopicItem> items;
  final bool hasMore;
}
