import '../../domain/models/feed_page.dart';
import '../local/feed_cache_store.dart';
import '../services/feed_api_service.dart';
import '../../../../core/network/network_error_utils.dart';

class FeedRepository {
  FeedRepository(this._apiService, this._cacheStore);

  final FeedApiService _apiService;
  final FeedCacheStore _cacheStore;

  Future<FeedFetchResult> getFeedPage({
    int page = 1,
    int pageSize = feedPageSize,
    bool forceNetwork = false,
    String? topicId,
  }) async {
    if (topicId == null) {
      if (!forceNetwork) {
        final cached = await _cacheStore.readPage(page);
        if (cached != null) {
          return FeedFetchResult(
            page: cached.page,
            fromCache: true,
            isOfflineFallback: false,
          );
        }
      }
    }

    try {
      final pageData = await _apiService.fetchFeed(
        page: page,
        pageSize: pageSize,
        topicId: topicId,
      );
      if (topicId == null) {
        await _cacheStore.writePage(pageData);
      }
      return FeedFetchResult(
        page: pageData,
        fromCache: false,
        isOfflineFallback: false,
      );
    } catch (error) {
      if (topicId != null || !isNetworkError(error)) {
        rethrow;
      }

      final cached = await _cacheStore.readPage(page, allowStale: true);
      if (cached != null) {
        return FeedFetchResult(
          page: cached.page,
          fromCache: true,
          isOfflineFallback: true,
        );
      }
      rethrow;
    }
  }

  Future<void> clearCache() => _cacheStore.clear();
}
