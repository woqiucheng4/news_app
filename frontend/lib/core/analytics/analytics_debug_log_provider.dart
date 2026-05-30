import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnalyticsDebugLogEntry {
  const AnalyticsDebugLogEntry({
    required this.eventName,
    required this.params,
    required this.recordedAt,
  });

  final String eventName;
  final Map<String, Object> params;
  final DateTime recordedAt;
}

final analyticsDebugLogProvider =
    NotifierProvider<AnalyticsDebugLogNotifier, List<AnalyticsDebugLogEntry>>(
  AnalyticsDebugLogNotifier.new,
);

class AnalyticsDebugLogNotifier extends Notifier<List<AnalyticsDebugLogEntry>> {
  static const _maxEntries = 20;

  @override
  List<AnalyticsDebugLogEntry> build() => const [];

  void append({
    required String eventName,
    required Map<String, Object> params,
  }) {
    final next = [
      AnalyticsDebugLogEntry(
        eventName: eventName,
        params: params,
        recordedAt: DateTime.now(),
      ),
      ...state,
    ].take(_maxEntries).toList(growable: false);
    state = next;
  }

  void clear() {
    state = const [];
  }
}
