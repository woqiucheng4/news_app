import 'package:dio/dio.dart';

import '../domain/models/auth_tokens.dart';

class AuthApiService {
  AuthApiService(this._dio);

  final Dio _dio;

  Future<AuthTokens> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {
        'email': email.trim(),
        'password': password,
      },
    );
    return _readAuthTokens(response.data);
  }

  Future<AuthTokens> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/register',
      data: {
        'email': email.trim(),
        'password': password,
        if (displayName != null && displayName.trim().isNotEmpty)
          'display_name': displayName.trim(),
      },
    );
    return _readAuthTokens(response.data);
  }

  Future<AuthTokens> oauthLogin({
    required String provider,
    required String providerId,
    required String email,
    String? displayName,
    String? avatarUrl,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/oauth/$provider',
      data: {
        'provider_id': providerId.trim(),
        'email': email.trim(),
        if (displayName != null && displayName.trim().isNotEmpty)
          'display_name': displayName.trim(),
        if (avatarUrl != null && avatarUrl.trim().isNotEmpty)
          'avatar_url': avatarUrl.trim(),
      },
    );
    return _readAuthTokens(response.data);
  }

  AuthTokens _readAuthTokens(Map<String, dynamic>? data) {
    final tokens = AuthTokens.fromJson(data);
    if (tokens.accessToken.trim().isEmpty) {
      throw DioException(
        requestOptions: RequestOptions(path: '/auth/login'),
        message: 'Missing access token in auth response',
      );
    }
    return AuthTokens(
      accessToken: tokens.accessToken.trim(),
      refreshToken: tokens.refreshToken?.trim(),
    );
  }
}
