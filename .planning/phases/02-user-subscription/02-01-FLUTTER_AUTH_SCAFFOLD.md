# 02-01 Flutter Auth Scaffold

> Phase index: [`02-01-PHASE_SUMMARY.md`](./02-01-PHASE_SUMMARY.md) · API SoT: [`02-01-API_CONTRACT.md`](./02-01-API_CONTRACT.md)

## Goal

- 提供 Flutter 端的 Auth 接入完整代码骨架，覆盖：
  - 邮箱注册 / 登录
  - Google / Apple OAuth
  - Token 持久化（替换 02-02 中的 `InMemoryAuthTokenReader`）
  - 401 自动刷新 + 失败兜底跳登录
  - GDPR 数据导出 / 账户注销

## File Layout

```text
lib/
  core/
    auth/
      auth_token_reader.dart           # 接口（02-02 已声明）
      secure_storage_token_reader.dart # ← 02-01 落地：真实持久化实现
    network/
      api_client.dart                  # 02-02 已写
      auth_interceptor.dart            # 02-02 已写，本文新增 401 刷新逻辑
  features/auth/
    data/
      models/
        auth_response_dto.dart
        user_dto.dart
        user_settings_dto.dart
      datasources/
        auth_api.dart
        user_api.dart
      repositories/
        auth_repository.dart
        user_repository.dart
    presentation/
      providers/
        auth_providers.dart
      pages/
        login_page.dart
        register_page.dart
        oauth_redirect_page.dart       # 平台原生回调结束后路由到这里
        settings_page.dart             # 含 GDPR 导出 / 注销
```

## Dependencies (pubspec.yaml)

```yaml
dependencies:
  flutter_secure_storage: ^9.2.2
  google_sign_in: ^6.2.1
  sign_in_with_apple: ^6.1.2
  dio: ^5.7.0
  flutter_riverpod: ^2.5.1
  freezed_annotation: ^2.4.4
  json_annotation: ^4.9.0

dev_dependencies:
  build_runner: ^2.4.12
  freezed: ^2.5.7
  json_serializable: ^6.8.0
  riverpod_generator: ^2.4.0
```

## 1) Token Reader Implementation

```dart
// lib/core/auth/auth_token_reader.dart  (interface, 已在 02-02 声明)
abstract interface class AuthTokenReader {
  Future<String?> readAccessToken();
  Future<String?> readRefreshToken();
  Future<void> saveTokens({required String accessToken, required String refreshToken});
  Future<void> updateAccessToken(String accessToken);
  Future<void> clear();
}
```

```dart
// lib/core/auth/secure_storage_token_reader.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'auth_token_reader.dart';

class SecureStorageTokenReader implements AuthTokenReader {
  static const _kAccess = 'newsflow.access_token';
  static const _kRefresh = 'newsflow.refresh_token';

  final FlutterSecureStorage _storage;
  SecureStorageTokenReader([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
              iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
            );

  @override
  Future<String?> readAccessToken() => _storage.read(key: _kAccess);
  @override
  Future<String?> readRefreshToken() => _storage.read(key: _kRefresh);

  @override
  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    await _storage.write(key: _kAccess, value: accessToken);
    await _storage.write(key: _kRefresh, value: refreshToken);
  }

  @override
  Future<void> updateAccessToken(String accessToken) =>
      _storage.write(key: _kAccess, value: accessToken);

  @override
  Future<void> clear() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
  }
}
```

## 2) Auth Interceptor with 401 Refresh

> ⚠️ 这是对 02-02 `auth_interceptor.dart` 的扩展。02-02 版本只注入 `Authorization` 头；本版本增加 401 自动刷新。

```dart
// lib/core/network/auth_interceptor.dart
import 'package:dio/dio.dart';
import '../auth/auth_token_reader.dart';

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required this.tokenReader,
    required this.refreshDio,
    required this.onLogout,
  });

  final AuthTokenReader tokenReader;
  final Dio refreshDio;          // 不带 AuthInterceptor 的独立 Dio，避免循环
  final Future<void> Function() onLogout;

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await tokenReader.readAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) return handler.next(err);

    final refresh = await tokenReader.readRefreshToken();
    if (refresh == null || refresh.isEmpty) {
      await onLogout();
      return handler.next(err);
    }

    try {
      final res = await refreshDio.post('/api/v1/auth/refresh',
          data: {'refresh_token': refresh});
      final newAccess = res.data['access_token'] as String;
      await tokenReader.updateAccessToken(newAccess);

      final retry = err.requestOptions
        ..headers['Authorization'] = 'Bearer $newAccess';
      final cloned = await refreshDio.fetch(retry);
      return handler.resolve(cloned);
    } catch (_) {
      await tokenReader.clear();
      await onLogout();
      return handler.next(err);
    }
  }
}
```

## 3) Freezed DTOs

```dart
// lib/features/auth/data/models/auth_response_dto.dart
import 'package:freezed_annotation/freezed_annotation.dart';
import 'user_dto.dart';

part 'auth_response_dto.freezed.dart';
part 'auth_response_dto.g.dart';

@freezed
sealed class AuthResponseDto with _$AuthResponseDto {
  const factory AuthResponseDto({
    @JsonKey(name: 'access_token') required String accessToken,
    @JsonKey(name: 'refresh_token') String? refreshToken, // refresh 端点不返回
    @JsonKey(name: 'token_type') required String tokenType,
    UserDto? user,
  }) = _AuthResponseDto;

  factory AuthResponseDto.fromJson(Map<String, dynamic> json) =>
      _$AuthResponseDtoFromJson(json);
}
```

```dart
// lib/features/auth/data/models/user_dto.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_dto.freezed.dart';
part 'user_dto.g.dart';

@freezed
sealed class UserDto with _$UserDto {
  const factory UserDto({
    required String id,
    required String email,
    String? username,
    @JsonKey(name: 'display_name') String? displayName,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    @JsonKey(name: 'is_active') @Default(true) bool isActive,
    @JsonKey(name: 'is_verified') @Default(false) bool isVerified,
    @JsonKey(name: 'is_premium') @Default(false) bool isPremium,
    @JsonKey(name: 'created_at') String? createdAt,
  }) = _UserDto;

  factory UserDto.fromJson(Map<String, dynamic> json) => _$UserDtoFromJson(json);
}
```

```dart
// lib/features/auth/data/models/user_settings_dto.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_settings_dto.freezed.dart';
part 'user_settings_dto.g.dart';

@freezed
sealed class UserSettingsDto with _$UserSettingsDto {
  const factory UserSettingsDto({
    @JsonKey(name: 'push_enabled') bool? pushEnabled,
    @JsonKey(name: 'push_daily_briefing') bool? pushDailyBriefing,
    @JsonKey(name: 'push_breaking_news') bool? pushBreakingNews,
    @JsonKey(name: 'push_max_per_day') int? pushMaxPerDay,
    String? language,
    String? theme,
  }) = _UserSettingsDto;

  factory UserSettingsDto.fromJson(Map<String, dynamic> json) =>
      _$UserSettingsDtoFromJson(json);
}
```

## 4) Datasource

```dart
// lib/features/auth/data/datasources/auth_api.dart
import 'package:dio/dio.dart';
import '../models/auth_response_dto.dart';

class AuthApi {
  AuthApi(this._dio);
  final Dio _dio;

  Future<AuthResponseDto> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    final res = await _dio.post('/api/v1/auth/register', data: {
      'email': email,
      'password': password,
      if (displayName != null) 'display_name': displayName,
    });
    return AuthResponseDto.fromJson(res.data as Map<String, dynamic>);
  }

  Future<AuthResponseDto> login({required String email, required String password}) async {
    final res = await _dio.post('/api/v1/auth/login',
        data: {'email': email, 'password': password});
    return AuthResponseDto.fromJson(res.data as Map<String, dynamic>);
  }

  Future<AuthResponseDto> oauthLogin({
    required String provider, // 'google' | 'apple'
    required String providerId,
    required String email,
    String? displayName,
    String? avatarUrl,
  }) async {
    final res = await _dio.post('/api/v1/auth/oauth/$provider', data: {
      'provider_id': providerId,
      'email': email,
      if (displayName != null) 'display_name': displayName,
      if (avatarUrl != null) 'avatar_url': avatarUrl,
    });
    return AuthResponseDto.fromJson(res.data as Map<String, dynamic>);
  }

  Future<String> refresh(String refreshToken) async {
    final res = await _dio.post('/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken});
    return res.data['access_token'] as String;
  }
}
```

```dart
// lib/features/auth/data/datasources/user_api.dart
import 'package:dio/dio.dart';
import '../models/user_dto.dart';
import '../models/user_settings_dto.dart';

class UserApi {
  UserApi(this._dio);
  final Dio _dio;

  Future<UserDto> getMe() async {
    final res = await _dio.get('/api/v1/users/me');
    return UserDto.fromJson(res.data as Map<String, dynamic>);
  }

  Future<bool> updateSettings(UserSettingsDto settings) async {
    final res = await _dio.put('/api/v1/users/me/settings', data: settings.toJson());
    return (res.data as Map)['success'] as bool;
  }

  Future<Map<String, dynamic>> exportData() async {
    final res = await _dio.get('/api/v1/users/me/export');
    return Map<String, dynamic>.from(res.data as Map);
  }

  Future<bool> deleteAccount() async {
    final res = await _dio.delete('/api/v1/users/me');
    return (res.data as Map)['success'] as bool;
  }
}
```

## 5) OAuth Native SDK Integration

```dart
// 简化示例：实际使用时可包成 GoogleAuthProvider / AppleAuthProvider 类
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

Future<({String providerId, String email, String? displayName, String? avatarUrl})>
    googleSignIn() async {
  final googleSignIn = GoogleSignIn(scopes: const ['email', 'profile']);
  final account = await googleSignIn.signIn();
  if (account == null) throw Exception('Cancelled');
  return (
    providerId: account.id,
    email: account.email,
    displayName: account.displayName,
    avatarUrl: account.photoUrl,
  );
}

Future<({String providerId, String email, String? displayName, String? avatarUrl})>
    appleSignIn() async {
  final cred = await SignInWithApple.getAppleIDCredential(scopes: const [
    AppleIDAuthorizationScopes.email,
    AppleIDAuthorizationScopes.fullName,
  ]);
  final email = cred.email ?? '${cred.userIdentifier}@privaterelay.appleid.com';
  final displayName = [cred.givenName, cred.familyName].whereType<String>().join(' ');
  return (
    providerId: cred.userIdentifier!,
    email: email,
    displayName: displayName.isEmpty ? null : displayName,
    avatarUrl: null,
  );
}
```

## 6) Repository + Riverpod Notifier

```dart
// lib/features/auth/data/repositories/auth_repository.dart
import '../../../../core/auth/auth_token_reader.dart';
import '../datasources/auth_api.dart';
import '../models/user_dto.dart';

class AuthRepository {
  AuthRepository({required this.api, required this.tokenReader});
  final AuthApi api;
  final AuthTokenReader tokenReader;

  Future<UserDto> register(String email, String password, {String? displayName}) async {
    final res = await api.register(email: email, password: password, displayName: displayName);
    await tokenReader.saveTokens(
      accessToken: res.accessToken,
      refreshToken: res.refreshToken!,
    );
    return res.user!;
  }

  Future<UserDto> login(String email, String password) async {
    final res = await api.login(email: email, password: password);
    await tokenReader.saveTokens(
      accessToken: res.accessToken,
      refreshToken: res.refreshToken!,
    );
    return res.user!;
  }

  Future<UserDto> loginWithOAuth({
    required String provider,
    required String providerId,
    required String email,
    String? displayName,
    String? avatarUrl,
  }) async {
    final res = await api.oauthLogin(
      provider: provider,
      providerId: providerId,
      email: email,
      displayName: displayName,
      avatarUrl: avatarUrl,
    );
    await tokenReader.saveTokens(
      accessToken: res.accessToken,
      refreshToken: res.refreshToken!,
    );
    return res.user!;
  }

  Future<void> logout() => tokenReader.clear();

  Future<bool> isLoggedIn() async {
    final t = await tokenReader.readAccessToken();
    return t != null && t.isNotEmpty;
  }
}
```

```dart
// lib/features/auth/presentation/providers/auth_providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../data/models/user_dto.dart';
import '../../data/repositories/auth_repository.dart';

part 'auth_providers.g.dart';

@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  Future<UserDto?> build() async {
    final repo = ref.read(authRepositoryProvider);
    if (await repo.isLoggedIn()) {
      return ref.read(userRepositoryProvider).getMe();
    }
    return null;
  }

  Future<void> register(String email, String password, {String? displayName}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final user = await ref.read(authRepositoryProvider).register(
            email,
            password,
            displayName: displayName,
          );
      return user;
    });
  }

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async =>
        await ref.read(authRepositoryProvider).login(email, password));
  }

  Future<void> loginWithGoogle() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final g = await googleSignIn(); // 来自 §5
      return ref.read(authRepositoryProvider).loginWithOAuth(
            provider: 'google',
            providerId: g.providerId,
            email: g.email,
            displayName: g.displayName,
            avatarUrl: g.avatarUrl,
          );
    });
  }

  Future<void> loginWithApple() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final a = await appleSignIn(); // 来自 §5
      return ref.read(authRepositoryProvider).loginWithOAuth(
            provider: 'apple',
            providerId: a.providerId,
            email: a.email,
            displayName: a.displayName,
          );
    });
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AsyncData(null);
  }
}
```

## 7) GDPR 操作（Settings 页）

```dart
// lib/features/auth/presentation/pages/settings_page.dart 关键片段
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';

Future<void> exportMyData(WidgetRef ref) async {
  final data = await ref.read(userRepositoryProvider).exportData();
  final dir = await getApplicationDocumentsDirectory();
  final file = File('${dir.path}/newsflow-export-${DateTime.now().millisecondsSinceEpoch}.json');
  await file.writeAsString(const JsonEncoder.withIndent('  ').convert(data));
  // 后续可用 share_plus 触发系统分享
}

Future<void> deleteMyAccount(WidgetRef ref, BuildContext context) async {
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (_) => AlertDialog(
      title: const Text('删除账户'),
      content: const Text('此操作不可撤销。是否继续？'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
        TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('确认')),
      ],
    ),
  );
  if (confirmed != true) return;

  await ref.read(userRepositoryProvider).deleteAccount();
  await ref.read(authNotifierProvider.notifier).logout();
}
```

## 8) Wiring (在 main.dart 或 providers 文件中)

```dart
final authTokenReaderProvider = Provider<AuthTokenReader>((ref) =>
    SecureStorageTokenReader());

final apiClientProvider = Provider<Dio>((ref) {
  final reader = ref.read(authTokenReaderProvider);
  final refreshDio = Dio(BaseOptions(baseUrl: apiBaseUrl));
  final dio = Dio(BaseOptions(baseUrl: apiBaseUrl, headers: {'Content-Type': 'application/json'}));
  dio.interceptors.add(AuthInterceptor(
    tokenReader: reader,
    refreshDio: refreshDio,
    onLogout: () async => ref.read(authNotifierProvider.notifier).logout(),
  ));
  return dio;
});

final authApiProvider = Provider<AuthApi>((ref) => AuthApi(ref.read(apiClientProvider)));
final userApiProvider = Provider<UserApi>((ref) => UserApi(ref.read(apiClientProvider)));

final authRepositoryProvider = Provider<AuthRepository>((ref) => AuthRepository(
      api: ref.read(authApiProvider),
      tokenReader: ref.read(authTokenReaderProvider),
    ));

final userRepositoryProvider = Provider<UserRepository>((ref) => UserRepository(
      api: ref.read(userApiProvider),
    ));
```

## 9) Migration from 02-02 `InMemoryAuthTokenReader`

| 02-02 | 02-01 替换 |
|---|---|
| `InMemoryAuthTokenReader` | `SecureStorageTokenReader` |
| Dio 单实例 + 静态 token | 双 Dio（业务 + refresh）+ 401 自动刷新 |
| 无登录页 | `LoginPage` + `RegisterPage` + OAuth 按钮 |
| 启动直接拉数据 | 启动先 `authNotifierProvider.build()` 判定登录态 |

升级步骤：
1. 删除 02-02 中临时的 `InMemoryAuthTokenReader`
2. 添加 `flutter_secure_storage` / `google_sign_in` / `sign_in_with_apple` 依赖
3. 复制本文 §1-8 代码骨架
4. 把 `apiClientProvider` 中的 `tokenReader` 替换为 `SecureStorageTokenReader`
5. 在路由中加入登录守卫（未登录跳 `/login`）

## Definition of Done (Flutter Auth 接入)

- [ ] 邮箱注册 / 登录可成功拿到 token 并持久化
- [ ] Google / Apple OAuth 端到端跑通（含 iOS Apple Sign-In 真机配置）
- [ ] App 重启后仍是登录态
- [ ] access_token 过期自动用 refresh_token 续期，业务请求无感知
- [ ] refresh_token 过期 → 清空 token + 跳转登录页
- [ ] Settings 页可触发 GDPR 导出 / 注销
- [ ] 登出后所有需鉴权请求返回 401，引导登录

## Cross-Reference

- Backend 接口：[`02-01-API_CONTRACT.md`](./02-01-API_CONTRACT.md)
- 02-02 网络层骨架（被本文扩展）：[`02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md`](./02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md)
- 整体启动序：[`02-02-FLUTTER_BOOTSTRAP_EXECUTION_PLAN.md`](./02-02-FLUTTER_BOOTSTRAP_EXECUTION_PLAN.md)（Step 3 的临时 token 方案在本文落地为正式实现）
