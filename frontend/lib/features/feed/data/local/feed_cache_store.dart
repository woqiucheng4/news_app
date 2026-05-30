import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../domain/models/feed_page.dart';

const feedCacheTtl = Duration(minutes: 30);
const maxCachedFeedPages = 5;

class FeedCacheStore {
  FeedCacheStore(this._prefsFuture);

  final Future<SharedPreferences> _prefsFuture;

  static Future<FeedCacheStore> create() async {
    return FeedCacheStore(SharedPreferences.getInstance());
  }

  Future<CachedFeedPage?> readPage(
    int page, {
    bool allowStale = false,
  }) async {
    final prefs = await _prefsFuture;
    final raw = prefs.getString(_pageKey(page));
    if (raw == null || raw.isEmpty) {
      return null;
    }

    try {
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      final cachedAt = DateTime.parse(decoded['cached_at'] as String);
      final feedPage = FeedPage.fromJson(
        Map<String, dynamic>.from(decoded['page'] as Map),
      );
      final isStale = DateTime.now().difference(cachedAt) > feedCacheTtl;
      if (isStale && !allowStale) {
        return null;
      }
      return CachedFeedPage(
        page: feedPage,
        cachedAt: cachedAt,
        isStale: isStale,
      );
    } catch (_) {
      await prefs.remove(_pageKey(page));
      return null;
    }
  }

  Future<void> writePage(FeedPage page) async {
    final prefs = await _prefsFuture;
    final payload = jsonEncode({
      'cached_at': DateTime.now().toUtc().toIso8601String(),
      'page': page.toJson(),
    });
    await prefs.setString(_pageKey(page.page), payload);

    final pages = {
      ...prefs.getStringList(_pagesIndexKey) ?? [],
      page.page.toString(),
    }.map(int.parse).toList()
      ..sort();

    while (pages.length > maxCachedFeedPages) {
      final removed = pages.removeAt(0);
      await prefs.remove(_pageKey(removed));
    }

    await prefs.setStringList(
      _pagesIndexKey,
      pages.map((value) => value.toString()).toList(growable: false),
    );
  }

  Future<void> clear() async {
    final prefs = await _prefsFuture;
    final pages = prefs.getStringList(_pagesIndexKey) ?? [];
    for (final page in pages) {
      await prefs.remove(_pageKey(int.parse(page)));
    }
    await prefs.remove(_pagesIndexKey);
  }

  String _pageKey(int page) => 'feed_cache_page_$page';
}

class CachedFeedPage {
  const CachedFeedPage({
    required this.page,
    required this.cachedAt,
    required this.isStale,
  });

  final FeedPage page;
  final DateTime cachedAt;
  final bool isStale;
}

const _pagesIndexKey = 'feed_cache_page_index';
