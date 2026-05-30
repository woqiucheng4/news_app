import 'package:dio/dio.dart';
import 'package:newsflow_frontend/features/feed/data/local/article_cache_store.dart';
import 'package:newsflow_frontend/features/feed/data/repositories/article_detail_repository.dart';
import 'package:newsflow_frontend/features/feed/data/services/feed_api_service.dart';
import 'package:newsflow_frontend/features/feed/domain/models/article_detail.dart';
import 'package:newsflow_frontend/features/feed/domain/models/article_detail_view_data.dart';
import 'package:newsflow_frontend/features/feed/domain/models/feed_item.dart';
import 'package:newsflow_frontend/features/feed/domain/models/related_articles_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

ArticleDetail buildIntegrationArticleDetail({
  required String articleId,
  required List<FeedItem> relatedArticles,
  int? relatedTotal,
}) {
  return ArticleDetail(
    id: articleId,
    title: 'Integration parent article',
    url: 'https://example.com/$articleId',
    summary: 'Summary used by related-articles integration tests.',
    relatedArticles: relatedArticles,
    relatedArticlesTotal: relatedTotal ?? relatedArticles.length,
  );
}

class IntegrationArticleDetailRepository extends ArticleDetailRepository {
  IntegrationArticleDetailRepository(this._article)
      : super(
          FeedApiService(Dio()),
          ArticleCacheStore(SharedPreferences.getInstance()),
        );

  final ArticleDetail _article;

  @override
  Future<ArticleDetailFetchResult> getArticle(
    String articleId, {
    bool forceNetwork = false,
  }) async {
    return ArticleDetailFetchResult(
      viewData: ArticleDetailViewData(article: _article),
    );
  }

  @override
  Future<ArticleDetailFetchResult> fetchFromNetwork(String articleId) async {
    return getArticle(articleId);
  }

  @override
  Future<RelatedArticlesPage> fetchRelatedArticles(
    String articleId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    return RelatedArticlesPage(
      page: page,
      pageSize: pageSize,
      articles: _article.relatedArticles,
      hasMore: false,
      total: _article.relatedArticlesTotal,
    );
  }
}

FeedItem integrationRelatedItem(String id, String title) {
  return FeedItem(
    id: id,
    title: title,
    summary: 'Related summary for $title',
    sourceUrl: 'https://example.com/$id',
  );
}
