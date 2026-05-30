class AuthSession {
  const AuthSession({
    required this.accessToken,
    this.refreshToken,
  });

  final String accessToken;
  final String? refreshToken;

  static const empty = AuthSession(accessToken: '');

  bool get isAuthenticated => accessToken.trim().isNotEmpty;
}
