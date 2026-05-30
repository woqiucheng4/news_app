import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/auth/auth_token_provider.dart';
import '../../../../core/network/api_client.dart';
import '../../data/users_api_service.dart';
import '../../domain/models/user_profile.dart';

final usersApiServiceProvider = Provider<UsersApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return UsersApiService(dio);
});

final currentUserProvider = FutureProvider<UserProfile?>((ref) async {
  final token = ref.watch(accessTokenValueProvider).trim();
  if (token.isEmpty) {
    return null;
  }

  final api = ref.read(usersApiServiceProvider);
  return api.fetchCurrentUser();
});
