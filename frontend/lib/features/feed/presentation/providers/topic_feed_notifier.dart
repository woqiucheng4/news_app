import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../data/repositories/feed_repository.dart';
import '../../domain/models/feed_item.dart';
import '../../domain/models/feed_page.dart';
import 'feed_data_providers.dart';

class TopicFeedScope {
  const TopicFeedScope(this.topicId);

  final String topicId;
}

final topicFeedScopeProvider = Provider<TopicFeedScope>((ref) {
  throw UnimplementedError('Override topicFeedScopeProvider in TopicFeedScreen');
});

final topicFeedHasMoreProvider = StateProvider<bool>((ref) => true);
final topicFeedLoadingMoreProvider = StateProvider<bool>((ref) => false);
final topicFeedLoadMoreErrorProvider = StateProvider<Object?>((ref) => null);

final topicFeedNotifierProvider =
    AsyncNotifierProvider<TopicFeedNotifier, List<FeedItem>>(
  TopicFeedNotifier.new,
);

class TopicFeedNotifier extends AsyncNotifier<List<FeedItem>> {
  int _page = 1;

  String get _topicId => ref.watch(topicFeedScopeProvider).topicId;

  @override
  Future<List<FeedItem>> build() async {
    _page = 1;
    ref.read(topicFeedHasMoreProvider.notifier).state = true;
    ref.read(topicFeedLoadingMoreProvider.notifier).state = false;
    ref.read(topicFeedLoadMoreErrorProvider.notifier).state = null;

    final result = await ref.read(feedRepositoryProvider).getFeedPage(
          page: 1,
          topicId: _topicId,
        );
    _applyFetchMetadata(result);
    unawaited(_prefetchArticlePreviews(result.page.articles));
    return result.page.articles;
  }

  Future<void> reload() async {
    _page = 1;
    ref.read(topicFeedLoadMoreErrorProvider.notifier).state = null;
    ref.read(topicFeedLoadingMoreProvider.notifier).state = false;

    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final result = await ref.read(feedRepositoryProvider).getFeedPage(
            page: 1,
            topicId: _topicId,
            forceNetwork: true,
          );
      _applyFetchMetadata(result);
      unawaited(_prefetchArticlePreviews(result.page.articles));
      return result.page.articles;
    });

    if (!state.hasError) {
      ref.read(appAnalyticsProvider).trackFeedRefresh(source: 'topic_feed');
    }
  }

  Future<void> loadMore() async {
    final hasMore = ref.read(topicFeedHasMoreProvider);
    final isLoadingMore = ref.read(topicFeedLoadingMoreProvider);
    final current = state.value;
    if (!hasMore || isLoadingMore || current == null) {
      return;
    }

    ref.read(topicFeedLoadingMoreProvider.notifier).state = true;
    ref.read(topicFeedLoadMoreErrorProvider.notifier).state = null;

    try {
      final nextPage = _page + 1;
      final result = await ref.read(feedRepositoryProvider).getFeedPage(
            page: nextPage,
            topicId: _topicId,
          );
      _page = nextPage;
      ref.read(topicFeedHasMoreProvider.notifier).state = result.page.hasMore;
      unawaited(_prefetchArticlePreviews(result.page.articles));
      state = AsyncData([...current, ...result.page.articles]);
    } catch (error) {
      ref.read(topicFeedLoadMoreErrorProvider.notifier).state = error;
    } finally {
      ref.read(topicFeedLoadingMoreProvider.notifier).state = false;
    }
  }

  Future<void> _prefetchArticlePreviews(List<FeedItem> items) async {
    if (items.isEmpty) {
      return;
    }
    await ref.read(articleDetailRepositoryProvider).cachePreviewFromFeedItems(items);
  }

  void _applyFetchMetadata(FeedFetchResult result) {
    ref.read(topicFeedHasMoreProvider.notifier).state = result.page.hasMore;
  }
}
