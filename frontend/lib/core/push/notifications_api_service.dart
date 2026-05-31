import 'package:dio/dio.dart';

class NotificationsApiService {
  NotificationsApiService(this._dio);

  final Dio _dio;

  Future<void> registerPushToken({
    required String token,
    required String platform,
    String? deviceId,
  }) async {
    await _dio.post<Map<String, dynamic>>(
      '/notifications/register',
      data: {
        'token': token,
        'platform': platform,
        if (deviceId != null) 'device_id': deviceId,
      },
    );
  }
}
