# 02-02 Flutter Repository + Riverpod Notifiers

> Phase index: [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) · API SoT: [`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md)

## Goal

- 基于已定义的 API 契约和 DTO，提供可直接粘贴的 Repository + Riverpod 状态管理模板。
- 覆盖：
  - 话题目录与搜索分页
  - 我的订阅列表
  - 关键词订阅
  - 订阅重排（乐观更新 + 回滚）
  - 个性化 Feed 分页

## 1) Repository Interfaces

```dart
abstract interface class SubscriptionRepository {
  Future<List<TopicCategoryDto>> getCategories();

  Future<List<TopicDto>> getTopics({
    String? category,
    String? query,
    int limit = 20,
    int offset = 0,
  });

  Future<List<SubscriptionDto>> getMySubscriptions({
    int limit = 100,
    int offset = 0,
  });

  Future<void> subscribeTopic({
    required String topicId,
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  });

  Future<TopicDto> subscribeKeyword({
    required String keyword,
    String category = 'custom',
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  });

  Future<void> updateSubscription({
    required String topicId,
    bool? isActive,
    int? priority,
    bool? pushEnabled,
    bool? pushBreakingOnly,
  });

  Future<void> reorderSubscriptions({
    required List<({String topicId, int priority})> items,
  });

  Future<void> unsubscribe(String topicId);
}

abstract interface class FeedRepository {
  Future<FeedResponseDto> getFeed({
    int page = 1,
    int pageSize = 20,
  });
}
```

## 2) Repository Implementations

```dart
class SubscriptionRepositoryImpl implements SubscriptionRepository {
  SubscriptionRepositoryImpl(this._api);
  final SubscriptionApi _api;

  @override
  Future<List<TopicCategoryDto>> getCategories() => _api.getCategories();

  @override
  Future<List<TopicDto>> getTopics({
    String? category,
    String? query,
    int limit = 20,
    int offset = 0,
  }) {
    return _api.getTopics(
      category: category,
      q: query,
      limit: limit,
      offset: offset,
    );
  }

  @override
  Future<List<SubscriptionDto>> getMySubscriptions({
    int limit = 100,
    int offset = 0,
  }) {
    return _api.getMySubscriptions();
  }

  @override
  Future<void> subscribeTopic({
    required String topicId,
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  }) {
    return _api.subscribeTopic(
      topicId: topicId,
      pushEnabled: pushEnabled,
      pushBreakingOnly: pushBreakingOnly,
    );
  }

  @override
  Future<TopicDto> subscribeKeyword({
    required String keyword,
    String category = 'custom',
    bool pushEnabled = true,
    bool pushBreakingOnly = false,
  }) {
    return _api.subscribeKeyword(
      keyword: keyword,
      category: category,
    );
  }

  @override
  Future<void> updateSubscription({
    required String topicId,
    bool? isActive,
    int? priority,
    bool? pushEnabled,
    bool? pushBreakingOnly,
  }) {
    return _api.updateSubscription(
      topicId: topicId,
      isActive: isActive,
      priority: priority,
      pushEnabled: pushEnabled,
      pushBreakingOnly: pushBreakingOnly,
    );
  }

  @override
  Future<void> reorderSubscriptions({
    required List<({String topicId, int priority})> items,
  }) {
    return _api.reorderSubscriptions([
      for (final item in items)
        {'topic_id': item.topicId, 'priority': item.priority},
    ]);
  }

  @override
  Future<void> unsubscribe(String topicId) => _api.unsubscribe(topicId);
}

class FeedRepositoryImpl implements FeedRepository {
  FeedRepositoryImpl(this._api);
  final FeedApi _api;

  @override
  Future<FeedResponseDto> getFeed({int page = 1, int pageSize = 20}) {
    return _api.getFeed(page: page, pageSize: pageSize);
  }
}
```

## 3) State Models (Freezed)

```dart
@freezed
class TopicListState with _$TopicListState {
  const factory TopicListState({
    @Default(<TopicDto>[]) List<TopicDto> items,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingMore,
    @Default(false) bool hasMore,
    String? category,
    String? query,
    String? error,
  }) = _TopicListState;
}

@freezed
class SubscriptionListState with _$SubscriptionListState {
  const factory SubscriptionListState({
    @Default(<SubscriptionDto>[]) List<SubscriptionDto> items,
    @Default(false) bool isLoading,
    String? error,
  }) = _SubscriptionListState;
}

@freezed
class FeedListState with _$FeedListState {
  const factory FeedListState({
    @Default(<ArticleDto>[]) List<ArticleDto> items,
    @Default(1) int nextPage,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingMore,
    @Default(true) bool hasMore,
    String? error,
  }) = _FeedListState;
}
```

## 4) Providers Wiring

```dart
final subscriptionRepositoryProvider = Provider<SubscriptionRepository>((ref) {
  final api = ref.watch(subscriptionApiProvider);
  return SubscriptionRepositoryImpl(api);
});

final feedRepositoryProvider = Provider<FeedRepository>((ref) {
  final api = ref.watch(feedApiProvider);
  return FeedRepositoryImpl(api);
});
```

## 5) Topics Notifier (Query + Pagination)

```dart
@riverpod
class TopicsNotifier extends _$TopicsNotifier {
  static const _pageSize = 20;

  @override
  TopicListState build() => const TopicListState();

  Future<void> loadFirstPage({String? category, String? query}) async {
    state = state.copyWith(
      isLoading: true,
      category: category,
      query: query,
      error: null,
      items: const [],
    );

    try {
      final items = await ref.read(subscriptionRepositoryProvider).getTopics(
            category: category,
            query: query,
            limit: _pageSize,
            offset: 0,
          );
      state = state.copyWith(
        isLoading: false,
        items: items,
        hasMore: items.length == _pageSize,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true, error: null);

    try {
      final next = await ref.read(subscriptionRepositoryProvider).getTopics(
            category: state.category,
            query: state.query,
            limit: _pageSize,
            offset: state.items.length,
          );
      state = state.copyWith(
        isLoadingMore: false,
        items: [...state.items, ...next],
        hasMore: next.length == _pageSize,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: e.toString());
    }
  }
}
```

## 6) My Subscriptions Notifier (Optimistic Reorder)

```dart
@riverpod
class MySubscriptionsNotifier extends _$MySubscriptionsNotifier {
  @override
  SubscriptionListState build() => const SubscriptionListState();

  Future<void> refresh() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final items =
          await ref.read(subscriptionRepositoryProvider).getMySubscriptions();
      state = state.copyWith(isLoading: false, items: items);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> subscribeKeyword(String keyword) async {
    state = state.copyWith(error: null);
    try {
      await ref.read(subscriptionRepositoryProvider).subscribeKeyword(
            keyword: keyword,
          );
      await refresh();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> unsubscribe(String topicId) async {
    final oldItems = state.items;
    final newItems = oldItems.where((e) => e.topic.id != topicId).toList();
    state = state.copyWith(items: newItems, error: null); // optimistic remove

    try {
      await ref.read(subscriptionRepositoryProvider).unsubscribe(topicId);
    } catch (e) {
      state = state.copyWith(items: oldItems, error: e.toString()); // rollback
    }
  }

  Future<void> reorder(List<SubscriptionDto> reordered) async {
    final previous = state.items;
    state = state.copyWith(items: reordered, error: null); // optimistic reorder

    try {
      final payload = <({String topicId, int priority})>[];
      for (int index = 0; index < reordered.length; index++) {
        // larger priority means higher rank
        payload.add((topicId: reordered[index].topic.id, priority: reordered.length - index));
      }
      await ref.read(subscriptionRepositoryProvider).reorderSubscriptions(items: payload);
    } catch (e) {
      state = state.copyWith(items: previous, error: e.toString()); // rollback
    }
  }
}
```

## 7) Feed Notifier (Infinite Scroll)

```dart
@riverpod
class FeedNotifier extends _$FeedNotifier {
  static const _pageSize = 20;

  @override
  FeedListState build() => const FeedListState();

  Future<void> refresh() async {
    state = state.copyWith(
      isLoading: true,
      isLoadingMore: false,
      error: null,
      nextPage: 1,
      hasMore: true,
      items: const [],
    );
    await _loadPage(1, replace: true);
  }

  Future<void> loadMore() async {
    if (state.isLoading || state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true, error: null);
    await _loadPage(state.nextPage, replace: false);
  }

  Future<void> _loadPage(int page, {required bool replace}) async {
    try {
      final result = await ref.read(feedRepositoryProvider).getFeed(
            page: page,
            pageSize: _pageSize,
          );
      final merged = replace ? result.articles : [...state.items, ...result.articles];
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        items: merged,
        nextPage: page + 1,
        hasMore: result.hasMore,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        error: e.toString(),
      );
    }
  }
}
```

## 8) UI Integration Tips

- 进入页面先触发：
  - 目录页：`topicsNotifier.loadFirstPage()`
  - 订阅页：`mySubscriptionsNotifier.refresh()`
  - Feed 页：`feedNotifier.refresh()`
- 搜索防抖建议 300ms，避免每次输入都打 API。
- 重排完成后不立即强制 refresh，先用乐观更新，失败再回滚。
- 所有错误统一走 `state.error` 显示 toast/snackbar，避免页面闪烁。
