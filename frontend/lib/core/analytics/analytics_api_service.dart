import 'package:dio/dio.dart';

import 'analytics_funnel.dart';

class AnalyticsApiService {
  AnalyticsApiService(this._dio);

  final Dio _dio;

  Future<AnalyticsFunnel> fetchMyFunnel({
    required int days,
    required String scope,
    String? sessionId,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/analytics/me/funnel',
      queryParameters: {
        'days': days,
        'scope': scope,
        if (sessionId != null && sessionId.isNotEmpty) 'session_id': sessionId,
      },
    );

    return AnalyticsFunnel.fromJson(response.data ?? const {});
  }

  Future<RelatedAnalyticsFunnel> fetchMyRelatedFunnel({
    required int days,
    required String scope,
    String? sessionId,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/analytics/me/related-funnel',
      queryParameters: {
        'days': days,
        'scope': scope,
        if (sessionId != null && sessionId.isNotEmpty) 'session_id': sessionId,
      },
    );

    return RelatedAnalyticsFunnel.fromJson(response.data ?? const {});
  }
}
