import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

/// Wraps store billing APIs for premium subscription purchase.
class IapPurchaseService {
  IapPurchaseService();

  final InAppPurchase _iap = InAppPurchase.instance;

  bool get isSupported =>
      !kIsWeb && (Platform.isIOS || Platform.isAndroid);

  String get platformName => Platform.isIOS ? 'ios' : 'android';

  Future<bool> isStoreAvailable() async {
    if (!isSupported) {
      return false;
    }
    return _iap.isAvailable();
  }

  Future<ProductDetails?> loadProduct(String productId) async {
    if (!await isStoreAvailable()) {
      return null;
    }

    final response = await _iap.queryProductDetails({productId});
    if (response.error != null || response.productDetails.isEmpty) {
      return null;
    }
    return response.productDetails.first;
  }

  Stream<List<PurchaseDetails>> get purchaseStream => _iap.purchaseStream;

  Future<bool> purchaseSubscription(ProductDetails product) async {
    final purchaseParam = PurchaseParam(productDetails: product);
    return _iap.buyNonConsumable(purchaseParam: purchaseParam);
  }

  Future<void> completePurchase(PurchaseDetails purchase) async {
    if (purchase.pendingCompletePurchase) {
      await _iap.completePurchase(purchase);
    }
  }

  String? purchaseToken(PurchaseDetails purchase) {
    final token = purchase.verificationData.serverVerificationData.trim();
    if (token.isEmpty) {
      return null;
    }
    return token;
  }
}
