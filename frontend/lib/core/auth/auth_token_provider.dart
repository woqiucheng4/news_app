import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_refresh_client.dart';
import 'auth_session.dart';
import 'auth_token_store.dart';

const _envAccessToken =
    String.fromEnvironment('NEWSFLOW_ACCESS_TOKEN', defaultValue: '');

final accessTokenProvider =
    AsyncNotifierProvider<AuthSessionNotifier, AuthSession>(
  AuthSessionNotifier.new,
);

/// Sync token read for interceptors and analytics resolvers.
final accessTokenValueProvider = Provider<String>((ref) {
  final session = ref.watch(accessTokenProvider);
  final access = session.value?.accessToken.trim() ?? '';
  if (access.isNotEmpty) {
    return access;
  }
  return _envAccessToken;
});

final accessTokenLockedByEnvProvider = Provider<bool>((ref) {
  ref.watch(accessTokenProvider);
  return _envAccessToken.isNotEmpty;
});

final authRefreshCoordinatorProvider = Provider<AuthRefreshCoordinator>((ref) {
  return AuthRefreshCoordinator(ref);
});

class AuthRefreshCoordinator {
  AuthRefreshCoordinator(this._ref);

  final Ref _ref;
  Future<bool>? _inFlight;

  Future<bool> refreshAccessToken() {
    return _inFlight ??= _refresh().whenComplete(() {
      _inFlight = null;
    });
  }

  Future<bool> _refresh() {
    return _ref.read(accessTokenProvider.notifier).refreshAccessToken();
  }
}

class AuthSessionNotifier extends AsyncNotifier<AuthSession> {
  AuthTokenStore get _store => ref.read(authTokenStoreProvider);

  @override
  Future<AuthSession> build() async {
    if (_envAccessToken.isNotEmpty) {
      return AuthSession(accessToken: _envAccessToken);
    }

    final session = await _store.readSession();
    if (session.accessToken.isNotEmpty) {
      return session;
    }

    final refresh = session.refreshToken?.trim() ?? '';
    if (refresh.isEmpty) {
      return AuthSession.empty;
    }

    return _refreshAndPersist(refresh);
  }

  Future<void> setSession({
    required String accessToken,
    required String refreshToken,
  }) async {
    final access = accessToken.trim();
    final refresh = refreshToken.trim();
    if (_envAccessToken.isNotEmpty) {
      state = AsyncData(AuthSession(accessToken: _envAccessToken));
      return;
    }

    final session = AuthSession(
      accessToken: access,
      refreshToken: refresh.isEmpty ? null : refresh,
    );
    state = AsyncData(session);
    await _store.writeSession(access: access, refresh: refresh);
  }

  Future<void> setToken(String token) {
    return setSession(
      accessToken: token,
      refreshToken: state.value?.refreshToken ?? '',
    );
  }

  Future<void> logout() async {
    if (_envAccessToken.isNotEmpty) {
      state = AsyncData(AuthSession(accessToken: _envAccessToken));
      return;
    }

    state = const AsyncData(AuthSession.empty);
    await _store.clear();
  }

  Future<bool> refreshAccessToken() async {
    if (_envAccessToken.isNotEmpty) {
      return true;
    }

    final refresh = state.value?.refreshToken?.trim() ?? '';
    if (refresh.isEmpty) {
      final stored = await _store.readSession();
      final storedRefresh = stored.refreshToken?.trim() ?? '';
      if (storedRefresh.isEmpty) {
        await logout();
        return false;
      }
      return _tryRefresh(storedRefresh);
    }

    return _tryRefresh(refresh);
  }

  Future<bool> _tryRefresh(String refreshToken) async {
    try {
      await _refreshAndPersist(refreshToken);
      return true;
    } catch (_) {
      await logout();
      return false;
    }
  }

  Future<AuthSession> _refreshAndPersist(String refreshToken) async {
    final tokens = await AuthRefreshClient.refreshTokens(refreshToken);
    final rotatedRefresh = tokens.refreshToken?.trim() ?? refreshToken.trim();
    final session = AuthSession(
      accessToken: tokens.accessToken,
      refreshToken: rotatedRefresh,
    );
    state = AsyncData(session);
    await _store.writeSession(
      access: tokens.accessToken,
      refresh: rotatedRefresh,
    );
    return session;
  }

  String get cachedAccessToken {
    if (_envAccessToken.isNotEmpty) {
      return _envAccessToken;
    }
    return state.value?.accessToken ?? '';
  }
}
