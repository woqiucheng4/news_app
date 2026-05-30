# 02-02 Flutter Minimal UI Templates

> Phase index: [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) · API SoT: [`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md)

## Goal

- 提供可直接复制的最小 UI 模板：
  - `SubscriptionPage`（目录/关键词订阅/我的订阅）
  - `FeedPage`（信息流首屏 + 下拉加载）
  - `main.dart`（双 Tab 入口）
- 与前文 Notifier 命名保持一致：
  - `topicsNotifierProvider`
  - `mySubscriptionsNotifierProvider`
  - `feedNotifierProvider`

## 1) `subscription_page.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/subscription_providers.dart';

class SubscriptionPage extends ConsumerStatefulWidget {
  const SubscriptionPage({super.key});

  @override
  ConsumerState<SubscriptionPage> createState() => _SubscriptionPageState();
}

class _SubscriptionPageState extends ConsumerState<SubscriptionPage> {
  final _keywordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await ref.read(topicsNotifierProvider.notifier).loadFirstPage();
      await ref.read(mySubscriptionsNotifierProvider.notifier).refresh();
      await ref.read(topicCategoriesProvider.future); // preload categories
    });
  }

  @override
  void dispose() {
    _keywordController.dispose();
    super.dispose();
  }

  Future<void> _subscribeKeyword() async {
    final keyword = _keywordController.text.trim();
    if (keyword.isEmpty) return;
    await ref.read(mySubscriptionsNotifierProvider.notifier).subscribeKeyword(keyword);
    _keywordController.clear();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('关键词订阅成功')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final topicState = ref.watch(topicsNotifierProvider);
    final myState = ref.watch(mySubscriptionsNotifierProvider);
    final categories = ref.watch(topicCategoriesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('订阅管理')),
      body: RefreshIndicator(
        onRefresh: () async {
          await ref.read(topicsNotifierProvider.notifier).loadFirstPage();
          await ref.read(mySubscriptionsNotifierProvider.notifier).refresh();
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text('分类目录', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            categories.when(
              data: (items) => Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final c in items)
                    ActionChip(
                      label: Text('${c.name} (${c.topicCount})'),
                      onPressed: () {
                        ref.read(topicsNotifierProvider.notifier).loadFirstPage(category: c.name);
                      },
                    ),
                ],
              ),
              loading: () => const LinearProgressIndicator(),
              error: (e, _) => Text('分类加载失败: $e'),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _keywordController,
                    decoration: const InputDecoration(
                      hintText: '输入关键词（如 NVIDIA）',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _subscribeKeyword,
                  child: const Text('订阅'),
                ),
              ],
            ),
            const SizedBox(height: 20),
            const Text('话题列表', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (topicState.isLoading) const LinearProgressIndicator(),
            if (topicState.error != null) Text('话题加载失败: ${topicState.error}'),
            ...topicState.items.map(
              (t) => Card(
                child: ListTile(
                  title: Text(t.name),
                  subtitle: Text('${t.category ?? 'uncategorized'} · 订阅数 ${t.subscriberCount}'),
                  trailing: t.isSubscribed
                      ? const Chip(label: Text('已订阅'))
                      : ElevatedButton(
                          onPressed: () async {
                            await ref.read(mySubscriptionsNotifierProvider.notifier).subscribeTopic(t.id);
                            await ref.read(topicsNotifierProvider.notifier).loadFirstPage(
                                  category: topicState.category,
                                  query: topicState.query,
                                );
                            await ref.read(mySubscriptionsNotifierProvider.notifier).refresh();
                          },
                          child: const Text('订阅'),
                        ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text('我的订阅', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (myState.isLoading) const LinearProgressIndicator(),
            if (myState.error != null) Text('订阅加载失败: ${myState.error}'),
            ...myState.items.map(
              (s) => Card(
                child: ListTile(
                  title: Text(s.topic.name),
                  subtitle: Text('priority=${s.priority} · push=${s.pushEnabled}'),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () async {
                      await ref.read(mySubscriptionsNotifierProvider.notifier).unsubscribe(s.topic.id);
                      await ref.read(topicsNotifierProvider.notifier).loadFirstPage(
                            category: topicState.category,
                            query: topicState.query,
                          );
                    },
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

## 2) `feed_page.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/feed_providers.dart';

class FeedPage extends ConsumerStatefulWidget {
  const FeedPage({super.key});

  @override
  ConsumerState<FeedPage> createState() => _FeedPageState();
}

class _FeedPageState extends ConsumerState<FeedPage> {
  final _controller = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(feedNotifierProvider.notifier).refresh();
    });
    _controller.addListener(_onScroll);
  }

  void _onScroll() {
    if (!_controller.hasClients) return;
    final max = _controller.position.maxScrollExtent;
    final cur = _controller.position.pixels;
    if (cur > max - 200) {
      ref.read(feedNotifierProvider.notifier).loadMore();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(feedNotifierProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('信息流')),
      body: RefreshIndicator(
        onRefresh: () => ref.read(feedNotifierProvider.notifier).refresh(),
        child: ListView.builder(
          controller: _controller,
          padding: const EdgeInsets.all(12),
          itemCount: state.items.length + 1,
          itemBuilder: (context, index) {
            if (index == state.items.length) {
              if (state.isLoadingMore) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (!state.hasMore) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(child: Text('没有更多了')),
                );
              }
              return const SizedBox.shrink();
            }
            final a = state.items[index];
            return Card(
              child: ListTile(
                title: Text(a.title),
                subtitle: Text(a.summary ?? a.excerpt ?? 'No summary'),
              ),
            );
          },
        ),
      ),
    );
  }
}
```

## 3) `main.dart` (Two Tabs)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'features/feed/presentation/pages/feed_page.dart';
import 'features/subscription/presentation/pages/subscription_page.dart';

void main() {
  runApp(const ProviderScope(child: NewsFlowApp()));
}

class NewsFlowApp extends StatelessWidget {
  const NewsFlowApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NewsFlow',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo),
      home: const _HomeShell(),
    );
  }
}

class _HomeShell extends StatefulWidget {
  const _HomeShell();

  @override
  State<_HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<_HomeShell> {
  int _index = 0;
  final _pages = const [SubscriptionPage(), FeedPage()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.subscriptions_outlined), label: '订阅'),
          NavigationDestination(icon: Icon(Icons.article_outlined), label: '信息流'),
        ],
      ),
    );
  }
}
```

## 4) Suggested Provider Names (Alignment)

为避免拷贝后变量名对不上，建议你在 provider 文件里使用这些导出名：

- `topicCategoriesProvider`
- `topicsNotifierProvider`
- `mySubscriptionsNotifierProvider`
- `feedNotifierProvider`

## 5) Quick Run Checklist

- [ ] 先确保 `ApiClient` 的 `baseUrl` 可连通后端（模拟器注意 `10.0.2.2`）。
- [ ] 先让 `x-user-id` 方案跑通（开发态），再替换成 Bearer token。
- [ ] 首次运行若为空，先从后端插入少量 topic 测试数据。
- [ ] 出现 `401` 时优先检查 interceptor 是否注入了鉴权头。
