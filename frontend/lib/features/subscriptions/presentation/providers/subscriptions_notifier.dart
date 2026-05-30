import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../core/network/api_client.dart';
import '../../data/repositories/subscriptions_repository.dart';
import '../../data/services/subscriptions_api_service.dart';
import '../../domain/models/subscription_item.dart';

final subscriptionsApiServiceProvider = Provider<SubscriptionsApiService>((ref) {
  final dio = ref.watch(dioProvider);
  return SubscriptionsApiService(dio);
});

final subscriptionsRepositoryProvider = Provider<SubscriptionsRepository>((ref) {
  final service = ref.watch(subscriptionsApiServiceProvider);
  return SubscriptionsRepository(service);
});

final subscriptionsNotifierProvider =
    AsyncNotifierProvider<SubscriptionsNotifier, List<SubscriptionItem>>(
  SubscriptionsNotifier.new,
);

class SubscriptionsNotifier extends AsyncNotifier<List<SubscriptionItem>> {
  @override
  Future<List<SubscriptionItem>> build() async {
    final repository = ref.read(subscriptionsRepositoryProvider);
    return repository.getMySubscriptions();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repository = ref.read(subscriptionsRepositoryProvider);
      return repository.getMySubscriptions();
    });
    if (!state.hasError) {
      ref.read(appAnalyticsProvider).trackSubscriptionListRefresh(source: 'pull');
    }
  }

  Future<void> togglePush(String topicId, bool enabled) async {
    final previous = state;
    final current = state.valueOrNull;
    if (current == null) return;

    state = AsyncData(
      current
          .map(
            (item) => item.topicId == topicId ? item.copyWith(pushEnabled: enabled) : item,
          )
          .toList(growable: false),
    );

    final repository = ref.read(subscriptionsRepositoryProvider);
    final result = await AsyncValue.guard(() => repository.setPushEnabled(topicId, enabled));
    ref.read(appAnalyticsProvider).trackSubscriptionPushToggle(
          topicId: topicId,
          enabled: enabled,
          success: !result.hasError,
        );
    if (result.hasError) {
      state = previous;
    }
  }

  Future<void> removeSubscription(String topicId) async {
    final previous = state;
    final current = state.valueOrNull;
    if (current == null) return;

    state = AsyncData(
      current.where((item) => item.topicId != topicId).toList(growable: false),
    );

    final repository = ref.read(subscriptionsRepositoryProvider);
    final result = await AsyncValue.guard(() => repository.unsubscribe(topicId));
    ref.read(appAnalyticsProvider).trackSubscriptionUnsubscribe(
          topicId: topicId,
          success: !result.hasError,
        );
    if (result.hasError) {
      state = previous;
    }
  }
}
