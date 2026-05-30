import 'package:dio/dio.dart';

import '../../../feed/domain/models/feed_item.dart';

class ArticleSearchApiService {
  ArticleSearchApiService(this._dio);

  final Dio _dio;

  Future<List<FeedItem>> searchArticles({
    required String query,
    int limit = 20,
    CancelToken? cancelToken,
  }) async {
    final normalized = query.trim();
    if (normalized.isEmpty) {
      return const [];
    }

    final response = await _dio.get<List<dynamic>>(
      '/articles/search',
      queryParameters: {
        'q': normalized,
        'limit': limit,
      },
      cancelToken: cancelToken,
    );

    final raw = response.data ?? const [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(FeedItem.fromJson)
        .toList(growable: false);
  }
}
