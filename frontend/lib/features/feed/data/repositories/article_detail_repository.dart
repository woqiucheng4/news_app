import '../../domain/models/article_detail.dart';
import '../../domain/models/article_detail_view_data.dart';
import '../../domain/models/feed_item.dart';
import '../../domain/models/related_articles_page.dart';
import '../local/article_cache_store.dart';
import '../services/feed_api_service.dart';
import '../../../../core/network/network_error_utils.dart';

class ArticleDetailRepository {
  ArticleDetailRepository(this._apiService, this._cacheStore);

  final FeedApiService _apiService;
  final ArticleCacheStore _cacheStore;

  Future<void> cachePreviewFromFeedItem(FeedItem item) async {
    if (item.id.trim().isEmpty) {
      return;
    }
    await _cacheStore.writePreviewIfAbsent(item.toArticleDetailPreview());
  }

  Future<void> cachePreviewFromFeedItems(Iterable<FeedItem> items) async {
    await Future.wait(
      items.map(cachePreviewFromFeedItem),
      eagerError: false,
    );
  }

  Future<CachedArticleDetail?> readCachedArticleDetail(String articleId) async {
    return _cacheStore.read(articleId, allowStale: true);
  }

  Future<ArticleDetailFetchResult> fetchFromNetwork(String articleId) async {
    final article = await _apiService.fetchArticle(articleId);
    await _cacheStore.write(article);
    return ArticleDetailFetchResult(
      viewData: ArticleDetailViewData(article: article),
    );
  }

  Future<ArticleDetailFetchResult> getArticle(
    String articleId, {
    bool forceNetwork = false,
  }) async {
    if (!forceNetwork) {
      final cached = await _cacheStore.read(articleId);
      if (cached != null) {
        return ArticleDetailFetchResult(
          viewData: ArticleDetailViewData(
            article: cached.article,
            showPreview: cached.isPreview,
            showCached: !cached.isPreview && cached.isStale,
          ),
        );
      }
    }

    try {
      return await fetchFromNetwork(articleId);
    } catch (error) {
      if (!isNetworkError(error)) {
        rethrow;
      }

      final cached = await _cacheStore.read(articleId, allowStale: true);
      if (cached != null) {
        return ArticleDetailFetchResult(
          viewData: ArticleDetailViewData(
            article: cached.article,
            showOffline: true,
          ),
        );
      }
      rethrow;
    }
  }

  Future<RelatedArticlesPage> fetchRelatedArticles(
    String articleId, {
    int page = 1,
    int pageSize = 20,
  }) {
    return _apiService.fetchRelatedArticles(
      articleId,
      page: page,
      pageSize: pageSize,
    );
  }

  Future<void> clearCache() => _cacheStore.clear();
}
