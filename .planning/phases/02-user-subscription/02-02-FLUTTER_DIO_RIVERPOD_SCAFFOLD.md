# 02-02 Flutter Scaffold: Dio + Riverpod API Layer

> Phase index: [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) · API SoT: [`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md)

## Current Repo Status

- 当前仓库尚未包含 Flutter 工程（未检测到 `pubspec.yaml` / `.dart` 文件）。
- 本文提供可直接复制到 Flutter 项目的接口层草稿，覆盖 02-02 已落地的后端契约。

## Recommended File Layout

```text
lib/
  core/network/
    api_client.dart
    auth_interceptor.dart
  features/subscription/data/
    datasources/subscription_api.dart
    models/topic_dto.dart
    models/subscription_dto.dart
    models/topic_category_dto.dart
  features/feed/data/
    datasources/feed_api.dart
    models/article_dto.dart
    models/feed_response_dto.dart
  features/subscription/presentation/providers/
    subscription_providers.dart
  features/feed/presentation/providers/
    feed_providers.dart
```

## 1) Dio Client + Auth Interceptor

```dart
// lib/core/network/api_client.dart
import 'package:dio/dio.dart';
import 'auth_interceptor.dart';

class ApiClient {
  ApiClient({
    required String baseUrl,
    required AuthTokenReader tokenReader,
  }) : dio = Dio(
          BaseOptions(
            baseUrl: baseUrl,
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 15),
            headers: {'Content-Type': 'application/json'},
          ),
        ) {
    dio.interceptors.add(AuthInterceptor(tokenReader: tokenReader));
  }

  final Dio dio;
}
```

```dart
// lib/core/network/auth_interceptor.dart
import 'package:dio/dio.dart';

abstract class AuthTokenReader {
  Future<String?> readAccessToken();
}

class AuthInterceptor extends Interceptor {
  AuthInterceptor({required this.tokenReader});

  final AuthTokenReader tokenReader;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await tokenReader.readAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}
```

## 2) Subscription DTOs

```dart
// topic_dto.dart
class TopicDto {
  TopicDto({
    required this.id,
    required this.name,
    required this.slug,
    required this.subscriberCount,
    required this.isSubscribed,
    this.description,
    this.category,
  });

  final String id;
  final String name;
  final String slug;
  final String? description;
  final String? category;
  final int subscriberCount;
  final bool isSubscribed;

  factory TopicDto.fromJson(Map<String, dynamic> json) => TopicDto(
        id: json['id'] as String,
        name: json['name'] as String,
        slug: json['slug'] as String,
        description: json['description'] as String?,
        category: json['category'] as String?,
        subscriberCount: (json['subscriber_count'] as num?)?.toInt() ?? 0,
        isSubscribed: json['is_subscribed'] as bool? ?? false,
      );
}
```

```dart
// topic_category_dto.dart
class TopicCategoryDto {
  TopicCategoryDto({required this.name, required this.topicCount});

  final String name;
  final int topicCount;

  factory TopicCategoryDto.fromJson(Map<String, dynamic> json) =>
      TopicCategoryDto(
        name: json['name'] as String,
        topicCount: (json['topic_count'] as num).toInt(),
      );
}
```

```dart
// subscription_dto.dart
import 'topic_dto.dart';

class SubscriptionDto {
  SubscriptionDto({
    required this.topic,
    required this.isActive,
    required this.priority,
    required this.pushEnabled,
    required this.pushBreakingOnly,
    required this.subscribedAt,
  });

  final TopicDto topic;
  final bool isActive;
  final int priority;
  final bool pushEnabled;
  final bool pushBreakingOnly;
  final DateTime subscribedAt;

  factory SubscriptionDto.fromJson(Map<String, dynamic> json) =>
      SubscriptionDto(
        topic: TopicDto.fromJson(json['topic'] as Map<String, dynamic>),
        isActive: json['is_active'] as bool,
        priority: (json['priority'] as num).toInt(),
        pushEnabled: json['push_enabled'] as bool,
        pushBreakingOnly: json['push_breaking_only'] as bool,
        subscribedAt: DateTime.parse(json['subscribed_at'] as String),
      );
}
```

## 3) Subscription API Datasource

```dart
// subscription_api.dart
import 'package:dio/dio.dart';
import '../models/topic_dto.dart';
import '../models/topic_category_dto.dart';
import '../models/subscription_dto.dart';

class SubscriptionApi {
  SubscriptionApi(this._dio);
  final Dio _dio;

  Future<List<TopicCategoryDto>> getCategories() async {
    final res = await _dio.get('/api/v1/subscriptions/topics/categories');
    return (res.data as List)
        .map((e) => TopicCategoryDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<TopicDto>> getTopics({
    String? category,
    String? q,
    int limit = 20,
    int offset = 0,
  }) async {
    final res = await _dio.get(
      '/api/v1/subscriptions/topics',
      queryParameters: {
        if (category != null) 'category': category,
        if (q != null) 'q': q,
        'limit': limit,
        'offset': offset,
      },
    );
    return (res.data as List)
        .map((e) => TopicDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<SubscriptionDto>> getMySubscriptions() async {
    final res = await _dio.get('/api/v1/subscriptions/me');
    return (res.data as List)
        .map((e) => SubscriptionDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> subscribeTopic({
    required String topicId,
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  }) async {
    await _dio.post(
      '/api/v1/subscriptions/subscribe',
      data: {
        'topic_id': topicId,
        'push_enabled': pushEnabled,
        'push_breaking_only': pushBreakingOnly,
      },
    );
  }

  Future<TopicDto> subscribeKeyword({
    required String keyword,
    String category = 'custom',
  }) async {
    final res = await _dio.post(
      '/api/v1/subscriptions/subscribe/keyword',
      data: {'keyword': keyword, 'category': category},
    );
    final payload = res.data as Map<String, dynamic>;
    return TopicDto.fromJson(payload['topic'] as Map<String, dynamic>);
  }

  Future<void> updateSubscription({
    required String topicId,
    bool? isActive,
    int? priority,
    bool? pushEnabled,
    bool? pushBreakingOnly,
  }) async {
    await _dio.patch(
      '/api/v1/subscriptions/me/$topicId',
      data: {
        if (isActive != null) 'is_active': isActive,
        if (priority != null) 'priority': priority,
        if (pushEnabled != null) 'push_enabled': pushEnabled,
        if (pushBreakingOnly != null) 'push_breaking_only': pushBreakingOnly,
      },
    );
  }

  Future<void> reorderSubscriptions(List<Map<String, dynamic>> items) async {
    await _dio.put(
      '/api/v1/subscriptions/me/reorder',
      data: {'items': items},
    );
  }

  Future<void> unsubscribe(String topicId) async {
    await _dio.delete('/api/v1/subscriptions/unsubscribe/$topicId');
  }
}
```

## 4) Feed API Datasource

```dart
// feed_api.dart
import 'package:dio/dio.dart';
import '../models/feed_response_dto.dart';

class FeedApi {
  FeedApi(this._dio);
  final Dio _dio;

  Future<FeedResponseDto> getFeed({int page = 1, int pageSize = 20}) async {
    final res = await _dio.get(
      '/api/v1/articles/feed',
      queryParameters: {'page': page, 'page_size': pageSize},
    );
    return FeedResponseDto.fromJson(res.data as Map<String, dynamic>);
  }
}
```

## 5) Riverpod Provider Sketch

```dart
// subscription_providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

final subscriptionApiProvider = Provider<SubscriptionApi>((ref) {
  final client = ref.watch(apiClientProvider);
  return SubscriptionApi(client.dio);
});

@riverpod
class MySubscriptionsNotifier extends _$MySubscriptionsNotifier {
  @override
  Future<List<SubscriptionDto>> build() async {
    return ref.watch(subscriptionApiProvider).getMySubscriptions();
  }

  Future<void> refreshData() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(subscriptionApiProvider).getMySubscriptions(),
    );
  }
}
```

## Integration Checklist

- [ ] 在 Flutter 工程中添加 `dio`、`flutter_riverpod`（以及 `riverpod_annotation`/`build_runner` 若使用代码生成）。
- [ ] 接入统一 token 存储实现 `AuthTokenReader`。
- [ ] 以 `02-02-API_CONTRACT.md` 为唯一字段来源，避免前后端字段命名偏差。
- [ ] DTO 建议优先使用 `02-02-FLUTTER_FREEZED_MODELS.md` 中的 Freezed 版本，减少手写解析错误。
- [ ] Repository + Riverpod Notifier 建议参考 `02-02-FLUTTER_REPOSITORY_RIVERPOD_NOTIFIERS.md`。
- [ ] 先联通 `topics/categories -> topics -> subscribe -> my subscriptions -> reorder -> feed` 主链路。
