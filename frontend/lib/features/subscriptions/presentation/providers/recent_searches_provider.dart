import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _recentSearchesStorageKey = 'discover_recent_searches';
const _maxRecentSearches = 8;

final recentSearchesProvider =
    AsyncNotifierProvider<RecentSearchesNotifier, List<String>>(
  RecentSearchesNotifier.new,
);

class RecentSearchesNotifier extends AsyncNotifier<List<String>> {
  @override
  Future<List<String>> build() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_recentSearchesStorageKey) ?? const [];
  }

  Future<void> addSearch(String query) async {
    final normalized = query.trim();
    if (normalized.isEmpty) return;

    final current = state.valueOrNull ?? const <String>[];
    final deduplicated = [
      normalized,
      ...current.where((item) => item.toLowerCase() != normalized.toLowerCase()),
    ];
    final next = deduplicated.take(_maxRecentSearches).toList(growable: false);

    state = AsyncData(next);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_recentSearchesStorageKey, next);
  }

  Future<void> clearAll() async {
    state = const AsyncData([]);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_recentSearchesStorageKey);
  }

  Future<void> removeSearch(String query) async {
    final normalized = query.trim();
    if (normalized.isEmpty) return;

    final current = state.valueOrNull ?? const <String>[];
    final next = current
        .where((item) => item.toLowerCase() != normalized.toLowerCase())
        .toList(growable: false);

    state = AsyncData(next);
    final prefs = await SharedPreferences.getInstance();
    if (next.isEmpty) {
      await prefs.remove(_recentSearchesStorageKey);
    } else {
      await prefs.setStringList(_recentSearchesStorageKey, next);
    }
  }
}
