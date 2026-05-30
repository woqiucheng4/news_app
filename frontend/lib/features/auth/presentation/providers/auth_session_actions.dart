import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_insights_provider.dart';
import '../../../../core/auth/auth_token_provider.dart';
import '../../../feed/presentation/providers/feed_notifier.dart';
import '../../../settings/presentation/providers/current_user_provider.dart';
import '../../domain/models/auth_tokens.dart';

final authSessionActionsProvider = Provider<AuthSessionActions>((ref) {
  return AuthSessionActions(ref);
});

class AuthSessionActions {
  AuthSessionActions(this._ref);

  final Ref _ref;

  Future<void> completeLogin(AuthTokens tokens) async {
    await _ref.read(accessTokenProvider.notifier).setSession(
          accessToken: tokens.accessToken,
          refreshToken: tokens.refreshToken ?? '',
        );
    _ref.invalidate(currentUserProvider);
    _ref.invalidate(analyticsInsightsProvider);
    _ref.invalidate(feedNotifierProvider);
  }
}
