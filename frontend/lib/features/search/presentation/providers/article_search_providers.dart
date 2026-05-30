import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../data/repositories/article_search_repository.dart';
import '../../data/services/article_search_api_service.dart';

final articleSearchApiServiceProvider = Provider<ArticleSearchApiService>((ref) {
  return ArticleSearchApiService(ref.watch(dioProvider));
});

final articleSearchRepositoryProvider = Provider<ArticleSearchRepository>((ref) {
  return ArticleSearchRepositoryImpl(ref.watch(articleSearchApiServiceProvider));
});
