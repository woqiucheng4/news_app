import 'feed_item.dart';
import 'feed_source.dart';

class ArticleDetail {
  const ArticleDetail({
    required this.id,
    required this.title,
    required this.url,
    this.excerpt,
    this.summary,
    this.author,
    this.source,
    this.category,
    this.publishedAt,
    this.relatedArticles = const [],
    this.relatedArticlesTotal = 0,
  });

  final String id;
  final String title;
  final String url;
  final String? excerpt;
  final String? summary;
  final String? author;
  final FeedSource? source;
  final String? category;
  final String? publishedAt;
  final List<FeedItem> relatedArticles;
  final int relatedArticlesTotal;

  String get sourceName => source?.name?.trim() ?? '';

  String get displaySummary => (summary?.trim().isNotEmpty == true)
      ? summary!.trim()
      : (excerpt?.trim() ?? '');

  factory ArticleDetail.fromJson(Map<String, dynamic> json) {
    final sourceJson = json['source'];
    final relatedJson = json['related_articles'];
    return ArticleDetail(
      id: (json['id'] ?? '') as String,
      title: (json['title'] ?? '') as String,
      url: (json['url'] ?? '') as String,
      excerpt: json['excerpt'] as String?,
      summary: json['summary'] as String?,
      author: json['author'] as String?,
      source: sourceJson is Map<String, dynamic>
          ? FeedSource.fromJson(sourceJson)
          : null,
      category: json['category'] as String?,
      publishedAt: json['published_at'] as String?,
      relatedArticles: relatedJson is List
          ? relatedJson
              .whereType<Map>()
              .map((item) => FeedItem.fromJson(Map<String, dynamic>.from(item)))
              .toList()
          : const [],
      relatedArticlesTotal: _parseRelatedArticlesTotal(
        json,
        relatedJson is List ? relatedJson.length : 0,
      ),
    );
  }

  static int _parseRelatedArticlesTotal(
    Map<String, dynamic> json,
    int relatedCount,
  ) {
    final total = json['related_articles_total'];
    if (total is num) {
      return total.toInt();
    }
    return relatedCount;
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'url': url,
      if (excerpt != null) 'excerpt': excerpt,
      if (summary != null) 'summary': summary,
      if (author != null) 'author': author,
      if (source != null) 'source': source!.toJson(),
      if (category != null) 'category': category,
      if (publishedAt != null) 'published_at': publishedAt,
      if (relatedArticles.isNotEmpty)
        'related_articles': relatedArticles.map((item) => item.toJson()).toList(),
      if (relatedArticlesTotal > 0) 'related_articles_total': relatedArticlesTotal,
    };
  }
}
