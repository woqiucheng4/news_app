import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_client.dart';
import '../../data/auth_api_service.dart';
import '../../data/oauth_gateway.dart';

final oauthGatewayProvider = Provider<OAuthGateway>((ref) {
  return const OAuthGateway();
});

final authApiServiceProvider = Provider<AuthApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return AuthApiService(dio);
});
