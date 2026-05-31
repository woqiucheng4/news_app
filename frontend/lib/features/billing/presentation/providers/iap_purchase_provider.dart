import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../../../settings/presentation/providers/current_user_provider.dart';
import '../../data/services/iap_purchase_service.dart';
import '../providers/billing_data_providers.dart';
import '../providers/entitlements_provider.dart';

final iapPurchaseServiceProvider = Provider<IapPurchaseService>((ref) {
  return IapPurchaseService();
});

final storeProductProvider =
    FutureProvider.family<ProductDetails?, String>((ref, productId) async {
  if (productId.trim().isEmpty) {
    return null;
  }
  final iap = ref.read(iapPurchaseServiceProvider);
  return iap.loadProduct(productId);
});

class IapPurchaseController extends Notifier<AsyncValue<void>> {
  StreamSubscription<List<PurchaseDetails>>? _subscription;

  @override
  AsyncValue<void> build() {
    ref.onDispose(_dispose);
    _listenToPurchases();
    return const AsyncData(null);
  }

  void _listenToPurchases() {
    final iap = ref.read(iapPurchaseServiceProvider);
    if (!iap.isSupported) {
      return;
    }

    _subscription?.cancel();
    _subscription = iap.purchaseStream.listen(
      (purchases) async {
        for (final purchase in purchases) {
          await _handlePurchase(purchase);
        }
      },
      onError: (error, _) {
        state = AsyncError(error, StackTrace.current);
      },
    );
  }

  Future<void> _handlePurchase(PurchaseDetails purchase) async {
    final iap = ref.read(iapPurchaseServiceProvider);

    switch (purchase.status) {
      case PurchaseStatus.pending:
        state = const AsyncLoading();
      case PurchaseStatus.error:
        state = AsyncError(
          purchase.error ?? StateError('Purchase failed'),
          StackTrace.current,
        );
      case PurchaseStatus.canceled:
        state = const AsyncData(null);
      case PurchaseStatus.purchased:
      case PurchaseStatus.restored:
        final token = iap.purchaseToken(purchase);
        if (token == null) {
          state = AsyncError(
            StateError('Missing purchase token'),
            StackTrace.current,
          );
          break;
        }

        try {
          final billing = ref.read(billingApiServiceProvider);
          await billing.verifyPurchase(
            platform: iap.platformName,
            productId: purchase.productID,
            purchaseToken: token,
          );
          ref.invalidate(entitlementsProvider);
          ref.invalidate(currentUserProvider);
          state = const AsyncData(null);
        } catch (error, stackTrace) {
          state = AsyncError(error, stackTrace);
        } finally {
          await iap.completePurchase(purchase);
        }
    }
  }

  Future<void> purchase(String productId) async {
    final iap = ref.read(iapPurchaseServiceProvider);
    if (!iap.isSupported) {
      state = AsyncError(
        StateError('In-app purchase is not supported on this platform'),
        StackTrace.current,
      );
      return;
    }

    state = const AsyncLoading();
    try {
      final product = await iap.loadProduct(productId);
      if (product == null) {
        throw StateError('Product not found in store');
      }
      final started = await iap.purchaseSubscription(product);
      if (!started) {
        throw StateError('Unable to start purchase flow');
      }
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
    }
  }

  Future<void> _dispose() async {
    await _subscription?.cancel();
  }
}

final iapPurchaseControllerProvider =
    NotifierProvider<IapPurchaseController, AsyncValue<void>>(
  IapPurchaseController.new,
);
