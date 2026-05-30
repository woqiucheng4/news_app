import 'package:dio/dio.dart';

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required this.dio,
    required this.tokenResolver,
    required this.onRefreshToken,
  });

  final Dio dio;
  final String Function() tokenResolver;
  final Future<bool> Function() onRefreshToken;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = tokenResolver().trim();
    if (token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (!_shouldAttemptRefresh(err)) {
      handler.next(err);
      return;
    }

    final refreshed = await onRefreshToken();
    if (!refreshed) {
      handler.next(err);
      return;
    }

    try {
      final requestOptions = err.requestOptions;
      requestOptions.headers['Authorization'] = 'Bearer ${tokenResolver()}';
      final response = await dio.fetch<dynamic>(requestOptions);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  bool _shouldAttemptRefresh(DioException err) {
    if (err.response?.statusCode != 401) {
      return false;
    }

    final path = err.requestOptions.path;
    if (path.contains('/auth/login') ||
        path.contains('/auth/register') ||
        path.contains('/auth/refresh')) {
      return false;
    }

    return tokenResolver().trim().isNotEmpty ||
        err.requestOptions.headers.containsKey('Authorization');
  }
}
