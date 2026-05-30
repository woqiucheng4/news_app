class OAuthIdentity {
  const OAuthIdentity({
    required this.providerId,
    required this.email,
    this.displayName,
    this.avatarUrl,
  });

  final String providerId;
  final String email;
  final String? displayName;
  final String? avatarUrl;
}

class OAuthCancelledException implements Exception {
  const OAuthCancelledException();
}

class OAuthUnavailableException implements Exception {
  const OAuthUnavailableException(this.message);

  final String message;
}
