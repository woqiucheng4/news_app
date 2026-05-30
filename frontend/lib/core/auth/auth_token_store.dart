import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'auth_session.dart';

const _accessTokenStorageKey = 'access_token';
const _refreshTokenStorageKey = 'refresh_token';
const _legacyAccessTokenKey = 'access_token';
const _legacyRefreshTokenKey = 'refresh_token';

class AuthTokenStore {
  AuthTokenStore({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
              iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
            );

  final FlutterSecureStorage _storage;

  Future<AuthSession> readSession() async {
    final access = (await _storage.read(key: _accessTokenStorageKey))?.trim() ?? '';
    final refresh = (await _storage.read(key: _refreshTokenStorageKey))?.trim() ?? '';

    if (access.isEmpty && refresh.isEmpty) {
      return AuthSession.empty;
    }

    return AuthSession(
      accessToken: access,
      refreshToken: refresh.isEmpty ? null : refresh,
    );
  }

  Future<void> writeSession({
    required String access,
    required String refresh,
  }) async {
    if (access.isEmpty) {
      await _storage.delete(key: _accessTokenStorageKey);
    } else {
      await _storage.write(key: _accessTokenStorageKey, value: access);
    }

    if (refresh.isEmpty) {
      await _storage.delete(key: _refreshTokenStorageKey);
    } else {
      await _storage.write(key: _refreshTokenStorageKey, value: refresh);
    }
  }

  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: _accessTokenStorageKey),
      _storage.delete(key: _refreshTokenStorageKey),
    ]);
  }

  Future<void> migrateFromSharedPreferencesIfNeeded() async {
    final existing = await readSession();
    if (existing.isAuthenticated || (existing.refreshToken?.isNotEmpty ?? false)) {
      await _clearLegacySharedPreferences();
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final legacyAccess = prefs.getString(_legacyAccessTokenKey)?.trim() ?? '';
    final legacyRefresh = prefs.getString(_legacyRefreshTokenKey)?.trim() ?? '';
    if (legacyAccess.isEmpty && legacyRefresh.isEmpty) {
      return;
    }

    await writeSession(access: legacyAccess, refresh: legacyRefresh);
    await _clearLegacySharedPreferences();
  }

  Future<void> _clearLegacySharedPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    await Future.wait([
      prefs.remove(_legacyAccessTokenKey),
      prefs.remove(_legacyRefreshTokenKey),
    ]);
  }
}

final authTokenStoreProvider = Provider<AuthTokenStore>((ref) {
  throw UnimplementedError('AuthTokenStore must be overridden at startup');
});
