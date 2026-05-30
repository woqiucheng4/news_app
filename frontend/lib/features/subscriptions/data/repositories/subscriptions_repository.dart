import 'package:dio/dio.dart';

import '../../domain/models/subscription_item.dart';
import '../../domain/models/topic_category.dart';
import '../../domain/models/topic_item.dart';
import '../services/subscriptions_api_service.dart';

class SubscriptionsRepository {
  SubscriptionsRepository(this._apiService);

  final SubscriptionsApiService _apiService;

  Future<List<SubscriptionItem>> getMySubscriptions() {
    return _apiService.fetchMySubscriptions();
  }

  Future<void> setPushEnabled(String topicId, bool enabled) {
    return _apiService.updateSubscription(topicId, pushEnabled: enabled);
  }

  Future<void> unsubscribe(String topicId) {
    return _apiService.unsubscribe(topicId);
  }

  Future<List<TopicItem>> getTopics({
    String? query,
    String? category,
    int limit = 30,
    int offset = 0,
    CancelToken? cancelToken,
  }) {
    return _apiService.fetchTopics(
      query: query,
      category: category,
      limit: limit,
      offset: offset,
      cancelToken: cancelToken,
    );
  }

  Future<void> subscribe(String topicId) {
    return _apiService.subscribeTopic(topicId);
  }

  Future<List<TopicCategory>> getTopicCategories() {
    return _apiService.fetchTopicCategories();
  }

  Future<String?> subscribeByKeyword(
    String keyword, {
    String category = 'custom',
  }) {
    return _apiService.subscribeByKeyword(keyword, category: category);
  }
}
