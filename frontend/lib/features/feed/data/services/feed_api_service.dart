import 'package:dio/dio.dart';

import '../../domain/models/article_detail.dart';
import '../../domain/models/feed_page.dart';
import '../../domain/models/related_articles_page.dart';

const feedPageSize = 20;

class FeedApiService {
  FeedApiService(this._dio);

  final Dio _dio;

  Future<FeedPage> fetchFeed({
    int page = 1,
    int pageSize = feedPageSize,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/articles/feed',
      queryParameters: {
        'page': page,
        'page_size': pageSize,
      },
    );
    return FeedPage.fromJson(response.data ?? const {});
  }

  Future<ArticleDetail> fetchArticle(String articleId) async {
    final response = await _dio.get<Map<String, dynamic>>('/articles/$articleId');
    return ArticleDetail.fromJson(response.data ?? const {});
  }

  Future<RelatedArticlesPage> fetchRelatedArticles(
    String articleId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/articles/$articleId/related',
      queryParameters: {
        'page': page,
        'page_size': pageSize,
      },
    );
    return RelatedArticlesPage.fromJson(response.data ?? const {});
  }
}
