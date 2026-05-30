import 'package:dio/dio.dart';

bool isUnauthorizedError(Object error) {
  return error is DioException && error.response?.statusCode == 401;
}
