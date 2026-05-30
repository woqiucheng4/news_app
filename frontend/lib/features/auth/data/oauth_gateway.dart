import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../../../core/constants/app_constants.dart';
import '../domain/models/oauth_identity.dart';

class OAuthGateway {
  const OAuthGateway();

  bool get supportsGoogleSignIn {
    if (kIsWeb) {
      return AppConstants.googleWebClientId.isNotEmpty;
    }
    return true;
  }

  bool get supportsAppleSignIn {
    if (kIsWeb) {
      return false;
    }
    return Platform.isIOS || Platform.isMacOS || Platform.isAndroid;
  }

  Future<OAuthIdentity> signInWithGoogle() async {
    if (!supportsGoogleSignIn) {
      throw const OAuthUnavailableException('Google Sign-In is not configured');
    }

    final googleSignIn = GoogleSignIn(
      scopes: const ['email', 'profile'],
      clientId: _googleClientId(),
    );

    final account = await googleSignIn.signIn();
    if (account == null) {
      throw const OAuthCancelledException();
    }

    return OAuthIdentity(
      providerId: account.id,
      email: account.email,
      displayName: account.displayName,
      avatarUrl: account.photoUrl,
    );
  }

  Future<OAuthIdentity> signInWithApple() async {
    if (!supportsAppleSignIn) {
      throw const OAuthUnavailableException('Apple Sign-In is unavailable');
    }

    final credential = await SignInWithApple.getAppleIDCredential(
      scopes: const [
        AppleIDAuthorizationScopes.email,
        AppleIDAuthorizationScopes.fullName,
      ],
    );

    final providerId = credential.userIdentifier?.trim();
    if (providerId == null || providerId.isEmpty) {
      throw const OAuthUnavailableException('Apple Sign-In returned no user id');
    }

    final email = credential.email?.trim();
    final resolvedEmail = (email != null && email.isNotEmpty)
        ? email
        : '$providerId@privaterelay.appleid.com';

    final displayName = [
      credential.givenName,
      credential.familyName,
    ].whereType<String>().map((part) => part.trim()).where((part) => part.isNotEmpty).join(' ');

    return OAuthIdentity(
      providerId: providerId,
      email: resolvedEmail,
      displayName: displayName.isEmpty ? null : displayName,
    );
  }

  String? _googleClientId() {
    if (kIsWeb && AppConstants.googleWebClientId.isNotEmpty) {
      return AppConstants.googleWebClientId;
    }
    if (!kIsWeb && Platform.isIOS && AppConstants.googleIosClientId.isNotEmpty) {
      return AppConstants.googleIosClientId;
    }
    return null;
  }
}
