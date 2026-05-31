import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/auth/auth_token_provider.dart';
import '../../domain/models/entitlements.dart';
import 'billing_data_providers.dart';

final entitlementsProvider = FutureProvider<Entitlements?>((ref) async {
  final token = ref.watch(accessTokenValueProvider).trim();
  if (token.isEmpty) {
    return null;
  }

  final api = ref.read(entitlementsApiServiceProvider);
  return api.fetchEntitlements();
});

final isPremiumProvider = Provider<bool>((ref) {
  return ref.watch(entitlementsProvider).value?.isPremium ?? false;
});
