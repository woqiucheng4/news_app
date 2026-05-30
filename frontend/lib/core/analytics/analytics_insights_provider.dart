import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_token_provider.dart';
import '../network/api_client.dart';
import 'analytics_api_service.dart';
import 'analytics_funnel.dart';
import 'analytics_session_provider.dart';

final analyticsApiServiceProvider = Provider<AnalyticsApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return AnalyticsApiService(dio);
});

final analyticsInsightsProvider = FutureProvider<AnalyticsInsights?>((ref) async {
  final token = ref.watch(accessTokenValueProvider).trim();
  if (token.isEmpty) {
    return null;
  }

  final sessionId = await ref.watch(analyticsSessionIdProvider.future);
  final api = ref.read(analyticsApiServiceProvider);
  const days = 7;

  final userFunnel = await api.fetchMyFunnel(days: days, scope: 'user');
  final sessionFunnel = await api.fetchMyFunnel(
    days: days,
    scope: 'session',
    sessionId: sessionId,
  );
  final userRelatedFunnel = await api.fetchMyRelatedFunnel(days: days, scope: 'user');
  final sessionRelatedFunnel = await api.fetchMyRelatedFunnel(
    days: days,
    scope: 'session',
    sessionId: sessionId,
  );

  return AnalyticsInsights(
    userFunnel: userFunnel,
    sessionFunnel: sessionFunnel,
    userRelatedFunnel: userRelatedFunnel,
    sessionRelatedFunnel: sessionRelatedFunnel,
    sessionId: sessionId,
  );
});
