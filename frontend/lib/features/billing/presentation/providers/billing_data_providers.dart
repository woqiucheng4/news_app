import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../data/services/billing_api_service.dart';
import '../../data/services/deep_analysis_api_service.dart';
import '../../data/services/entitlements_api_service.dart';

final entitlementsApiServiceProvider = Provider<EntitlementsApiService>((ref) {
  return EntitlementsApiService(ref.watch(dioProvider));
});

final billingApiServiceProvider = Provider<BillingApiService>((ref) {
  return BillingApiService(ref.watch(dioProvider));
});

final deepAnalysisApiServiceProvider = Provider<DeepAnalysisApiService>((ref) {
  return DeepAnalysisApiService(ref.watch(dioProvider));
});
