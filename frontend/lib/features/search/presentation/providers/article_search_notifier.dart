import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../feed/domain/models/feed_item.dart';
import 'article_search_providers.dart';

const _debounceMs = 350;

final articleSearchNotifierProvider =
    AsyncNotifierProvider<ArticleSearchNotifier, List<FeedItem>>(
  ArticleSearchNotifier.new,
);

class ArticleSearchNotifier extends AsyncNotifier<List<FeedItem>> {
  Timer? _debounce;
  CancelToken? _cancelToken;

  @override
  Future<List<FeedItem>> build() async {
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

    _debounce = Timer(const Duration(milliseconds: _debounceMs), () {
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
        return await ref.read(articleSearchRepositoryProvider).search(
              query: query,
              cancelToken: token,
            );
      } on DioException catch (error) {
        if (CancelToken.isCancel(error)) {
          return state.value ?? const [];
        }
        rethrow;
      }
    });
  }
}
