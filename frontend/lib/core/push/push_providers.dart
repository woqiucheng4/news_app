import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_client.dart';
import 'notifications_api_service.dart';
import 'push_notification_service.dart';

final notificationsApiServiceProvider = Provider<NotificationsApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return NotificationsApiService(dio);
});

final pushNotificationServiceProvider = Provider<PushNotificationService>((ref) {
  final api = ref.watch(notificationsApiServiceProvider);
  return PushNotificationService(api);
});

final pushTopicSyncProvider = Provider<PushTopicSync>((ref) {
  return PushTopicSync(ref);
});

class PushTopicSync {
  PushTopicSync(this._ref);

  final Ref _ref;

  Future<void> subscribe(String topicId) {
    return _ref.read(pushNotificationServiceProvider).subscribeToTopic(topicId);
  }

  Future<void> unsubscribe(String topicId) {
    return _ref
        .read(pushNotificationServiceProvider)
        .unsubscribeFromTopic(topicId);
  }

  Future<void> syncAll({
    required Iterable<({String topicId, bool pushEnabled})> subscriptions,
  }) async {
    final service = _ref.read(pushNotificationServiceProvider);
    for (final item in subscriptions) {
      await service.syncTopicSubscriptions(
        topicIds: [item.topicId],
        pushEnabled: item.pushEnabled,
      );
    }
  }
}
