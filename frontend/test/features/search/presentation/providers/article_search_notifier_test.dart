import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:newsflow_frontend/features/feed/domain/models/feed_item.dart';
import 'package:newsflow_frontend/features/search/data/repositories/article_search_repository.dart';
import 'package:newsflow_frontend/features/search/presentation/providers/article_search_notifier.dart';
import 'package:newsflow_frontend/features/search/presentation/providers/article_search_providers.dart';

class _StubArticleSearchRepository implements ArticleSearchRepository {
  _StubArticleSearchRepository(this._handler);

  final Future<List<FeedItem>> Function(
    String query,
    CancelToken? cancelToken,
  ) _handler;

  @override
  Future<List<FeedItem>> search({
    required String query,
    int limit = 20,
    CancelToken? cancelToken,
  }) {
    return _handler(query, cancelToken);
  }
}

FeedItem _item(String id, String title) {
  return FeedItem(
    id: id,
    title: title,
    summary: 'summary',
    sourceUrl: 'https://example.com/$id',
  );
}

void main() {
  test('ArticleSearchNotifier debounces and returns results', () async {
    final container = ProviderContainer(
      overrides: [
        articleSearchRepositoryProvider.overrideWithValue(
          _StubArticleSearchRepository((query, cancelToken) async {
            await Future<void>.delayed(const Duration(milliseconds: 20));
            return [_item('a-1', 'Result for $query')];
          }),
        ),
      ],
    );
    addTearDown(container.dispose);

    final notifier = container.read(articleSearchNotifierProvider.notifier);

    notifier.onQueryChanged('ai');
    await Future<void>.delayed(const Duration(milliseconds: 450));

    final state = container.read(articleSearchNotifierProvider);
    expect(state.hasError, isFalse);
    expect(state.valueOrNull, hasLength(1));
    expect(state.valueOrNull!.first.title, 'Result for ai');
  });

  test('ArticleSearchNotifier clears results when query is empty', () async {
    final container = ProviderContainer(
      overrides: [
        articleSearchRepositoryProvider.overrideWithValue(
          _StubArticleSearchRepository((query, cancelToken) async {
            return [_item('a-1', query)];
          }),
        ),
      ],
    );
    addTearDown(container.dispose);

    final notifier = container.read(articleSearchNotifierProvider.notifier);
    notifier.onQueryChanged('news');
    await Future<void>.delayed(const Duration(milliseconds: 450));
    expect(container.read(articleSearchNotifierProvider).valueOrNull, isNotEmpty);

    notifier.onQueryChanged('');
    expect(container.read(articleSearchNotifierProvider).valueOrNull, isEmpty);
  });
}
