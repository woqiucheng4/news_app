import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../data/local/article_cache_store.dart';
import '../../data/local/feed_cache_store.dart';
import '../../data/repositories/article_detail_repository.dart';
import '../../data/repositories/feed_repository.dart';
import '../../data/services/feed_api_service.dart';

final feedCacheStoreProvider = Provider<FeedCacheStore>((ref) {
  throw UnimplementedError('FeedCacheStore must be overridden at startup');
});

final articleCacheStoreProvider = Provider<ArticleCacheStore>((ref) {
  throw UnimplementedError('ArticleCacheStore must be overridden at startup');
});

final feedApiServiceProvider = Provider<FeedApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return FeedApiService(dio);
});

final feedRepositoryProvider = Provider<FeedRepository>((ref) {
  final apiService = ref.watch(feedApiServiceProvider);
  final cacheStore = ref.watch(feedCacheStoreProvider);
  return FeedRepository(apiService, cacheStore);
});

final articleDetailRepositoryProvider = Provider<ArticleDetailRepository>((ref) {
  final api = ref.watch(feedApiServiceProvider);
  final cache = ref.watch(articleCacheStoreProvider);
  return ArticleDetailRepository(api, cache);
});
