import 'package:dio/dio.dart';

import '../../../feed/domain/models/feed_item.dart';
import '../services/article_search_api_service.dart';

abstract interface class ArticleSearchRepository {
  Future<List<FeedItem>> search({
    required String query,
    int limit,
    CancelToken? cancelToken,
  });
}

class ArticleSearchRepositoryImpl implements ArticleSearchRepository {
  ArticleSearchRepositoryImpl(this._api);

  final ArticleSearchApiService _api;

  @override
  Future<List<FeedItem>> search({
    required String query,
    int limit = 20,
    CancelToken? cancelToken,
  }) {
    return _api.searchArticles(
      query: query,
      limit: limit,
      cancelToken: cancelToken,
    );
  }
}
