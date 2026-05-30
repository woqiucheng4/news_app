import 'feed_item.dart';

class RelatedArticlesPage {
  const RelatedArticlesPage({
    required this.page,
    required this.pageSize,
    required this.articles,
    required this.hasMore,
    required this.total,
  });

  final int page;
  final int pageSize;
  final List<FeedItem> articles;
  final bool hasMore;
  final int total;

  factory RelatedArticlesPage.fromJson(Map<String, dynamic> json) {
    final articlesJson = json['articles'];
    return RelatedArticlesPage(
      page: (json['page'] as num?)?.toInt() ?? 1,
      pageSize: (json['page_size'] as num?)?.toInt() ?? 20,
      articles: articlesJson is List
          ? articlesJson
              .whereType<Map>()
              .map((item) => FeedItem.fromJson(Map<String, dynamic>.from(item)))
              .toList()
          : const [],
      hasMore: json['has_more'] as bool? ?? false,
      total: (json['total'] as num?)?.toInt() ?? 0,
    );
  }
}
