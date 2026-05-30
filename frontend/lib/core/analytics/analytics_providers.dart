import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_token_provider.dart';
import '../auth/jwt_subject_extractor.dart';
import '../constants/app_constants.dart';
import 'analytics_backend.dart';
import 'analytics_debug_log_provider.dart';
import 'analytics_event_sanitizer.dart';
import 'analytics_preferences_provider.dart';
import 'analytics_session_provider.dart';
import 'discovery_analytics.dart';
import 'firebase_analytics_backend.dart';

String _resolveAnalyticsEndpoint() {
  if (AppConstants.analyticsEndpoint.isNotEmpty) {
    return AppConstants.analyticsEndpoint;
  }
  if (AppConstants.analyticsTransport.toLowerCase() == 'http') {
    return '${AppConstants.apiBaseUrl}/analytics/events';
  }
  return '';
}

final analyticsSanitizerProvider = Provider<AnalyticsEventSanitizer>((ref) {
  return AnalyticsEventSanitizer(
    redactSearchTerms: AppConstants.analyticsRedactSearch,
  );
});

final analyticsBackendProvider = Provider<AnalyticsBackend>((ref) {
  ref.watch(analyticsSessionIdProvider);

  return switch (AppConstants.analyticsTransport.toLowerCase()) {
    'http' => HttpAnalyticsBackend(
        endpoint: _resolveAnalyticsEndpoint(),
        accessTokenResolver: () => ref.read(accessTokenValueProvider),
        userIdResolver: () =>
            JwtSubjectExtractor.extractSubject(
              ref.read(accessTokenValueProvider),
            ) ??
            '',
        sessionIdResolver: () =>
            ref.read(analyticsSessionIdProvider.notifier).cachedOrEmpty,
      ),
    'firebase' => FirebaseAnalyticsBackend(),
    _ => const DebugAnalyticsBackend(),
  };
});

final discoveryAnalyticsProvider = Provider<DiscoveryAnalytics>((ref) {
  final sanitizer = ref.watch(analyticsSanitizerProvider);
  final delegate = switch (AppConstants.analyticsAdapter.toLowerCase()) {
    'production' => ProductionDiscoveryAnalyticsAdapter(
        backend: ref.watch(analyticsBackendProvider),
        sanitizer: sanitizer,
      ),
    _ => DebugDiscoveryAnalyticsAdapter(
        sanitizer: sanitizer,
      ),
  };

  final adapter = LoggingDiscoveryAnalyticsAdapter(
    sanitizer: sanitizer,
    delegate: delegate,
    isEnabled: () => ref.read(analyticsEnabledProvider).value ?? true,
    onLogged: (eventName, params) {
      ref.read(analyticsDebugLogProvider.notifier).append(
            eventName: eventName,
            params: params,
          );
    },
  );

  return DiscoveryAnalytics(adapter: adapter);
});

/// Preferred provider name for app-wide analytics.
final appAnalyticsProvider = discoveryAnalyticsProvider;
