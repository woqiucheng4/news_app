import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/models/article_detail_view_data.dart';
import 'feed_data_providers.dart';

class ArticleDetailScope {
  const ArticleDetailScope(this.articleId);

  final String articleId;
}

final articleDetailScopeProvider = Provider<ArticleDetailScope>((ref) {
  throw UnimplementedError(
    'Override articleDetailScopeProvider in ArticleDetailScreen',
  );
});

final articleDetailNotifierProvider =
    AsyncNotifierProvider<ArticleDetailNotifier, ArticleDetailViewData>(
  ArticleDetailNotifier.new,
);

class ArticleDetailNotifier extends AsyncNotifier<ArticleDetailViewData> {
  String get _articleId => ref.watch(articleDetailScopeProvider).articleId;

  @override
  Future<ArticleDetailViewData> build() async {
    final articleId = _articleId;
    final repository = ref.read(articleDetailRepositoryProvider);
    final cached = await repository.readCachedArticleDetail(articleId);

    if (cached != null) {
      _refreshFromNetwork(articleId);
      return ArticleDetailViewData(
        article: cached.article,
        showPreview: cached.isPreview,
        showCached: !cached.isPreview && cached.isStale,
      );
    }

    final result = await repository.getArticle(articleId);
    return result.viewData;
  }

  Future<void> refreshFromNetwork() async {
    state = const AsyncLoading<ArticleDetailViewData>().copyWithPrevious(state);
    state = await AsyncValue.guard(() async {
      final repository = ref.read(articleDetailRepositoryProvider);
      final result = await repository.fetchFromNetwork(_articleId);
      return result.viewData;
    });
  }

  Future<void> _refreshFromNetwork(String articleId) async {
    try {
      final repository = ref.read(articleDetailRepositoryProvider);
      final result = await repository.fetchFromNetwork(articleId);
      if (!ref.mounted) {
        return;
      }
      state = AsyncData(result.viewData);
    } catch (_) {
      // Keep showing the feed preview when background refresh fails.
    }
  }
}
