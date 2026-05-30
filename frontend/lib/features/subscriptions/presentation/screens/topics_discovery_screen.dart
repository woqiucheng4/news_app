import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../l10n/app_localizations.dart';
import '../providers/recent_searches_provider.dart';
import '../providers/topics_discovery_notifier.dart';
import '../utils/subscription_error_mapper.dart';

class TopicsDiscoveryScreen extends ConsumerStatefulWidget {
  const TopicsDiscoveryScreen({super.key});

  @override
  ConsumerState<TopicsDiscoveryScreen> createState() => _TopicsDiscoveryScreenState();
}

class _TopicsDiscoveryScreenState extends ConsumerState<TopicsDiscoveryScreen> {
  late final TextEditingController _searchController;
  late final TextEditingController _keywordController;
  late final ScrollController _scrollController;
  Timer? _searchDebounceTimer;
  bool _didHydrateFromUrl = false;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController(
      text: ref.read(topicQueryProvider),
    );
    _keywordController = TextEditingController();
    _scrollController = ScrollController(
      initialScrollOffset: ref.read(topicDiscoveryScrollOffsetProvider),
    );
    _scrollController.addListener(() {
      ref.read(topicDiscoveryScrollOffsetProvider.notifier).state = _scrollController.offset;
    });
  }

  @override
  void dispose() {
    _searchDebounceTimer?.cancel();
    _searchController.dispose();
    _keywordController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_didHydrateFromUrl) return;

    _didHydrateFromUrl = true;
    final uri = GoRouterState.of(context).uri;
    Future.microtask(() {
      if (!mounted) return;
      ref.read(topicsDiscoveryNotifierProvider.notifier).hydrateFromUrl(
            query: uri.queryParameters['q'],
            category: uri.queryParameters['category'],
          );
    });
  }

  void _onSearchChanged(String value) {
    _searchDebounceTimer?.cancel();
    _searchDebounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      _submitSearch(value, source: 'debounce');
    });
  }

  Future<void> _submitSearch(
    String value, {
    required String source,
  }) async {
    final query = value.trim();
    await ref.read(topicsDiscoveryNotifierProvider.notifier).search(query);

    if (query.isNotEmpty) {
      await ref.read(recentSearchesProvider.notifier).addSearch(query);
    }

    ref.read(discoveryAnalyticsProvider).trackSearchSubmitted(
          query: query,
          source: source,
          category: ref.read(selectedTopicCategoryProvider),
        );
  }

  Future<void> _clearFilters() async {
    _searchDebounceTimer?.cancel();
    _searchController.clear();
    await ref
        .read(topicsDiscoveryNotifierProvider.notifier)
        .hydrateFromUrl(query: '', category: null);
  }

  void _showMessage(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  void _syncUrlWithState({
    required String query,
    required String? category,
  }) {
    if (!mounted) return;

    final nextQuery = query.trim();
    final nextCategory = (category ?? '').trim();
    final currentUri = GoRouterState.of(context).uri;
    final currentQuery = (currentUri.queryParameters['q'] ?? '').trim();
    final currentCategory = (currentUri.queryParameters['category'] ?? '').trim();
    if (nextQuery == currentQuery && nextCategory == currentCategory) {
      return;
    }

    final params = <String, String>{};
    if (nextQuery.isNotEmpty) params['q'] = nextQuery;
    if (nextCategory.isNotEmpty) params['category'] = nextCategory;
    final nextUri = Uri(
      path: '/subscriptions/discover',
      queryParameters: params.isEmpty ? null : params,
    );
    context.go(nextUri.toString());
  }

  Future<void> _showKeywordSubscribeDialog() async {
    final l10n = AppLocalizations.of(context)!;
    _keywordController.clear();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(l10n.keywordDialogTitle),
          content: TextField(
            controller: _keywordController,
            autofocus: true,
            decoration: InputDecoration(
              hintText: l10n.keywordInputHint,
            ),
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => Navigator.of(context).pop(true),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text(MaterialLocalizations.of(context).cancelButtonLabel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: Text(MaterialLocalizations.of(context).okButtonLabel),
            ),
          ],
        );
      },
    );

    if (confirmed != true) return;

    final keyword = _keywordController.text.trim();
    if (keyword.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.keywordEmptyValidation)),
      );
      return;
    }

    final result =
        await ref.read(topicsDiscoveryNotifierProvider.notifier).subscribeKeyword(keyword);
    if (!mounted) return;
    if (result.success) {
      _searchController.text = keyword;
    }
    _showMessage(
      result.success
          ? l10n.keywordSubscribeSuccess
          : '${l10n.keywordSubscribeFailed}: ${mapSubscriptionError(result.error ?? Exception(), l10n)}',
    );
    ref.read(discoveryAnalyticsProvider).trackKeywordSubscribe(
          keyword: keyword,
          success: result.success,
        );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    ref.listen<String>(topicQueryProvider, (_, next) {
      if (_searchController.text != next) {
        _searchController.text = next;
        _searchController.selection = TextSelection.collapsed(offset: next.length);
      }
      _syncUrlWithState(
        query: next,
        category: ref.read(selectedTopicCategoryProvider),
      );
    });
    ref.listen<String?>(selectedTopicCategoryProvider, (_, next) {
      _syncUrlWithState(
        query: ref.read(topicQueryProvider),
        category: next,
      );
    });

    final topicsState = ref.watch(topicsDiscoveryNotifierProvider);
    final categoriesState = ref.watch(topicCategoriesProvider);
    final recentSearchesState = ref.watch(recentSearchesProvider);
    final selectedCategory = ref.watch(selectedTopicCategoryProvider);
    final query = ref.watch(topicQueryProvider);
    final hasMore = ref.watch(topicsHasMoreProvider);
    final loadingMore = ref.watch(topicsLoadingMoreProvider);
    final loadMoreError = ref.watch(topicsLoadMoreErrorProvider);
    final highlightedTopicId = ref.watch(highlightedTopicIdProvider);
    final actionLoadingIds = ref.watch(topicActionLoadingIdsProvider);
    final keywordSubscribing = ref.watch(keywordSubscribingProvider);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: l10n.topicSearchHint,
                    prefixIcon: const Icon(Icons.search),
                  ),
                  textInputAction: TextInputAction.search,
                  onChanged: _onSearchChanged,
                  onSubmitted: (value) {
                    _submitSearch(value, source: 'submit');
                  },
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                onPressed: () {
                  _submitSearch(_searchController.text, source: 'button');
                },
                child: const Icon(Icons.search),
              ),
              const SizedBox(width: 8),
              TextButton(
                onPressed: (query.isEmpty && selectedCategory == null) ? null : _clearFilters,
                child: Text(l10n.clearFiltersAction),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: categoriesState.when(
                  data: (categories) {
                    return SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          FilterChip(
                            selected: selectedCategory == null,
                            label: Text(l10n.allCategoriesAction),
                            onSelected: (_) {
                              ref
                                  .read(topicsDiscoveryNotifierProvider.notifier)
                                  .setCategory(null);
                              ref.read(discoveryAnalyticsProvider).trackCategorySelected(
                                    category: 'all',
                                    source: 'chip',
                                  );
                            },
                          ),
                          const SizedBox(width: 8),
                          for (final category in categories) ...[
                            FilterChip(
                              selected: selectedCategory == category.name,
                              label: Text(category.name),
                              onSelected: (_) {
                                ref
                                    .read(topicsDiscoveryNotifierProvider.notifier)
                                    .setCategory(category.name);
                                ref.read(discoveryAnalyticsProvider).trackCategorySelected(
                                      category: category.name,
                                      source: 'chip',
                                    );
                              },
                            ),
                            const SizedBox(width: 8),
                          ],
                        ],
                      ),
                    );
                  },
                  loading: () => const SizedBox(height: 32),
                  error: (_, __) => const SizedBox.shrink(),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton.tonalIcon(
                onPressed: keywordSubscribing ? null : _showKeywordSubscribeDialog,
                icon: const Icon(Icons.add),
                label: Text(l10n.keywordSubscribeAction),
              ),
            ],
          ),
        ),
        if (query.isEmpty)
          recentSearchesState.when(
            data: (history) {
              if (history.isEmpty) return const SizedBox.shrink();
              return Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            l10n.recentSearchesTitle,
                            style: Theme.of(context).textTheme.titleSmall,
                          ),
                        ),
                        TextButton(
                          onPressed: () {
                            ref.read(discoveryAnalyticsProvider).trackRecentSearchesCleared(
                                  previousCount: history.length,
                                );
                            ref.read(recentSearchesProvider.notifier).clearAll();
                          },
                          child: Text(l10n.clearRecentSearchesAction),
                        ),
                      ],
                    ),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final item in history)
                          InputChip(
                            label: Text(item),
                            onPressed: () {
                              _searchController.text = item;
                              _submitSearch(item, source: 'history');
                            },
                            onDeleted: () {
                              ref
                                  .read(recentSearchesProvider.notifier)
                                  .removeSearch(item);
                              ref.read(discoveryAnalyticsProvider).trackRecentSearchDeleted(
                                    query: item,
                                  );
                            },
                            deleteButtonTooltipMessage: l10n.removeRecentSearchAction,
                          ),
                      ],
                    ),
                  ],
                ),
              );
            },
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: () => ref
                .read(topicsDiscoveryNotifierProvider.notifier)
                .refresh(forceNetwork: true),
            child: topicsState.when(
              data: (items) {
                final shouldShowHotCategories = query.isEmpty && selectedCategory == null;
                final sortedCategories = categoriesState.maybeWhen(
                  data: (categories) {
                    final cloned = [...categories];
                    cloned.sort((a, b) => b.topicCount.compareTo(a.topicCount));
                    return cloned.take(6).toList(growable: false);
                  },
                  orElse: () => const [],
                );

                if (items.isEmpty) {
                  return ListView(
                    controller: _scrollController,
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      if (shouldShowHotCategories && sortedCategories.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                l10n.hotCategoriesTitle,
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                              const SizedBox(height: 10),
                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: [
                                  for (final category in sortedCategories)
                                    ActionChip(
                                      label: Text('${category.name} (${category.topicCount})'),
                                      onPressed: () {
                                        ref
                                            .read(topicsDiscoveryNotifierProvider.notifier)
                                            .setCategory(category.name);
                                        ref
                                            .read(discoveryAnalyticsProvider)
                                            .trackCategorySelected(
                                              category: category.name,
                                              source: 'hot-shortcut',
                                            );
                                      },
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      SizedBox(
                        height: MediaQuery.of(context).size.height * 0.45,
                        child: Center(
                          child: Text(
                            shouldShowHotCategories
                                ? l10n.noTopicsFound
                                : l10n.noTopicsMatchFilters,
                          ),
                        ),
                      ),
                    ],
                  );
                }

                return NotificationListener<ScrollNotification>(
                  onNotification: (notification) {
                    if (notification.metrics.pixels >
                        notification.metrics.maxScrollExtent - 240) {
                      ref.read(topicsDiscoveryNotifierProvider.notifier).loadMore();
                    }
                    return false;
                  },
                  child: ListView.separated(
                    controller: _scrollController,
                    physics: const AlwaysScrollableScrollPhysics(),
                    itemCount: items.length + (hasMore ? 1 : 0),
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      if (index >= items.length) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Center(
                            child: loadingMore
                                ? const CircularProgressIndicator()
                                : loadMoreError != null
                                    ? Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Text(
                                            mapSubscriptionError(loadMoreError, l10n),
                                            style: Theme.of(context).textTheme.bodySmall,
                                          ),
                                          const SizedBox(height: 6),
                                          TextButton(
                                            onPressed: () {
                                              ref
                                                  .read(topicsDiscoveryNotifierProvider.notifier)
                                                  .loadMore();
                                            },
                                            child: Text(l10n.retryAction),
                                          ),
                                        ],
                                      )
                                    : TextButton(
                                        onPressed: () {
                                          ref
                                              .read(topicsDiscoveryNotifierProvider.notifier)
                                              .loadMore();
                                        },
                                        child: Text(l10n.loadMoreAction),
                                      ),
                          ),
                        );
                      }

                      final topic = items[index];
                      final isSubscribed = topic.isSubscribed;
                      final isHighlighted = highlightedTopicId == topic.id;
                      final isActionLoading = actionLoadingIds.contains(topic.id);

                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 220),
                        color: isHighlighted
                            ? Theme.of(context).colorScheme.primaryContainer.withOpacity(0.35)
                            : Colors.transparent,
                        child: ListTile(
                          title: Text(topic.name),
                          subtitle: Text(topic.category ?? ''),
                          trailing: FilledButton.tonal(
                            onPressed: isSubscribed || isActionLoading
                                ? null
                                : () async {
                                    final result = await ref
                                        .read(topicsDiscoveryNotifierProvider.notifier)
                                        .subscribeTopic(topic.id);
                                    if (!mounted) return;
                                    _showMessage(
                                      result.success
                                          ? l10n.subscribeSuccess
                                          : '${l10n.subscribeFailed}: ${mapSubscriptionError(result.error ?? Exception(), l10n)}',
                                    );
                                    ref.read(discoveryAnalyticsProvider).trackTopicSubscribe(
                                          topicId: topic.id,
                                          success: result.success,
                                        );
                                  },
                            child: isActionLoading
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : Text(
                                    isSubscribed ? l10n.subscribedAction : l10n.subscribeAction,
                                  ),
                          ),
                        ),
                      );
                    },
                  ),
                );
              },
              error: (error, _) {
                return ListView(
                  controller: _scrollController,
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: [
                    SizedBox(
                      height: MediaQuery.of(context).size.height * 0.7,
                      child: Center(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 24),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                '${l10n.loadFailed}: ${mapSubscriptionError(error, l10n)}',
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 16),
                              FilledButton(
                                onPressed: () {
                                  ref
                                      .read(topicsDiscoveryNotifierProvider.notifier)
                                      .refresh(forceNetwork: true);
                                },
                                child: Text(l10n.retryAction),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              },
              loading: () => ListView.separated(
                controller: _scrollController,
                physics: const AlwaysScrollableScrollPhysics(),
                itemCount: 8,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (_, __) => const _TopicSkeletonTile(),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _TopicSkeletonTile extends StatelessWidget {
  const _TopicSkeletonTile();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SkeletonBlock(width: 180, height: 14),
                SizedBox(height: 8),
                _SkeletonBlock(width: 110, height: 12),
              ],
            ),
          ),
          SizedBox(width: 12),
          _SkeletonBlock(width: 88, height: 32),
        ],
      ),
    );
  }
}

class _SkeletonBlock extends StatelessWidget {
  const _SkeletonBlock({
    required this.width,
    required this.height,
  });

  final double width;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
    );
  }
}
