import 'package:dio/dio.dart';

class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    // Centralized place for logging, mapping, and retry hooks.
    handler.next(err);
  }
}
