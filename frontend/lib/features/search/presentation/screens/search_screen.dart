import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../l10n/app_localizations.dart';
import '../../../feed/presentation/providers/feed_data_providers.dart';
import '../../../subscriptions/presentation/providers/recent_searches_provider.dart';
import '../providers/article_search_notifier.dart';
import '../providers/search_page_topics_notifier.dart';
import '../widgets/search_results_articles.dart';
import '../widgets/search_results_topics.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen>
    with SingleTickerProviderStateMixin {
  late final TextEditingController _controller;
  late final TabController _tabController;
  Timer? _analyticsDebounce;
  bool _didHydrateFromUrl = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_didHydrateFromUrl) {
      return;
    }
    _didHydrateFromUrl = true;

    final initialQuery = GoRouterState.of(context).uri.queryParameters['q'];
    if (initialQuery != null && initialQuery.trim().isNotEmpty) {
      _controller.text = initialQuery.trim();
      _dispatchQuery(initialQuery.trim(), source: 'deep_link');
    }
  }

  @override
  void dispose() {
    _analyticsDebounce?.cancel();
    _controller.dispose();
    _tabController.dispose();
    super.dispose();
  }

  void _onQueryChanged(String value) {
    ref.read(articleSearchNotifierProvider.notifier).onQueryChanged(value);
    ref.read(searchPageTopicsNotifierProvider.notifier).onQueryChanged(value);

    _analyticsDebounce?.cancel();
    final trimmed = value.trim();
    if (trimmed.isEmpty) {
      return;
    }

    _analyticsDebounce = Timer(const Duration(milliseconds: 350), () {
      _trackSearch(trimmed, source: 'global_search');
    });
  }

  void _dispatchQuery(String value, {required String source}) {
    _onQueryChanged(value);
    if (value.trim().isNotEmpty) {
      _trackSearch(value.trim(), source: source);
    }
  }

  void _trackSearch(String query, {required String source}) {
    ref.read(discoveryAnalyticsProvider).trackSearchSubmitted(
          query: query,
          source: source,
          category: null,
        );
    unawaited(ref.read(recentSearchesProvider.notifier).addSearch(query));
  }

  void _clearQuery() {
    _controller.clear();
    _onQueryChanged('');
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: _controller,
          autofocus: true,
          decoration: InputDecoration(
            hintText: l10n.globalSearchHint,
            border: InputBorder.none,
          ),
          onChanged: (value) {
            _onQueryChanged(value);
            setState(() {});
          },
          onSubmitted: (value) => _dispatchQuery(value, source: 'submit'),
          textInputAction: TextInputAction.search,
        ),
        actions: [
          if (_controller.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear),
              tooltip: l10n.clearFiltersAction,
              onPressed: _clearQuery,
            ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: l10n.globalSearchArticlesTab),
            Tab(text: l10n.globalSearchTopicsTab),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          SearchResultsArticles(),
          SearchResultsTopics(),
        ],
      ),
    );
  }
}
