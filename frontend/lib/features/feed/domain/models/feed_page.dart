import 'feed_item.dart';

class FeedPage {
  const FeedPage({
    required this.articles,
    required this.page,
    required this.hasMore,
  });

  final List<FeedItem> articles;
  final int page;
  final bool hasMore;

  factory FeedPage.fromJson(Map<String, dynamic> json) {
    final rawList = (json['articles'] as List?) ?? <dynamic>[];

    return FeedPage(
      articles: rawList
          .whereType<Map<String, dynamic>>()
          .map(FeedItem.fromJson)
          .toList(growable: false),
      page: (json['page'] as num?)?.toInt() ?? 1,
      hasMore: (json['has_more'] ?? false) as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'articles': articles.map((item) => item.toJson()).toList(growable: false),
      'page': page,
      'has_more': hasMore,
    };
  }
}

class FeedFetchResult {
  const FeedFetchResult({
    required this.page,
    required this.fromCache,
    required this.isOfflineFallback,
  });

  final FeedPage page;
  final bool fromCache;
  final bool isOfflineFallback;
}
