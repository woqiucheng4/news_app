import 'package:dio/dio.dart';

import '../constants/app_constants.dart';
import '../../features/auth/domain/models/auth_tokens.dart';

class AuthRefreshClient {
  const AuthRefreshClient._();

  static Future<AuthTokens> refreshTokens(String refreshToken) async {
    final dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: AppConstants.connectTimeout,
        receiveTimeout: AppConstants.receiveTimeout,
        contentType: Headers.jsonContentType,
      ),
    );

    final response = await dio.post<Map<String, dynamic>>(
      '/auth/refresh',
      data: {'refresh_token': refreshToken.trim()},
    );

    final tokens = AuthTokens.fromJson(response.data);
    if (tokens.accessToken.trim().isEmpty) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Missing access token in refresh response',
      );
    }

    return AuthTokens(
      accessToken: tokens.accessToken.trim(),
      refreshToken: tokens.refreshToken?.trim() ?? refreshToken.trim(),
    );
  }
}
