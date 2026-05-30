import '../../domain/models/article_detail.dart';

class ArticleDetailViewData {
  const ArticleDetailViewData({
    required this.article,
    this.showPreview = false,
    this.showCached = false,
    this.showOffline = false,
  });

  final ArticleDetail article;
  final bool showPreview;
  final bool showCached;
  final bool showOffline;
}

class ArticleDetailFetchResult {
  const ArticleDetailFetchResult({
    required this.viewData,
  });

  final ArticleDetailViewData viewData;
}
