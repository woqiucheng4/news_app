import 'package:dio/dio.dart';

import '../domain/models/user_profile.dart';

class UsersApiService {
  UsersApiService(this._dio);

  final Dio _dio;

  Future<UserProfile> fetchCurrentUser() async {
    final response = await _dio.get<Map<String, dynamic>>('/users/me');
    return UserProfile.fromJson(response.data ?? const {});
  }
}
