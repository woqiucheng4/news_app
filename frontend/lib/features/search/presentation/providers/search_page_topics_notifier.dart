import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../subscriptions/domain/models/topic_item.dart';
import '../../../subscriptions/presentation/providers/subscriptions_notifier.dart';

const _topicPageSize = 20;

final searchPageTopicsNotifierProvider =
    AsyncNotifierProvider<SearchPageTopicsNotifier, List<TopicItem>>(
  SearchPageTopicsNotifier.new,
);

class SearchPageTopicsNotifier extends AsyncNotifier<List<TopicItem>> {
  Timer? _debounce;
  CancelToken? _cancelToken;

  @override
  Future<List<TopicItem>> build() async {
    ref.onDispose(() {
      _debounce?.cancel();
      _cancelToken?.cancel('disposed');
    });
    return const [];
  }

  void onQueryChanged(String raw) {
    final query = raw.trim();
    _debounce?.cancel();

    if (query.isEmpty) {
      _cancelToken?.cancel('cleared');
      _cancelToken = null;
      state = const AsyncData([]);
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 350), () {
      unawaited(_runSearch(query));
    });
  }

  Future<void> _runSearch(String query) async {
    _cancelToken?.cancel('superseded');
    final token = CancelToken();
    _cancelToken = token;

    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      try {
        return await ref.read(subscriptionsRepositoryProvider).getTopics(
              query: query,
              limit: _topicPageSize,
              offset: 0,
              cancelToken: token,
            );
      } on DioException catch (error) {
        if (error.type == DioExceptionType.cancel) {
          return state.value ?? const [];
        }
        rethrow;
      }
    });
  }

  Future<bool> subscribeTopic(String topicId) async {
    final repository = ref.read(subscriptionsRepositoryProvider);
    await repository.subscribe(topicId);
    ref.invalidate(subscriptionsNotifierProvider);

    final current = state.value;
    if (current == null) {
      return true;
    }

    state = AsyncData(
      current
          .map(
            (item) => item.id == topicId
                ? item.copyWith(
                    isSubscribed: true,
                    subscriberCount: item.subscriberCount + 1,
                  )
                : item,
          )
          .toList(growable: false),
    );
    return true;
  }
}
