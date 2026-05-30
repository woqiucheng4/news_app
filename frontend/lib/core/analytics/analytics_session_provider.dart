import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _analyticsSessionStorageKey = 'analytics_session_id';

final analyticsSessionIdProvider =
    AsyncNotifierProvider<AnalyticsSessionIdNotifier, String>(
  AnalyticsSessionIdNotifier.new,
);

class AnalyticsSessionIdNotifier extends AsyncNotifier<String> {
  @override
  Future<String> build() async {
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_analyticsSessionStorageKey);
    if (existing != null && existing.isNotEmpty) {
      return existing;
    }

    final created = _createSessionId();
    await prefs.setString(_analyticsSessionStorageKey, created);
    return created;
  }

  String get cachedOrEmpty => state.valueOrNull ?? '';
}

String _createSessionId() {
  final timestamp = DateTime.now().millisecondsSinceEpoch;
  final randomPart = Random.secure().nextInt(0xFFFFFF);
  return 's-$timestamp-$randomPart';
}
