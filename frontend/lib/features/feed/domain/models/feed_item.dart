import 'feed_source.dart';
import 'article_detail.dart';

class FeedItem {
  const FeedItem({
    required this.id,
    required this.title,
    required this.summary,
    required this.sourceUrl,
    this.source,
    this.category,
    this.publishedAt,
  });

  final String id;
  final String title;
  final String summary;
  final String sourceUrl;
  final FeedSource? source;
  final String? category;
  final String? publishedAt;

  String get sourceName => source?.name?.trim() ?? '';

  ArticleDetail toArticleDetailPreview() {
    final normalizedSummary = summary.trim();
    return ArticleDetail(
      id: id,
      title: title,
      url: sourceUrl,
      summary: normalizedSummary.isEmpty ? null : normalizedSummary,
      excerpt: normalizedSummary.isEmpty ? null : normalizedSummary,
      source: source,
      category: category,
      publishedAt: publishedAt,
    );
  }

  factory FeedItem.fromJson(Map<String, dynamic> json) {
    final sourceJson = json['source'];
    return FeedItem(
      id: (json['id'] ?? '') as String,
      title: (json['title'] ?? '') as String,
      summary: (json['summary'] ?? json['excerpt'] ?? '') as String,
      sourceUrl: (json['url'] ?? json['source_url'] ?? '') as String,
      source: sourceJson is Map<String, dynamic>
          ? FeedSource.fromJson(sourceJson)
          : null,
      category: json['category'] as String?,
      publishedAt: json['published_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'summary': summary,
      'url': sourceUrl,
      if (source != null) 'source': source!.toJson(),
      if (category != null) 'category': category,
      if (publishedAt != null) 'published_at': publishedAt,
    };
  }
}
