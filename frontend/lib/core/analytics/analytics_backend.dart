import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Transport layer for sanitized analytics events.
abstract class AnalyticsBackend {
  const AnalyticsBackend();

  Future<void> send({
    required String eventName,
    required Map<String, Object> params,
  });
}

class DebugAnalyticsBackend extends AnalyticsBackend {
  const DebugAnalyticsBackend();

  @override
  Future<void> send({
    required String eventName,
    required Map<String, Object> params,
  }) async {
    debugPrint('[analytics:debug][$eventName] $params');
  }
}

/// Self-hosted analytics endpoint (JSON POST).
class HttpAnalyticsBackend extends AnalyticsBackend {
  HttpAnalyticsBackend({
    required this.endpoint,
    Dio? dio,
    String Function()? accessTokenResolver,
    String Function()? userIdResolver,
    String Function()? sessionIdResolver,
  })  : _dio = dio ?? Dio(),
        _accessTokenResolver = accessTokenResolver,
        _userIdResolver = userIdResolver,
        _sessionIdResolver = sessionIdResolver;

  final String endpoint;
  final Dio _dio;
  final String Function()? _accessTokenResolver;
  final String Function()? _userIdResolver;
  final String Function()? _sessionIdResolver;

  @override
  Future<void> send({
    required String eventName,
    required Map<String, Object> params,
  }) async {
    if (endpoint.isEmpty) {
      debugPrint('[analytics:http] skipped (empty endpoint): $eventName $params');
      return;
    }

    final headers = <String, String>{};
    final token = _accessTokenResolver?.call().trim() ?? '';
    if (token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    final userId = _userIdResolver?.call().trim() ?? '';
    if (userId.isNotEmpty) {
      headers['X-User-Id'] = userId;
    }

    final sessionId = _sessionIdResolver?.call().trim() ?? '';
    if (sessionId.isNotEmpty) {
      headers['X-Session-Id'] = sessionId;
    }

    try {
      await _dio.post<void>(
        endpoint,
        data: {
          'event': eventName,
          'params': params,
          'ts': DateTime.now().toUtc().toIso8601String(),
        },
        options: Options(headers: headers),
      );
    } catch (error, stackTrace) {
      debugPrint('[analytics:http] failed: $eventName error=$error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }
}
