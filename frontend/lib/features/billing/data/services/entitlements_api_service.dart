import 'package:dio/dio.dart';

import '../../domain/models/entitlements.dart';

class EntitlementsApiService {
  EntitlementsApiService(this._dio);

  final Dio _dio;

  Future<Entitlements> fetchEntitlements() async {
    final response =
        await _dio.get<Map<String, dynamic>>('/users/me/entitlements');
    return Entitlements.fromJson(response.data ?? const {});
  }
}
