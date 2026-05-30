import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'article_detail_provider.dart';
import 'feed_data_providers.dart';

Future<void> clearFeedLocalCaches(Ref ref) async {
  await ref.read(feedRepositoryProvider).clearCache();
  await ref.read(articleDetailRepositoryProvider).clearCache();
}

final clearFeedLocalCachesProvider = Provider<Future<void> Function()>((ref) {
  return () => clearFeedLocalCaches(ref);
});
