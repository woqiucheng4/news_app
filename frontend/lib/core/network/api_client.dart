import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_token_provider.dart';
import '../constants/app_constants.dart';
import 'auth_interceptor.dart';
import 'error_interceptor.dart';

final dioProvider = Provider<Dio>((ref) {
  ref.watch(accessTokenValueProvider);
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: AppConstants.connectTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      contentType: Headers.jsonContentType,
    ),
  );

  dio.interceptors.addAll([
    AuthInterceptor(
      dio: dio,
      tokenResolver: () => ref.read(accessTokenValueProvider),
      onRefreshToken: () =>
          ref.read(authRefreshCoordinatorProvider).refreshAccessToken(),
    ),
    ErrorInterceptor(),
  ]);

  return dio;
});
