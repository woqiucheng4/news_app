import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../domain/models/article_detail.dart';

const articleCacheTtl = Duration(days: 7);
const maxCachedArticles = 50;

class ArticleCacheStore {
  ArticleCacheStore(this._prefsFuture);

  final Future<SharedPreferences> _prefsFuture;

  static Future<ArticleCacheStore> create() async {
    return ArticleCacheStore(SharedPreferences.getInstance());
  }

  Future<CachedArticleDetail?> read(
    String articleId, {
    bool allowStale = false,
  }) async {
    final prefs = await _prefsFuture;
    final raw = prefs.getString(_articleKey(articleId));
    if (raw == null || raw.isEmpty) {
      return null;
    }

    try {
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      final cachedAt = DateTime.parse(decoded['cached_at'] as String);
      final article = ArticleDetail.fromJson(
        Map<String, dynamic>.from(decoded['article'] as Map),
      );
      final isPreview = decoded['is_preview'] as bool? ?? false;
      final isStale = DateTime.now().difference(cachedAt) > articleCacheTtl;
      if (isStale && !allowStale) {
        return null;
      }
      await _touchArticleIndex(prefs, articleId);
      return CachedArticleDetail(
        article: article,
        cachedAt: cachedAt,
        isStale: isStale,
        isPreview: isPreview,
      );
    } catch (_) {
      await prefs.remove(_articleKey(articleId));
      return null;
    }
  }

  Future<void> writePreviewIfAbsent(ArticleDetail article) async {
    final existing = await read(article.id, allowStale: true);
    if (existing != null) {
      return;
    }
    await _write(article, isPreview: true);
  }

  Future<void> write(ArticleDetail article) async {
    await _write(article, isPreview: false);
  }

  Future<void> _write(ArticleDetail article, {required bool isPreview}) async {
    final prefs = await _prefsFuture;
    final payload = jsonEncode({
      'cached_at': DateTime.now().toUtc().toIso8601String(),
      'is_preview': isPreview,
      'article': article.toJson(),
    });
    await prefs.setString(_articleKey(article.id), payload);
    await _touchArticleIndex(prefs, article.id);

    final index = [...prefs.getStringList(_articleIndexKey) ?? []];
    while (index.length > maxCachedArticles) {
      final removedId = index.removeAt(0);
      await prefs.remove(_articleKey(removedId));
    }
    await prefs.setStringList(_articleIndexKey, List<String>.from(index));
  }

  Future<void> clear() async {
    final prefs = await _prefsFuture;
    final index = prefs.getStringList(_articleIndexKey) ?? [];
    for (final articleId in index) {
      await prefs.remove(_articleKey(articleId));
    }
    await prefs.remove(_articleIndexKey);
  }

  Future<void> _touchArticleIndex(SharedPreferences prefs, String articleId) async {
    final index = [...prefs.getStringList(_articleIndexKey) ?? []]
      ..remove(articleId)
      ..add(articleId);
    await prefs.setStringList(_articleIndexKey, List<String>.from(index));
  }

  String _articleKey(String articleId) => 'article_cache_$articleId';
}

class CachedArticleDetail {
  const CachedArticleDetail({
    required this.article,
    required this.cachedAt,
    required this.isStale,
    this.isPreview = false,
  });

  final ArticleDetail article;
  final DateTime cachedAt;
  final bool isStale;
  final bool isPreview;

  bool get needsRelatedHydration =>
      !isPreview &&
      article.relatedArticles.isEmpty &&
      article.relatedArticlesTotal == 0;
}

const _articleIndexKey = 'article_cache_index';
