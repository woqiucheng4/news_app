# 02-03 Flutter Search Scaffold

> Phase index: [`02-03-PHASE_SUMMARY.md`](./02-03-PHASE_SUMMARY.md) · API SoT: [`02-03-API_CONTRACT.md`](./02-03-API_CONTRACT.md)

## Goal

- 提供 Flutter 端的搜索接入完整代码骨架，覆盖：
  - DTO（复用 02-02 的 `ArticleDto`）
  - 防抖 + 取消的搜索 Datasource
  - Repository + Riverpod `AsyncNotifier`
  - 与 02-02 话题搜索结合的双 Tab 全局搜索 UI
  - 空态 / 加载态 / 错误态完整处理

## File Layout

```text
lib/features/search/
  data/
    datasources/
      article_search_api.dart
    repositories/
      article_search_repository.dart
  presentation/
    providers/
      search_providers.dart
    pages/
      search_page.dart
      _search_results_articles.dart
      _search_results_topics.dart
```

> 注：Article DTO 复用 02-02 已生成的 `lib/features/feed/data/models/article_dto.dart`。
> Topic 搜索复用 02-02 的 `topicsNotifierProvider`（带 `query` 参数）。

## 1) Datasource

```dart
// lib/features/search/data/datasources/article_search_api.dart
import 'package:dio/dio.dart';
import '../../../feed/data/models/article_dto.dart';

class ArticleSearchApi {
  ArticleSearchApi(this._dio);
  final Dio _dio;

  Future<List<ArticleDto>> searchArticles({
    required String query,
    int limit = 20,
    CancelToken? cancelToken,
  }) async {
    if (query.isEmpty) return const [];
    final res = await _dio.get(
      '/api/v1/articles/search',
      queryParameters: {'q': query, 'limit': limit},
      cancelToken: cancelToken,
    );
    final list = (res.data as List).cast<Map<String, dynamic>>();
    return list.map(ArticleDto.fromJson).toList();
  }
}
```

## 2) Repository

```dart
// lib/features/search/data/repositories/article_search_repository.dart
import 'package:dio/dio.dart';
import '../../../feed/data/models/article_dto.dart';
import '../datasources/article_search_api.dart';

abstract interface class ArticleSearchRepository {
  Future<List<ArticleDto>> search({
    required String query,
    int limit,
    CancelToken? cancelToken,
  });
}

class ArticleSearchRepositoryImpl implements ArticleSearchRepository {
  ArticleSearchRepositoryImpl(this._api);
  final ArticleSearchApi _api;

  @override
  Future<List<ArticleDto>> search({
    required String query,
    int limit = 20,
    CancelToken? cancelToken,
  }) =>
      _api.searchArticles(query: query, limit: limit, cancelToken: cancelToken);
}
```

## 3) Riverpod Notifier (with Debounce + Cancellation)

```dart
// lib/features/search/presentation/providers/search_providers.dart
import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../feed/data/models/article_dto.dart';
import '../../data/repositories/article_search_repository.dart';

part 'search_providers.g.dart';

const _debounceMs = 350;

@riverpod
class ArticleSearchNotifier extends _$ArticleSearchNotifier {
  Timer? _debounce;
  CancelToken? _cancelToken;

  @override
  Future<List<ArticleDto>> build() async {
    ref.onDispose(() {
      _debounce?.cancel();
      _cancelToken?.cancel('disposed');
    });
    return const [];
  }

  /// UI 调用：每次输入 onChanged 触发，内部防抖 350ms
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
      _runSearch(query);
    });
  }

  Future<void> _runSearch(String query) async {
    _cancelToken?.cancel('superseded');
    final ct = CancelToken();
    _cancelToken = ct;

    state = const AsyncLoading();
    final repo = ref.read(articleSearchRepositoryProvider);
    state = await AsyncValue.guard(() async {
      try {
        return await repo.search(query: query, limit: 20, cancelToken: ct);
      } on DioException catch (e) {
        if (CancelToken.isCancel(e)) return const [];
        rethrow;
      }
    });
  }
}

// providers wiring (示例)
final articleSearchApiProvider =
    Provider<ArticleSearchApi>((ref) => ArticleSearchApi(ref.read(apiClientProvider)));

final articleSearchRepositoryProvider = Provider<ArticleSearchRepository>(
  (ref) => ArticleSearchRepositoryImpl(ref.read(articleSearchApiProvider)),
);
```

## 4) Search Page UI（双 Tab：文章 + 话题）

```dart
// lib/features/search/presentation/pages/search_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '_search_results_articles.dart';
import '_search_results_topics.dart';
import '../providers/search_providers.dart';
import '../../../subscription/presentation/providers/subscription_providers.dart';

class SearchPage extends ConsumerStatefulWidget {
  const SearchPage({super.key});

  @override
  ConsumerState<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends ConsumerState<SearchPage> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    ref.read(articleSearchNotifierProvider.notifier).onQueryChanged(value);
    // 02-02 已有的 topicsNotifier 接受 query；这里同步触发
    ref.read(topicsNotifierProvider.notifier).setQuery(value);
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: TextField(
            controller: _controller,
            autofocus: true,
            decoration: const InputDecoration(
              hintText: '搜索文章 / 话题',
              border: InputBorder.none,
            ),
            onChanged: _onChanged,
            textInputAction: TextInputAction.search,
          ),
          actions: [
            if (_controller.text.isNotEmpty)
              IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  _controller.clear();
                  _onChanged('');
                  setState(() {});
                },
              ),
          ],
          bottom: const TabBar(
            tabs: [Tab(text: '文章'), Tab(text: '话题')],
          ),
        ),
        body: const TabBarView(
          children: [
            SearchResultsArticles(),
            SearchResultsTopics(),
          ],
        ),
      ),
    );
  }
}
```

```dart
// lib/features/search/presentation/pages/_search_results_articles.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/search_providers.dart';

class SearchResultsArticles extends ConsumerWidget {
  const SearchResultsArticles({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncResults = ref.watch(articleSearchNotifierProvider);

    return asyncResults.when(
      data: (articles) {
        if (articles.isEmpty) {
          return const Center(child: Text('输入关键词搜索文章'));
        }
        return ListView.separated(
          itemCount: articles.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, i) {
            final a = articles[i];
            return ListTile(
              title: Text(a.title, maxLines: 2, overflow: TextOverflow.ellipsis),
              subtitle: Text(
                a.summary ?? a.excerpt ?? '',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: Text(
                a.publishedAt?.split('T').first ?? '',
                style: Theme.of(context).textTheme.labelSmall,
              ),
              onTap: () {
                // TODO: navigate to article detail
              },
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('搜索失败：$e')),
    );
  }
}
```

```dart
// lib/features/search/presentation/pages/_search_results_topics.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../subscription/presentation/providers/subscription_providers.dart';

class SearchResultsTopics extends ConsumerWidget {
  const SearchResultsTopics({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncTopics = ref.watch(topicsNotifierProvider);

    return asyncTopics.when(
      data: (topics) {
        if (topics.isEmpty) {
          return const Center(child: Text('输入关键词搜索话题'));
        }
        return ListView.separated(
          itemCount: topics.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, i) {
            final t = topics[i];
            return ListTile(
              title: Text(t.name),
              subtitle: Text(t.description ?? ''),
              trailing: t.isSubscribed
                  ? const Chip(label: Text('已订阅'))
                  : ElevatedButton(
                      onPressed: () {
                        // TODO: subscribe via 02-02 API
                      },
                      child: const Text('订阅'),
                    ),
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('搜索失败：$e')),
    );
  }
}
```

## 5) Wiring (添加到 main.dart 路由)

```dart
// 在 go_router 配置中添加：
GoRoute(
  path: '/search',
  builder: (context, state) => const SearchPage(),
),

// AppBar 中加入搜索按钮：
IconButton(
  icon: const Icon(Icons.search),
  onPressed: () => context.go('/search'),
),
```

## 6) 防抖 / 取消行为说明

| 用户行为 | Notifier 内部行为 | 网络层 |
|---|---|---|
| 输入"a" | 启动 350ms timer | 不发请求 |
| 200ms 后输入"ai" | cancel 旧 timer，重启 350ms | 不发请求 |
| 350ms 后无新输入 | timer fires，调 `_runSearch("ai")` | 发请求 + 创建 CancelToken |
| 100ms 后再输入"ai " | 取消上一个 CancelToken（'superseded'）；新 timer 启动 | 取消请求 + 不发新请求 |
| 用户清空输入 | 取消 timer + 取消 in-flight 请求 | 取消请求；state = `AsyncData([])` |
| 用户离开页面 | `ref.onDispose` 取消 timer + token | 取消请求 |

## Definition of Done (Flutter Search 接入)

- [ ] 输入关键词 350ms 后自动搜索，UI 不卡顿
- [ ] 快速连续输入只发最后一次请求
- [ ] 离开搜索页或清空输入立即取消 in-flight 请求
- [ ] 双 Tab 同时搜文章和话题，互不干扰
- [ ] 空态、加载态、错误态都有合理 UI
- [ ] 0 结果时显示提示语而非空白页

## Cross-Reference

- Backend 接口：[`02-03-API_CONTRACT.md`](./02-03-API_CONTRACT.md)
- 02-02 话题搜索：[`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md) §2 Topic List
- 02-02 ArticleDto 模板：[`02-02-FLUTTER_FREEZED_MODELS.md`](./02-02-FLUTTER_FREEZED_MODELS.md)
- 02-02 网络层：[`02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md`](./02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md)（提供 `apiClientProvider`）
