# NewsFlow Flutter 前端技术设计文档

**版本：** v1.0
**日期：** 2026-05-27
**状态：** Draft

---

## 1. 项目结构

```
lib/
├── main.dart                          # 应用入口
├── app.dart                           # MaterialApp 配置
│
├── core/                              # 核心基础设施
│   ├── constants/
│   │   ├── api_constants.dart         # API 端点、超时配置
│   │   ├── app_constants.dart         # 应用常量
│   │   └── storage_keys.dart          # 本地存储键名
│   ├── network/
│   │   ├── api_client.dart            # Dio 封装
│   │   ├── auth_interceptor.dart      # Token 注入 + 自动刷新
│   │   ├── error_interceptor.dart     # 统一错误处理
│   │   └── api_exception.dart         # 自定义异常类
│   ├── storage/
│   │   ├── local_storage.dart         # SharedPreferences 封装
│   │   └── secure_storage.dart        # FlutterSecureStorage 封装
│   ├── theme/
│   │   ├── app_theme.dart             # 主题定义（亮/暗）
│   │   ├── color_scheme.dart          # 色彩体系
│   │   └── text_styles.dart           # 文字样式
│   └── utils/
│       ├── date_formatter.dart        # 日期格式化
│       ├── url_launcher.dart          # 外部链接打开
│       └── platform_utils.dart        # 平台判断
│
├── features/                          # 功能模块（按功能划分）
│   ├── feed/                          # 信息流
│   │   ├── data/
│   │   │   ├── feed_repository.dart
│   │   │   └── feed_api.dart
│   │   ├── domain/
│   │   │   ├── models/
│   │   │   │   ├── article.dart       # Freezed 模型
│   │   │   │   └── feed_response.dart
│   │   │   └── services/
│   │   │       └── feed_service.dart
│   │   └── presentation/
│   │       ├── feed_page.dart
│   │       ├── feed_provider.dart     # Riverpod Notifier
│   │       ├── widgets/
│   │       │   ├── article_card.dart
│   │       │   ├── article_list.dart
│   │       │   └── feed_skeleton.dart
│   │       └── article_detail/
│   │           ├── article_detail_page.dart
│   │           └── article_detail_provider.dart
│   │
│   ├── search/                        # 搜索
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │       ├── search_page.dart
│   │       └── search_provider.dart
│   │
│   ├── auth/                          # 认证
│   │   ├── data/
│   │   │   └── auth_repository.dart
│   │   ├── domain/
│   │   │   └── models/
│   │   │       └── user.dart
│   │   └── presentation/
│   │       ├── login_page.dart
│   │       ├── register_page.dart
│   │       └── auth_provider.dart
│   │
│   ├── subscriptions/                 # 订阅管理
│   │   ├── data/
│   │   ├── domain/
│   │   │   └── models/
│   │   │       └── topic.dart
│   │   └── presentation/
│   │       ├── topics_page.dart
│   │       ├── subscriptions_page.dart
│   │       └── subscriptions_provider.dart
│   │
│   ├── notifications/                 # 通知
│   │   ├── data/
│   │   │   └── notification_repository.dart
│   │   ├── domain/
│   │   │   └── models/
│   │   │       ├── notification.dart
│   │   │       └── notification_preferences.dart
│   │   └── presentation/
│   │       ├── notifications_page.dart
│   │       ├── notification_settings_page.dart
│   │       └── notifications_provider.dart
│   │
│   ├── bookmarks/                     # 书签收藏
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │       ├── bookmarks_page.dart
│   │       └── bookmarks_provider.dart
│   │
│   ├── profile/                       # 个人中心
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   │       ├── profile_page.dart
│   │       ├── settings_page.dart
│   │       └── profile_provider.dart
│   │
│   └── onboarding/                    # 新手引导
│       └── presentation/
│           ├── onboarding_page.dart
│           └── topic_selection_page.dart
│
├── shared/                            # 共享组件
│   ├── widgets/
│   │   ├── app_bar.dart
│   │   ├── bottom_nav.dart
│   │   ├── loading_indicator.dart
│   │   ├── error_view.dart
│   │   ├── empty_view.dart
│   │   ├── cached_image.dart
│   │   └── shimmer_card.dart
│   └── extensions/
│       ├── context_extensions.dart
│       └── string_extensions.dart
│
└── router/                            # 路由配置
    └── app_router.dart
```

**目录原则：**
- 按功能模块划分（非按技术层划分）
- 每个模块内部遵循 data → domain → presentation 分层
- 共享组件放 `shared/widgets`，避免循环依赖

---

## 2. 状态管理 (Riverpod)

### 2.1 架构分层

```
┌─────────────────────────────────┐
│       Presentation (UI)         │  Widget → ref.watch(provider)
├─────────────────────────────────┤
│       Provider (State)          │  AsyncNotifier → state management
├─────────────────────────────────┤
│       Repository (Data)         │  API + Cache → data access
├─────────────────────────────────┤
│       API Client (Network)      │  Dio → HTTP communication
└─────────────────────────────────┘
```

### 2.2 Provider 类型选择

| 场景 | Provider 类型 | 示例 |
|---|---|---|
| 异步数据加载 | `AsyncNotifierProvider` | 信息流、文章详情 |
| 同步状态 | `NotifierProvider` | 主题、本地设置 |
| 依赖注入 | `Provider` | API Client、Repository |
| 一次性计算 | `FutureProvider` | 初始化配置 |
| 缓存派生 | `Provider` (computed) | 未读数、过滤列表 |

### 2.3 核心 Provider 设计

**API Client（全局单例）：**

```dart
@Riverpod(keepAlive: true)
Dio apiClient(ApiClientRef ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient.create(storage: storage);
}
```

**Repository（按模块）：**

```dart
@Riverpod(keepAlive: true)
FeedRepository feedRepository(FeedRepositoryRef ref) {
  return FeedRepository(api: ref.watch(apiClientProvider));
}
```

**信息流 Notifier：**

```dart
@riverpod
class FeedNotifier extends _$FeedNotifier {
  @override
  FutureOr<List<Article>> build() async {
    final repo = ref.watch(feedRepositoryProvider);
    final response = await repo.getFeed(page: 1);
    return response.items;
  }

  Future<void> loadMore() async {
    final current = state.value ?? [];
    final repo = ref.read(feedRepositoryProvider);
    final nextPage = (current.length ~/ 20) + 1;
    final response = await repo.getFeed(page: nextPage);
    if (!ref.mounted) return;
    state = AsyncData([...current, ...response.items]);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => build());
  }
}
```

**文章详情 Notifier：**

```dart
@riverpod
class ArticleDetailNotifier extends _$ArticleDetailNotifier {
  @override
  FutureOr<Article> build(String articleId) async {
    final repo = ref.watch(feedRepositoryProvider);
    return repo.getArticle(articleId);
  }

  Future<void> toggleBookmark() async {
    final article = state.value;
    if (article == null) return;
    final repo = ref.read(feedRepositoryProvider);
    await repo.toggleBookmark(article.id);
    if (!ref.mounted) return;
    state = AsyncData(article.copyWith(isBookmarked: !article.isBookmarked));
  }

  Future<void> generateSummary() async {
    final article = state.value;
    if (article == null) return;
    final repo = ref.read(feedRepositoryProvider);
    final result = await repo.generateSummary(article.id);
    if (!ref.mounted) return;
    state = AsyncData(article.copyWith(summary: result.summary));
  }
}
```

**认证状态：**

```dart
@Riverpod(keepAlive: true)
class AuthNotifier extends _$AuthNotifier {
  @override
  FutureOr<User?> build() async {
    final storage = ref.watch(secureStorageProvider);
    final token = await storage.getAccessToken();
    if (token == null) return null;
    final repo = ref.watch(authRepositoryProvider);
    return repo.getCurrentUser();
  }

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(authRepositoryProvider);
      final result = await repo.login(email: email, password: password);
      await ref.read(secureStorageProvider).saveTokens(
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      );
      return result.user;
    });
  }

  Future<void> logout() async {
    await ref.read(secureStorageProvider).clearTokens();
    state = const AsyncData(null);
  }
}
```

**通知偏好 Notifier：**

```dart
@riverpod
class NotificationPreferencesNotifier extends _$NotificationPreferencesNotifier {
  @override
  FutureOr<NotificationPreferences> build() async {
    final repo = ref.watch(notificationRepositoryProvider);
    return repo.getPreferences();
  }

  Future<void> updatePreferences(NotificationPreferences prefs) async {
    final repo = ref.read(notificationRepositoryProvider);
    await repo.updatePreferences(prefs);
    if (!ref.mounted) return;
    state = AsyncData(prefs);
  }

  Future<void> togglePush(bool enabled) async {
    final current = state.valueOrNull;
    if (current == null) return;
    await updatePreferences(current.copyWith(pushEnabled: enabled));
  }

  Future<void> setQuietHours(String start, String end) async {
    final current = state.valueOrNull;
    if (current == null) return;
    await updatePreferences(current.copyWith(
      quietHoursStart: start,
      quietHoursEnd: end,
    ));
  }

  Future<void> setMinRelevanceScore(double score) async {
    final current = state.valueOrNull;
    if (current == null) return;
    await updatePreferences(current.copyWith(minRelevanceScore: score));
  }

  Future<void> linkTelegram(String chatId) async {
    final repo = ref.read(notificationRepositoryProvider);
    await repo.linkTelegram(chatId);
    final current = state.valueOrNull;
    if (current == null) return;
    if (!ref.mounted) return;
    state = AsyncData(current.copyWith(
      telegramChatId: chatId,
      pushChannel: 'telegram',
    ));
  }
}
```

### 2.4 UI 消费模式

```dart
class FeedPage extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feedAsync = ref.watch(feedNotifierProvider);

    return feedAsync.when(
      loading: () => const FeedSkeleton(),
      error: (error, stack) => ErrorView(
        onRetry: () => ref.invalidate(feedNotifierProvider),
      ),
      data: (articles) => RefreshIndicator(
        onRefresh: () => ref.read(feedNotifierProvider.notifier).refresh(),
        child: ArticleList(
          articles: articles,
          onLoadMore: () => ref.read(feedNotifierProvider.notifier).loadMore(),
        ),
      ),
    );
  }
}
```

---

## 3. 路由设计 (go_router)

### 3.1 路由表

| 路径 | 页面 | 认证要求 |
|---|---|---|
| `/` | Shell (底部导航) | - |
| `/feed` | 信息流 (首页 Tab) | 否 |
| `/feed/:id` | 文章详情 | 否 |
| `/discover` | 发现 (Tab) | 否 |
| `/bookmarks` | 收藏 (Tab) | 是 |
| `/profile` | 个人中心 (Tab) | 否 |
| `/profile/settings` | 设置 | 是 |
| `/notifications` | 通知列表 | 是 |
| `/notifications/settings` | 通知渠道设置 | 是 |
| `/search` | 搜索 | 否 |
| `/topics` | 话题浏览 | 否 |
| `/login` | 登录 | 否 |
| `/register` | 注册 | 否 |
| `/onboarding` | 新手引导 | 否 |

### 3.2 路由配置

```dart
final appRouter = GoRouter(
  initialLocation: '/feed',
  redirect: _authGuard,
  routes: [
    // 底部导航 Shell
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return MainScaffold(navigationShell: navigationShell);
      },
      branches: [
        // 首页 Tab
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/feed',
            builder: (_, __) => const FeedPage(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (_, state) => ArticleDetailPage(
                  articleId: state.pathParameters['id']!,
                ),
              ),
            ],
          ),
        ]),
        // 发现 Tab
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/discover',
            builder: (_, __) => const TopicsPage(),
          ),
        ]),
        // 收藏 Tab
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/bookmarks',
            builder: (_, __) => const BookmarksPage(),
          ),
        ]),
        // 个人中心 Tab
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/profile',
            builder: (_, __) => const ProfilePage(),
            routes: [
              GoRoute(
                path: 'settings',
                builder: (_, __) => const SettingsPage(),
              ),
            ],
          ),
        ]),
      ],
    ),

    // 独立页面（无底部导航）
    GoRoute(
      path: '/notifications',
      builder: (_, __) => const NotificationsPage(),
      routes: [
        GoRoute(
          path: 'settings',
          builder: (_, __) => const NotificationSettingsPage(),
        ),
      ],
    ),
    GoRoute(
      path: '/search',
      builder: (_, __) => const SearchPage(),
    ),
    GoRoute(
      path: '/login',
      builder: (_, __) => const LoginPage(),
    ),
    GoRoute(
      path: '/register',
      builder: (_, __) => const RegisterPage(),
    ),
    GoRoute(
      path: '/onboarding',
      builder: (_, __) => const OnboardingPage(),
    ),
  ],
);
```

### 3.3 认证守卫

```dart
Future<String?> _authGuard(BuildContext context, GoRouterState state) {
  final authState = ProviderScope.containerOf(context)
      .read(authNotifierProvider);

  final isLoggedIn = authState.valueOrNull != null;
  final isPublicRoute = ['/feed', '/discover', '/login', '/register', '/onboarding']
      .any((path) => state.matchedLocation.startsWith(path));

  if (!isLoggedIn && !isPublicRoute) {
    return '/login';
  }
  if (isLoggedIn && state.matchedLocation == '/login') {
    return '/feed';
  }
  return null; // 不重定向
}
```

### 3.4 Deep Link 支持

```dart
// 支持的 Deep Link 格式
// https://newflow.app/feed/{articleId}
// https://newflow.app/topics/{topicSlug}

GoRoute(
  path: '/feed/:id',
  // go_router 自动处理 deep link 到此路径
)
```

---

## 4. 网络层设计 (Dio)

### 4.1 API Client 封装

```dart
class ApiClient {
  static Dio create({required SecureStorage storage}) {
    final dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    dio.interceptors.addAll([
      AuthInterceptor(storage: storage),
      ErrorInterceptor(),
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => log(obj.toString()),
      ),
    ]);

    return dio;
  }
}
```

### 4.2 Auth Interceptor（Token 自动注入 + 刷新）

```dart
class AuthInterceptor extends Interceptor {
  final SecureStorage storage;
  bool _isRefreshing = false;
  final _queue = <Completer<void>>[];

  AuthInterceptor({required this.storage});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = storage.getAccessTokenSync();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      if (_isRefreshing) {
        // 排队等待刷新完成
        final completer = Completer<void>();
        _queue.add(completer);
        await completer.future;
        // 用新 token 重试
        final token = storage.getAccessTokenSync();
        err.requestOptions.headers['Authorization'] = 'Bearer $token';
        final response = await Dio().fetch(err.requestOptions);
        return handler.resolve(response);
      }

      _isRefreshing = true;
      try {
        final refreshToken = await storage.getRefreshToken();
        if (refreshToken == null) {
          return handler.reject(err);
        }

        final response = await Dio().post(
          '${ApiConstants.baseUrl}/auth/refresh',
          data: {'refresh_token': refreshToken},
        );

        await storage.saveTokens(
          accessToken: response.data['access_token'],
          refreshToken: response.data['refresh_token'],
        );

        // 重试原请求
        final token = storage.getAccessTokenSync();
        err.requestOptions.headers['Authorization'] = 'Bearer $token';
        final retryResponse = await Dio().fetch(err.requestOptions);

        // 释放排队的请求
        for (final completer in _queue) {
          completer.complete();
        }
        _queue.clear();

        return handler.resolve(retryResponse);
      } catch (e) {
        // 刷新失败，清除 token
        await storage.clearTokens();
        for (final completer in _queue) {
          completer.completeError(e);
        }
        _queue.clear();
        return handler.reject(err);
      } finally {
        _isRefreshing = false;
      }
    }

    handler.next(err);
  }
}
```

### 4.3 Error Interceptor（统一错误处理）

```dart
class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final exception = switch (err.type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout => ApiException(
        message: '网络连接超时，请检查网络',
        code: 'TIMEOUT',
      ),
      DioExceptionType.connectionError => ApiException(
        message: '无法连接服务器',
        code: 'NO_CONNECTION',
      ),
      DioExceptionType.badResponse => _handleBadResponse(err.response!),
      _ => ApiException(
        message: '未知错误',
        code: 'UNKNOWN',
      ),
    };

    handler.reject(DioException(
      requestOptions: err.requestOptions,
      error: exception,
    ));
  }

  ApiException _handleBadResponse(Response response) {
    final data = response.data;
    return switch (response.statusCode) {
      400 => ApiException(
        message: data?['error']?['message'] ?? '请求参数错误',
        code: 'VALIDATION_ERROR',
        details: data?['error']?['details'],
      ),
      401 => ApiException(message: '登录已过期', code: 'UNAUTHORIZED'),
      403 => ApiException(message: '权限不足', code: 'FORBIDDEN'),
      404 => ApiException(message: '资源不存在', code: 'NOT_FOUND'),
      429 => ApiException(message: '请求过于频繁', code: 'RATE_LIMITED'),
      _ => ApiException(
        message: '服务器错误 (${response.statusCode})',
        code: 'SERVER_ERROR',
      ),
    };
  }
}
```

### 4.4 Repository 示例

```dart
class FeedRepository {
  final Dio api;

  FeedRepository({required this.api});

  Future<FeedResponse> getFeed({int page = 1, int pageSize = 20}) async {
    final response = await api.get('/api/v1/articles/feed', queryParameters: {
      'page': page,
      'page_size': pageSize,
    });
    return FeedResponse.fromJson(response.data);
  }

  Future<Article> getArticle(String id) async {
    final response = await api.get('/api/v1/articles/$id');
    return Article.fromJson(response.data);
  }

  Future<SearchResponse> search(String query, {int limit = 20}) async {
    final response = await api.get('/api/v1/articles/search', queryParameters: {
      'q': query,
      'limit': limit,
    });
    return SearchResponse.fromJson(response.data);
  }

  Future<SummaryResult> generateSummary(String articleId) async {
    final response = await api.post('/api/v1/articles/$articleId/summary');
    return SummaryResult.fromJson(response.data);
  }

  Future<void> toggleBookmark(String articleId) async {
    await api.post('/api/v1/articles/$articleId/bookmark');
  }
}
```

```dart
class NotificationRepository {
  final Dio api;

  NotificationRepository({required this.api});

  Future<NotificationPreferences> getPreferences() async {
    final response = await api.get('/api/v1/notifications/preferences');
    return NotificationPreferences.fromJson(response.data);
  }

  Future<void> updatePreferences(NotificationPreferences prefs) async {
    await api.put('/api/v1/notifications/preferences', data: prefs.toJson());
  }

  Future<void> linkTelegram(String chatId) async {
    await api.post('/api/v1/notifications/telegram/link', data: {
      'chat_id': chatId,
    });
  }

  Future<void> registerPushToken(String token, String platform) async {
    await api.post('/api/v1/notifications/register', data: {
      'token': token,
      'platform': platform,
    });
  }
}
```

---

## 5. 数据模型 (Freezed)

### 5.1 Article

```dart
@freezed
sealed class Article with _$Article {
  const factory Article({
    required String id,
    required String title,
    required String url,
    required SourceInfo source,
    required DateTime publishedAt,
    String? summary,
    String? content,
    String? excerpt,
    String? author,
    String? category,
    @Default([]) List<String> tags,
    String? eventId,
    @Default(false) bool isBookmarked,
    @Default(0) int viewCount,
    @Default(0) int bookmarkCount,
    String? summaryModel,
  }) = _Article;

  factory Article.fromJson(Map<String, dynamic> json) =>
      _$ArticleFromJson(json);
}

@freezed
sealed class SourceInfo with _$SourceInfo {
  const factory SourceInfo({
    required String id,
    required String name,
    String? iconUrl,
    String? url,
  }) = _SourceInfo;

  factory SourceInfo.fromJson(Map<String, dynamic> json) =>
      _$SourceInfoFromJson(json);
}
```

### 5.2 FeedResponse

```dart
@freezed
sealed class FeedResponse with _$FeedResponse {
  const factory FeedResponse({
    required List<Article> items,
    required int total,
    required int page,
    required int pageSize,
    required bool hasNext,
  }) = _FeedResponse;

  factory FeedResponse.fromJson(Map<String, dynamic> json) =>
      _$FeedResponseFromJson(json);
}
```

### 5.3 User

```dart
@freezed
sealed class User with _$User {
  const factory User({
    required String id,
    required String email,
    String? displayName,
    String? avatarUrl,
    @Default(false) bool isPremium,
    @Default(0) int subscriptionCount,
    DateTime? createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) =>
      _$UserFromJson(json);
}
```

### 5.4 Topic

```dart
@freezed
sealed class Topic with _$Topic {
  const factory Topic({
    required String id,
    required String name,
    required String slug,
    String? description,
    String? category,
    String? iconUrl,
    @Default(0) int subscriberCount,
    @Default(false) bool isSubscribed,
  }) = _Topic;

  factory Topic.fromJson(Map<String, dynamic> json) =>
      _$TopicFromJson(json);
}
```

### 5.5 Notification

```dart
@Freezed(unionKey: 'type', unionValueCase: FreezedUnionCase.snake)
sealed class AppNotification with _$AppNotification {
  const factory AppNotification.dailyBriefing({
    required String id,
    required String title,
    required String body,
    required DateTime createdAt,
    @Default(false) bool isRead,
  }) = DailyBriefingNotification;

  const factory AppNotification.breaking({
    required String id,
    required String title,
    required String body,
    required DateTime createdAt,
    @Default(false) bool isRead,
    String? articleId,
  }) = BreakingNotification;

  const factory AppNotification.update({
    required String id,
    required String title,
    required String body,
    required DateTime createdAt,
    @Default(false) bool isRead,
    String? articleId,
  }) = UpdateNotification;

  factory AppNotification.fromJson(Map<String, dynamic> json) =>
      _$AppNotificationFromJson(json);
}
```

### 5.6 API Error

```dart
@freezed
sealed class ApiException with _$AppException implements Exception {
  const factory ApiException({
    required String message,
    required String code,
    List<Map<String, String>>? details,
  }) = _ApiException;
}
```

### 5.7 NotificationPreferences

```dart
@freezed
sealed class NotificationPreferences with _$NotificationPreferences {
  const factory NotificationPreferences({
    @Default(true) bool pushEnabled,
    @Default('fcm') String pushChannel,       // fcm / telegram
    @Default(true) bool emailNotifications,
    String? telegramChatId,
    String? webhookUrl,                        // P2
    String? quietHoursStart,                   // "22:00"
    String? quietHoursEnd,                     // "08:00"
    @Default('UTC') String quietHoursTimezone,
    @Default(6.0) double minRelevanceScore,    // 推送价值阈值
  }) = _NotificationPreferences;

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) =>
      _$NotificationPreferencesFromJson(json);
}
```

---

## 6. 离线支持

### 6.1 离线策略

| 数据 | 离线策略 | 存储方式 |
|---|---|---|
| 文章列表 | 缓存最近 100 条 | SQLite (drift) |
| 文章详情 | 缓存已读文章 | SQLite |
| 用户设置 | 始终本地存储 | SharedPreferences |
| Token | 始终本地存储 | FlutterSecureStorage |
| 图片 | LRU 缓存 | cached_network_image |

### 6.2 缓存流程

```
请求文章列表
    │
    ├─ 有网络 → 从 API 获取 → 更新本地缓存 → 返回
    │
    └─ 无网络 → 从本地缓存返回 → 显示离线标记
```

### 6.3 实现要点

```dart
class FeedRepository {
  final Dio api;
  final FeedCacheDao cacheDao;

  Future<FeedResponse> getFeed({int page = 1, bool forceRefresh = false}) async {
    if (!forceRefresh) {
      // 尝试读缓存
      final cached = await cacheDao.getFeedPage(page);
      if (cached != null && !cached.isStale) {
        return cached.toResponse();
      }
    }

    try {
      final response = await api.get('/api/v1/articles/feed', queryParameters: {
        'page': page,
      });
      final feedResponse = FeedResponse.fromJson(response.data);

      // 写入缓存
      await cacheDao.saveFeedPage(page, feedResponse);

      return feedResponse;
    } on ApiException catch (e) {
      if (e.code == 'NO_CONNECTION' || e.code == 'TIMEOUT') {
        // 离线降级
        final cached = await cacheDao.getFeedPage(page);
        if (cached != null) {
          return cached.toResponse();
        }
      }
      rethrow;
    }
  }
}
```

---

## 7. 推送通知 (FCM)

### 7.1 集成流程

```dart
class PushNotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  Future<void> initialize() async {
    // 请求权限
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      // 获取 Token
      final token = await _messaging.getToken();
      if (token != null) {
        await _registerToken(token);
      }

      // Token 刷新监听
      _messaging.onTokenRefresh.listen(_registerToken);

      // 前台消息处理
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

      // 后台/终止状态点击处理
      FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);

      // 检查是否从通知启动
      final initialMessage = await _messaging.getInitialMessage();
      if (initialMessage != null) {
        _handleMessageOpenedApp(initialMessage);
      }
    }
  }

  Future<void> _registerToken(String token) async {
    final api = GetIt.instance<Dio>();
    await api.post('/api/v1/notifications/register', data: {
      'token': token,
      'platform': Platform.isIOS ? 'ios' : 'android',
    });
  }

  void _handleForegroundMessage(RemoteMessage message) {
    // 显示本地通知
    LocalNotifications.show(
      title: message.notification?.title ?? '',
      body: message.notification?.body ?? '',
      payload: message.data,
    );
  }

  void _handleMessageOpenedApp(RemoteMessage message) {
    // 根据 data 中的 type 和 id 导航
    final type = message.data['type'];
    final id = message.data['id'];
    switch (type) {
      case 'article':
        appRouter.go('/feed/$id');
      case 'event':
        appRouter.go('/feed?event=$id');
    }
  }
}
```

### 7.2 Topic 订阅

```dart
// 用户订阅话题时，同步订阅 FCM topic
Future<void> subscribeTopic(String topicSlug) async {
  await FirebaseMessaging.instance.subscribeToTopic('topic_$topicSlug');
}

Future<void> unsubscribeTopic(String topicSlug) async {
  await FirebaseMessaging.instance.unsubscribeFromTopic('topic_$topicSlug');
}
```

---

## 8. 主题与国际化

### 8.1 主题系统

```dart
class AppTheme {
  static ThemeData light() => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF1A73E8),
      brightness: Brightness.light,
    ),
    scaffoldBackgroundColor: const Color(0xFFF8F9FA),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
    ),
    cardTheme: CardTheme(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
  );

  static ThemeData dark() => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF1A73E8),
      brightness: Brightness.dark,
    ),
    scaffoldBackgroundColor: const Color(0xFF121212),
    cardTheme: CardTheme(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
  );
}
```

### 8.2 国际化

使用 Flutter 内置 `gen-l10n`：

```
lib/
├── l10n/
│   ├── app_en.arb
│   ├── app_zh.arb
│   └── app_ja.arb
```

```json
// app_en.arb
{
  "appTitle": "NewsFlow",
  "feedTab": "Feed",
  "discoverTab": "Discover",
  "bookmarksTab": "Bookmarks",
  "profileTab": "Profile",
  "searchHint": "Search articles...",
  "pullToRefresh": "Pull to refresh",
  "noArticles": "No articles yet",
  "offlineMode": "You are offline",
  "loginTitle": "Welcome Back",
  "loginButton": "Sign In",
  "registerButton": "Create Account"
}
```

---

## 9. 核心页面设计

### 9.1 信息流页 (FeedPage)

```
┌─────────────────────────────────────┐
│ NewsFlow                    [🔍] [🔔]│  AppBar
├─────────────────────────────────────┤
│ [全部] [科技] [财经] [娱乐] [+]      │  CategoryChips (横向滚动)
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ [图标] TechCrunch · 2h ago     │ │  ArticleCard
│ │ Apple 发布新 iPhone 17         │ │
│ │ Apple 今日发布了新一代 iPhone...│ │
│ │                    [🔖] [↗️]   │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ [图标] Reuters · 3h ago        │ │
│ │ NVIDIA 股价创新高              │ │
│ │ 受 AI 芯片需求推动...           │ │
│ │                    [🔖] [↗️]   │ │
│ └─────────────────────────────────┘ │
│ ...                                 │
├─────────────────────────────────────┤
│ [🏠首页] [🔍发现] [🔖收藏] [👤我的] │  BottomNav
└─────────────────────────────────────┘
```

### 9.2 文章详情页 (ArticleDetailPage)

```
┌─────────────────────────────────────┐
│ [←]                         [🔖] [↗️]│  AppBar
├─────────────────────────────────────┤
│                                     │
│ Apple 发布新 iPhone 17             │  Title (18sp, Bold)
│                                     │
│ TechCrunch · 2026-05-27            │  Source + Date (14sp, Gray)
│                                     │
│ ─────────────────────────────────── │  Divider
│                                     │
│ 【AI 摘要】                         │  Section header
│ Apple 今日发布了新一代 iPhone 17，  │  Summary (15sp)
│ 搭载 A19 芯片，性能提升 30%。      │
│ 新增卫星通信功能，售价 $999 起。    │
│                                     │
│ ─────────────────────────────────── │  Divider
│                                     │
│ [相关报道]                          │  Related articles
│ ┌─────────────────────────────────┐ │
│ │ iPhone 17 首周销量预测...       │ │  Related card
│ └─────────────────────────────────┘ │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ [阅读原文 →]                        │  Link button
│                                     │
└─────────────────────────────────────┘
```

### 9.3 通知设置页 (NotificationSettingsPage)

```
┌─────────────────────────────────────┐
│ [←] 通知设置                        │  AppBar
├─────────────────────────────────────┤
│                                     │
│ ── 推送渠道 ─────────────────────── │
│                                     │
│ [📱 FCM Push]           [✓ 已选中]  │  RadioListTile
│ [📧 Email]              [ ]         │
│ [✈️ Telegram]           [ ]         │  P1，点击后引导绑定
│                                     │
│ ── 免打扰时段 ───────────────────── │
│                                     │
│ 开启免打扰              [开关 🔘]   │  SwitchListTile
│                                     │
│ 开始时间                22:00       │  TimePicker
│ 结束时间                08:00       │  TimePicker
│ 时区                    自动检测    │  Dropdown
│                                     │
│ ── 推送过滤 ─────────────────────── │
│                                     │
│ 最低推送价值            ██████░░ 6  │  Slider (1-10)
│ 只推送"重大"新闻        [开关 🔘]   │  ≥8 分才推送
│                                     │
│ ── 邮件设置 ─────────────────────── │
│                                     │
│ 收件邮箱                user@...    │  自动读取账号邮箱
│                                     │
│ ── Telegram 设置 (P1) ───────────── │
│                                     │
│ 绑定状态                未绑定      │
│ [绑定 Telegram Bot]                 │  Button → 跳转 Bot
│                                     │
└─────────────────────────────────────┘
```

### 9.4 ArticleCard 组件

```dart
class ArticleCard extends ConsumerWidget {
  final Article article;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        onTap: onTap ?? () => context.go('/feed/${article.id}'),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 来源 + 时间
              Row(
                children: [
                  CachedImage(
                    url: article.source.iconUrl,
                    width: 20,
                    height: 20,
                    borderRadius: 4,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    article.source.name,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const Spacer(),
                  Text(
                    _formatTime(article.publishedAt),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // 标题
              Text(
                article.title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (article.summary != null) ...[
                const SizedBox(height: 8),
                // 摘要
                Text(
                  article.summary!,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
              const SizedBox(height: 12),
              // 操作按钮
              Row(
                children: [
                  const Spacer(),
                  IconButton(
                    icon: Icon(
                      article.isBookmarked
                          ? Icons.bookmark
                          : Icons.bookmark_border,
                    ),
                    onPressed: () => ref
                        .read(feedNotifierProvider.notifier)
                        .toggleBookmark(article.id),
                  ),
                  IconButton(
                    icon: const Icon(Icons.open_in_new),
                    onPressed: () => launchUrl(Uri.parse(article.url)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

---

## 10. 依赖清单

### 10.1 pubspec.yaml

```yaml
name: newflow
description: AI-powered information aggregation app
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.2.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_localizations:
    sdk: flutter

  # State Management
  flutter_riverpod: ^3.3.0
  riverpod_annotation: ^3.0.0

  # Routing
  go_router: ^17.0.0

  # Network
  dio: ^5.4.0

  # Models
  freezed_annotation: ^3.0.0
  json_annotation: ^4.9.0

  # Storage
  shared_preferences: ^2.2.0
  flutter_secure_storage: ^9.0.0
  drift: ^2.15.0           # SQLite (离线缓存)

  # UI
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0
  flutter_local_notifications: ^18.0.0

  # Firebase
  firebase_core: ^3.0.0
  firebase_messaging: ^15.0.0

  # Auth
  google_sign_in: ^6.2.0
  sign_in_with_apple: ^6.1.0

  # Utils
  intl: ^0.19.0
  url_launcher: ^6.2.0
  path_provider: ^2.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter

  # Code Generation
  build_runner: ^2.4.0
  riverpod_generator: ^3.0.0
  freezed: ^3.0.0
  json_serializable: ^6.8.0
  drift_dev: ^2.15.0

  # Lint
  flutter_lints: ^4.0.0

  # Testing
  mocktail: ^1.0.0
```

### 10.2 代码生成

```bash
# 一次性生成所有
dart run build_runner build --delete-conflicting-outputs

# 监听模式（开发时）
dart run build_runner watch --delete-conflicting-outputs
```

---

## 11. 测试策略

### 11.1 测试分层

| 层级 | 工具 | 覆盖目标 |
|---|---|---|
| Unit Test | `flutter_test` | Repository、Service、工具函数 |
| Widget Test | `flutter_test` | 独立组件渲染和交互 |
| Integration Test | `integration_test` | 完整用户流程 |

### 11.2 Mock 方案

```dart
// 使用 Riverpod 的 overrides 进行测试
testWidgets('FeedPage shows articles', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        feedRepositoryProvider.overrideWithValue(
          FakeFeedRepository(articles: [mockArticle]),
        ),
      ],
      child: const MaterialApp(home: FeedPage()),
    ),
  );

  await tester.pumpAndSettle();
  expect(find.text('Apple 发布新 iPhone 17'), findsOneWidget);
});
```

---

## 12. 构建与发布

### 12.1 环境配置

```dart
// lib/core/config.dart
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.newflow.app',
  );

  static const String environment = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: 'production',
  );
}
```

```bash
# 开发环境
flutter run --dart-define=API_BASE_URL=http://localhost:8000 --dart-define=ENVIRONMENT=development

# 生产环境
flutter build apk --dart-define=API_BASE_URL=https://api.newflow.app --dart-define=ENVIRONMENT=production
```

### 12.2 发布流程

```
1. 更新版本号 (pubspec.yaml)
2. flutter build appbundle (Android) / flutter build ipa (iOS)
3. 上传到 Google Play Console / App Store Connect
4. 提交审核
```

---

*文档版本：v1.0*
*最后更新：2026-05-27*
