import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:flutter/foundation.dart';

import 'analytics_backend.dart';

/// Firebase Analytics transport for production builds.
class FirebaseAnalyticsBackend extends AnalyticsBackend {
  FirebaseAnalyticsBackend({
    FirebaseAnalytics? analytics,
  }) : _analytics = analytics ?? FirebaseAnalytics.instance;

  final FirebaseAnalytics _analytics;

  @override
  Future<void> send({
    required String eventName,
    required Map<String, Object> params,
  }) async {
    try {
      await _analytics.logEvent(
        name: _normalizeEventName(eventName),
        parameters: _toFirebaseParams(params),
      );
    } catch (error, stackTrace) {
      debugPrint('[analytics:firebase] failed: $eventName error=$error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }

  String _normalizeEventName(String eventName) {
    final normalized = eventName
        .trim()
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9_]'), '_');
    if (normalized.isEmpty) return 'custom_event';
    return normalized.length <= 40 ? normalized : normalized.substring(0, 40);
  }

  Map<String, Object> _toFirebaseParams(Map<String, Object> params) {
    final mapped = <String, Object>{};
    var index = 0;

    for (final entry in params.entries) {
      if (index >= 25) break;

      final key = _normalizeParamKey(entry.key);
      if (key.isEmpty) continue;

      mapped[key] = _normalizeParamValue(entry.value);
      index += 1;
    }

    return mapped;
  }

  String _normalizeParamKey(String key) {
    final normalized = key
        .trim()
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9_]'), '_');
    if (normalized.isEmpty) return '';
    return normalized.length <= 40 ? normalized : normalized.substring(0, 40);
  }

  Object _normalizeParamValue(Object value) {
    if (value is bool || value is int || value is double) {
      return value;
    }
    final text = value.toString();
    return text.length <= 100 ? text : text.substring(0, 100);
  }
}
