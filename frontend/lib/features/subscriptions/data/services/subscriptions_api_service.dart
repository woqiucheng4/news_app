import 'package:dio/dio.dart';

import '../../domain/models/topic_category.dart';
import '../../domain/models/subscription_item.dart';
import '../../domain/models/topic_item.dart';

class SubscriptionsApiService {
  SubscriptionsApiService(this._dio);

  final Dio _dio;

  Future<List<SubscriptionItem>> fetchMySubscriptions() async {
    final response = await _dio.get<List<dynamic>>('/subscriptions/me');
    final rawList = response.data ?? <dynamic>[];

    return rawList
        .whereType<Map<String, dynamic>>()
        .map(SubscriptionItem.fromJson)
        .toList(growable: false);
  }

  Future<void> updateSubscription(
    String topicId, {
    bool? isActive,
    bool? pushEnabled,
    bool? pushBreakingOnly,
    int? priority,
  }) async {
    final payload = <String, dynamic>{};

    if (isActive != null) payload['is_active'] = isActive;
    if (pushEnabled != null) payload['push_enabled'] = pushEnabled;
    if (pushBreakingOnly != null) payload['push_breaking_only'] = pushBreakingOnly;
    if (priority != null) payload['priority'] = priority;

    if (payload.isEmpty) return;

    await _dio.patch<void>('/subscriptions/me/$topicId', data: payload);
  }

  Future<void> unsubscribe(String topicId) async {
    await _dio.delete<void>('/subscriptions/unsubscribe/$topicId');
  }

  Future<List<TopicItem>> fetchTopics({
    String? query,
    String? category,
    int limit = 30,
    int offset = 0,
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/subscriptions/topics',
      cancelToken: cancelToken,
      queryParameters: {
        'q': query,
        'category': category,
        'limit': limit,
        'offset': offset,
      }..removeWhere((key, value) => value == null || value == ''),
    );

    final rawList = response.data ?? <dynamic>[];
    return rawList
        .whereType<Map<String, dynamic>>()
        .map(TopicItem.fromJson)
        .toList(growable: false);
  }

  Future<void> subscribeTopic(
    String topicId, {
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  }) async {
    await _dio.post<void>(
      '/subscriptions/subscribe',
      data: {
        'topic_id': topicId,
        'push_enabled': pushEnabled,
        'push_breaking_only': pushBreakingOnly,
      },
    );
  }

  Future<List<TopicCategory>> fetchTopicCategories() async {
    final response = await _dio.get<List<dynamic>>('/subscriptions/topics/categories');
    final rawList = response.data ?? <dynamic>[];

    return rawList
        .whereType<Map<String, dynamic>>()
        .map(TopicCategory.fromJson)
        .toList(growable: false);
  }

  Future<String?> subscribeByKeyword(
    String keyword, {
    String category = 'custom',
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/subscriptions/subscribe/keyword',
      data: {
        'keyword': keyword,
        'category': category,
        'push_enabled': pushEnabled,
        'push_breaking_only': pushBreakingOnly,
      },
    );

    final topic = (response.data?['topic'] as Map?)?.cast<String, dynamic>();
    return topic?['id'] as String?;
  }
}
