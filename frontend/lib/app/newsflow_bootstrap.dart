import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod/misc.dart';

import '../core/auth/auth_token_provider.dart';
import '../core/auth/auth_token_store.dart';
import '../features/feed/data/local/article_cache_store.dart';
import '../features/feed/data/local/feed_cache_store.dart';
import '../features/feed/presentation/providers/feed_data_providers.dart';

/// Shared startup overrides for [NewsFlowApp] and integration tests.
Future<List<Override>> createNewsFlowCoreOverrides() async {
  final authTokenStore = AuthTokenStore();
  await authTokenStore.migrateFromSharedPreferencesIfNeeded();
  final feedCacheStore = await FeedCacheStore.create();
  final articleCacheStore = await ArticleCacheStore.create();

  return [
    authTokenStoreProvider.overrideWithValue(authTokenStore),
    feedCacheStoreProvider.overrideWithValue(feedCacheStore),
    articleCacheStoreProvider.overrideWithValue(articleCacheStore),
  ];
}
