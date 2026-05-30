import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:newsflow_frontend/features/feed/data/local/feed_cache_store.dart';
import 'package:newsflow_frontend/features/feed/data/repositories/feed_repository.dart';
import 'package:newsflow_frontend/features/feed/data/services/feed_api_service.dart';
import 'package:newsflow_frontend/features/feed/domain/models/feed_item.dart';
import 'package:newsflow_frontend/features/feed/domain/models/feed_page.dart';
import 'package:newsflow_frontend/features/feed/presentation/providers/feed_data_providers.dart';
import 'package:newsflow_frontend/features/feed/presentation/providers/topic_feed_notifier.dart';
import '../../../../helpers/stub_article_detail_repository.dart';

class StubFeedRepository extends FeedRepository {
  StubFeedRepository(this._pages, FeedCacheStore cacheStore)
      : super(FeedApiService(Dio()), cacheStore);

  final Map<int, FeedPage> _pages;

  @override
  Future<FeedFetchResult> getFeedPage({
    int page = 1,
    int pageSize = 20,
    bool forceNetwork = false,
    String? topicId,
  }) async {
    expect(topicId, 'topic-ai');
    final pageData = _pages[page] ??
        FeedPage(
          page: page,
          articles: const [],
          hasMore: false,
        );
    return FeedFetchResult(
      page: pageData,
      fromCache: false,
      isOfflineFallback: false,
    );
  }
}

FeedItem _item(String id) {
  return FeedItem(
    id: id,
    title: 'Title $id',
    summary: 'Summary',
    sourceUrl: 'https://example.com/$id',
  );
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('TopicFeedNotifier loads topic-scoped feed', () async {
    final cacheStore = FeedCacheStore(SharedPreferences.getInstance());
    final container = ProviderContainer(
      overrides: [
        topicFeedScopeProvider.overrideWithValue(const TopicFeedScope('topic-ai')),
        feedRepositoryProvider.overrideWithValue(
          StubFeedRepository(
            {
              1: FeedPage(
                page: 1,
                articles: [_item('t-1')],
                hasMore: false,
              ),
            },
            cacheStore,
          ),
        ),
        articleDetailRepositoryProvider.overrideWith(
          (ref) => StubArticleDetailRepository(
            (_) async => throw UnimplementedError(),
          ),
        ),
      ],
    );
    addTearDown(container.dispose);

    final state = await container.read(topicFeedNotifierProvider.future);
    expect(state, hasLength(1));
    expect(state.first.id, 't-1');
  });
}
