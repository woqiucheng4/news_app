import 'package:dio/dio.dart';
import 'package:newsflow_frontend/features/feed/data/local/article_cache_store.dart';
import 'package:newsflow_frontend/features/feed/data/repositories/article_detail_repository.dart';
import 'package:newsflow_frontend/features/feed/data/services/feed_api_service.dart';
import 'package:newsflow_frontend/features/feed/domain/models/related_articles_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

class StubArticleDetailRepository extends ArticleDetailRepository {
  StubArticleDetailRepository(this._fetchRelated)
      : super(
          FeedApiService(Dio()),
          ArticleCacheStore(SharedPreferences.getInstance()),
        );

  final Future<RelatedArticlesPage> Function(String articleId) _fetchRelated;

  @override
  Future<RelatedArticlesPage> fetchRelatedArticles(
    String articleId, {
    int page = 1,
    int pageSize = 20,
  }) {
    return _fetchRelated(articleId);
  }
}
