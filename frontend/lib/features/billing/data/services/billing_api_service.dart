import 'package:dio/dio.dart';

import '../../domain/models/purchase_verification.dart';

class BillingApiService {
  BillingApiService(this._dio);

  final Dio _dio;

  Future<PurchaseVerification> verifyPurchase({
    required String platform,
    required String productId,
    required String purchaseToken,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/billing/verify-purchase',
      data: {
        'platform': platform,
        'product_id': productId,
        'purchase_token': purchaseToken,
      },
    );
    return PurchaseVerification.fromJson(response.data ?? const {});
  }
}
