import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/models/article_detail_view_data.dart';
import 'feed_data_providers.dart';

final articleDetailProvider = AutoDisposeAsyncNotifierProviderFamily<
    ArticleDetailNotifier, ArticleDetailViewData, String>(
  ArticleDetailNotifier.new,
);

class ArticleDetailNotifier
    extends AutoDisposeFamilyAsyncNotifier<ArticleDetailViewData, String> {
  late String _articleId;

  @override
  Future<ArticleDetailViewData> build(String articleId) async {
    _articleId = articleId;
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
