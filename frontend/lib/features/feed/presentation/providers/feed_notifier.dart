import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../domain/models/feed_item.dart';
import '../../domain/models/feed_page.dart';
import 'feed_data_providers.dart';

final feedHasMoreProvider = StateProvider<bool>((ref) => true);
final feedLoadingMoreProvider = StateProvider<bool>((ref) => false);
final feedLoadMoreErrorProvider = StateProvider<Object?>((ref) => null);
final feedFromCacheProvider = StateProvider<bool>((ref) => false);
final feedOfflineFallbackProvider = StateProvider<bool>((ref) => false);

final feedNotifierProvider =
    AsyncNotifierProvider<FeedNotifier, List<FeedItem>>(FeedNotifier.new);

class FeedNotifier extends AsyncNotifier<List<FeedItem>> {
  int _page = 1;

  @override
  Future<List<FeedItem>> build() async {
    _page = 1;
    ref.read(feedHasMoreProvider.notifier).state = true;
    ref.read(feedLoadingMoreProvider.notifier).state = false;
    ref.read(feedLoadMoreErrorProvider.notifier).state = null;

    final result = await ref.read(feedRepositoryProvider).getFeedPage(page: 1);
    _applyFetchMetadata(result);
    unawaited(_prefetchArticlePreviews(result.page.articles));
    return result.page.articles;
  }

  Future<void> reload() async {
    _page = 1;
    ref.read(feedLoadMoreErrorProvider.notifier).state = null;
    ref.read(feedLoadingMoreProvider.notifier).state = false;

    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final result = await ref.read(feedRepositoryProvider).getFeedPage(
            page: 1,
            forceNetwork: true,
          );
      _applyFetchMetadata(result);
      unawaited(_prefetchArticlePreviews(result.page.articles));
      return result.page.articles;
    });

    if (!state.hasError) {
      ref.read(appAnalyticsProvider).trackFeedRefresh(source: 'pull');
    }
  }

  Future<void> loadMore() async {
    final hasMore = ref.read(feedHasMoreProvider);
    final isLoadingMore = ref.read(feedLoadingMoreProvider);
    final current = state.value;
    if (!hasMore || isLoadingMore || current == null) {
      return;
    }

    ref.read(feedLoadingMoreProvider.notifier).state = true;
    ref.read(feedLoadMoreErrorProvider.notifier).state = null;

    try {
      final nextPage = _page + 1;
      final result =
          await ref.read(feedRepositoryProvider).getFeedPage(page: nextPage);
      _page = nextPage;
      ref.read(feedHasMoreProvider.notifier).state = result.page.hasMore;
      if (result.isOfflineFallback) {
        ref.read(feedOfflineFallbackProvider.notifier).state = true;
      }
      unawaited(_prefetchArticlePreviews(result.page.articles));
      state = AsyncData([...current, ...result.page.articles]);
    } catch (error) {
      ref.read(feedLoadMoreErrorProvider.notifier).state = error;
    } finally {
      ref.read(feedLoadingMoreProvider.notifier).state = false;
    }
  }

  Future<void> _prefetchArticlePreviews(List<FeedItem> items) async {
    if (items.isEmpty) {
      return;
    }
    await ref.read(articleDetailRepositoryProvider).cachePreviewFromFeedItems(items);
  }

  void _applyFetchMetadata(FeedFetchResult result) {
    ref.read(feedHasMoreProvider.notifier).state = result.page.hasMore;
    ref.read(feedFromCacheProvider.notifier).state =
        result.fromCache && !result.isOfflineFallback;
    ref.read(feedOfflineFallbackProvider.notifier).state = result.isOfflineFallback;
  }
}
