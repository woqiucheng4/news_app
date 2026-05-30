import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../domain/models/feed_item.dart';
import '../../data/repositories/feed_repository.dart';
import 'feed_data_providers.dart';

final topicFeedHasMoreProvider = StateProvider.family<bool, String>((ref, topicId) => true);
final topicFeedLoadingMoreProvider =
    StateProvider.family<bool, String>((ref, topicId) => false);
final topicFeedLoadMoreErrorProvider =
    StateProvider.family<Object?, String>((ref, topicId) => null);

final topicFeedNotifierProvider =
    AsyncNotifierProvider.family<TopicFeedNotifier, List<FeedItem>, String>(
  TopicFeedNotifier.new,
);

class TopicFeedNotifier extends FamilyAsyncNotifier<List<FeedItem>, String> {
  int _page = 1;

  String get _topicId => arg;

  @override
  Future<List<FeedItem>> build(String topicId) async {
    _page = 1;
    ref.read(topicFeedHasMoreProvider(topicId).notifier).state = true;
    ref.read(topicFeedLoadingMoreProvider(topicId).notifier).state = false;
    ref.read(topicFeedLoadMoreErrorProvider(topicId).notifier).state = null;

    final result = await ref.read(feedRepositoryProvider).getFeedPage(
          page: 1,
          topicId: topicId,
        );
    _applyFetchMetadata(topicId, result);
    unawaited(_prefetchArticlePreviews(result.page.articles));
    return result.page.articles;
  }

  Future<void> reload() async {
    _page = 1;
    ref.read(topicFeedLoadMoreErrorProvider(_topicId).notifier).state = null;
    ref.read(topicFeedLoadingMoreProvider(_topicId).notifier).state = false;

    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final result = await ref.read(feedRepositoryProvider).getFeedPage(
            page: 1,
            topicId: _topicId,
            forceNetwork: true,
          );
      _applyFetchMetadata(_topicId, result);
      unawaited(_prefetchArticlePreviews(result.page.articles));
      return result.page.articles;
    });

    if (!state.hasError) {
      ref.read(appAnalyticsProvider).trackFeedRefresh(source: 'topic_feed');
    }
  }

  Future<void> loadMore() async {
    final hasMore = ref.read(topicFeedHasMoreProvider(_topicId));
    final isLoadingMore = ref.read(topicFeedLoadingMoreProvider(_topicId));
    final current = state.valueOrNull;
    if (!hasMore || isLoadingMore || current == null) {
      return;
    }

    ref.read(topicFeedLoadingMoreProvider(_topicId).notifier).state = true;
    ref.read(topicFeedLoadMoreErrorProvider(_topicId).notifier).state = null;

    try {
      final nextPage = _page + 1;
      final result = await ref.read(feedRepositoryProvider).getFeedPage(
            page: nextPage,
            topicId: _topicId,
          );
      _page = nextPage;
      ref.read(topicFeedHasMoreProvider(_topicId).notifier).state = result.page.hasMore;
      unawaited(_prefetchArticlePreviews(result.page.articles));
      state = AsyncData([...current, ...result.page.articles]);
    } catch (error) {
      ref.read(topicFeedLoadMoreErrorProvider(_topicId).notifier).state = error;
    } finally {
      ref.read(topicFeedLoadingMoreProvider(_topicId).notifier).state = false;
    }
  }

  Future<void> _prefetchArticlePreviews(List<FeedItem> items) async {
    if (items.isEmpty) {
      return;
    }
    await ref.read(articleDetailRepositoryProvider).cachePreviewFromFeedItems(items);
  }

  void _applyFetchMetadata(String topicId, FeedFetchResult result) {
    ref.read(topicFeedHasMoreProvider(topicId).notifier).state = result.page.hasMore;
  }
}
