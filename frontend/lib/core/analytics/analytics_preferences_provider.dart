import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _analyticsEnabledStorageKey = 'analytics_enabled';

final analyticsEnabledProvider =
    AsyncNotifierProvider<AnalyticsEnabledNotifier, bool>(
  AnalyticsEnabledNotifier.new,
);

class AnalyticsEnabledNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_analyticsEnabledStorageKey) ?? true;
  }

  Future<void> setEnabled(bool enabled) async {
    state = AsyncData(enabled);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_analyticsEnabledStorageKey, enabled);
  }
}
