# 02-02 Flutter DTOs (Freezed + Json Serializable)

> Phase index: [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) · API SoT: [`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md)

## Purpose

- 将 `02-02-API_CONTRACT.md` 中的接口字段，映射为可代码生成的 Flutter DTO。
- 适用于 `freezed + json_serializable` 技术栈（与项目约定一致）。

## Dependencies

在 Flutter 工程 `pubspec.yaml` 中加入（示例）：

```yaml
dependencies:
  freezed_annotation: ^2.4.4
  json_annotation: ^4.9.0

dev_dependencies:
  build_runner: ^2.4.12
  freezed: ^2.5.7
  json_serializable: ^6.8.0
```

生成命令：

```bash
dart run build_runner build --delete-conflicting-outputs
```

## 1) TopicCategoryDto

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'topic_category_dto.freezed.dart';
part 'topic_category_dto.g.dart';

@freezed
class TopicCategoryDto with _$TopicCategoryDto {
  const factory TopicCategoryDto({
    required String name,
    @JsonKey(name: 'topic_count') required int topicCount,
  }) = _TopicCategoryDto;

  factory TopicCategoryDto.fromJson(Map<String, dynamic> json) =>
      _$TopicCategoryDtoFromJson(json);
}
```

## 2) TopicDto

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'topic_dto.freezed.dart';
part 'topic_dto.g.dart';

@freezed
class TopicDto with _$TopicDto {
  const factory TopicDto({
    required String id,
    required String name,
    required String slug,
    String? description,
    String? category,
    @JsonKey(name: 'subscriber_count') @Default(0) int subscriberCount,
    @JsonKey(name: 'is_subscribed') @Default(false) bool isSubscribed,
  }) = _TopicDto;

  factory TopicDto.fromJson(Map<String, dynamic> json) =>
      _$TopicDtoFromJson(json);
}
```

## 3) SubscriptionDto

```dart
import 'package:freezed_annotation/freezed_annotation.dart';
import 'topic_dto.dart';

part 'subscription_dto.freezed.dart';
part 'subscription_dto.g.dart';

@freezed
class SubscriptionDto with _$SubscriptionDto {
  const factory SubscriptionDto({
    required TopicDto topic,
    @JsonKey(name: 'is_active') required bool isActive,
    required int priority,
    @JsonKey(name: 'push_enabled') required bool pushEnabled,
    @JsonKey(name: 'push_breaking_only') required bool pushBreakingOnly,
    @JsonKey(name: 'subscribed_at') required DateTime subscribedAt,
  }) = _SubscriptionDto;

  factory SubscriptionDto.fromJson(Map<String, dynamic> json) =>
      _$SubscriptionDtoFromJson(json);
}
```

## 4) ArticleDto

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'article_dto.freezed.dart';
part 'article_dto.g.dart';

@freezed
class ArticleDto with _$ArticleDto {
  const factory ArticleDto({
    required String id,
    required String title,
    required String url,
    String? excerpt,
    String? summary,
    String? author,
    Map<String, dynamic>? source,
    String? category,
    @Default(<String>[]) List<String> tags,
    @JsonKey(name: 'published_at') DateTime? publishedAt,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'view_count') @Default(0) int viewCount,
    @JsonKey(name: 'bookmark_count') @Default(0) int bookmarkCount,
  }) = _ArticleDto;

  factory ArticleDto.fromJson(Map<String, dynamic> json) =>
      _$ArticleDtoFromJson(json);
}
```

## 5) FeedResponseDto

```dart
import 'package:freezed_annotation/freezed_annotation.dart';
import 'article_dto.dart';

part 'feed_response_dto.freezed.dart';
part 'feed_response_dto.g.dart';

@freezed
class FeedResponseDto with _$FeedResponseDto {
  const factory FeedResponseDto({
    required int page,
    @JsonKey(name: 'page_size') required int pageSize,
    required List<ArticleDto> articles,
    @JsonKey(name: 'has_more') required bool hasMore,
  }) = _FeedResponseDto;

  factory FeedResponseDto.fromJson(Map<String, dynamic> json) =>
      _$FeedResponseDtoFromJson(json);
}
```

## 6) Optional: Common ApiResult Wrapper

如需统一处理 `{ "success": true }` 这种响应，可选增加：

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'api_result_dto.freezed.dart';
part 'api_result_dto.g.dart';

@freezed
class ApiResultDto with _$ApiResultDto {
  const factory ApiResultDto({
    required bool success,
    int? updated,
  }) = _ApiResultDto;

  factory ApiResultDto.fromJson(Map<String, dynamic> json) =>
      _$ApiResultDtoFromJson(json);
}
```

## 7) Mapping Notes

- `snake_case` 字段统一通过 `@JsonKey(name: '...')` 映射。
- `DateTime` 字段后端返回 ISO8601，`json_serializable` 可直接解析。
- 对可能缺省字段（如 `tags`、`is_subscribed`）使用 `@Default(...)` 降低空值风险。
- 如后续后端扩字段，可优先添加可空字段，避免强制升级导致客户端崩溃。
