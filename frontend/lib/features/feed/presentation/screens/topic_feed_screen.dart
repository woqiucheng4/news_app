import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import '../providers/feed_data_providers.dart';
import '../providers/topic_feed_notifier.dart';
import '../widgets/feed_article_card.dart';
import '../widgets/feed_list_skeleton.dart';

class TopicFeedScreen extends StatelessWidget {
  const TopicFeedScreen({
    super.key,
    required this.topicId,
    required this.topicName,
  });

  final String topicId;
  final String topicName;

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      overrides: [
        topicFeedScopeProvider.overrideWithValue(TopicFeedScope(topicId)),
      ],
      child: _TopicFeedContent(topicName: topicName),
    );
  }
}

class _TopicFeedContent extends ConsumerStatefulWidget {
  const _TopicFeedContent({required this.topicName});

  final String topicName;

  @override
  ConsumerState<_TopicFeedContent> createState() => _TopicFeedContentState();
}

class _TopicFeedContentState extends ConsumerState<_TopicFeedContent> {
  late final ScrollController _scrollController;
  String? _openingArticleId;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController()..addListener(_handleScroll);
  }

  @override
  void dispose() {
    _scrollController
      ..removeListener(_handleScroll)
      ..dispose();
    super.dispose();
  }

  void _handleScroll() {
    if (!_scrollController.hasClients) {
      return;
    }

    final position = _scrollController.position;
    if (position.maxScrollExtent - position.pixels > 240) {
      return;
    }

    final hasMore = ref.read(topicFeedHasMoreProvider);
    final isLoadingMore = ref.read(topicFeedLoadingMoreProvider);
    if (!hasMore || isLoadingMore) {
      return;
    }

    ref.read(topicFeedNotifierProvider.notifier).loadMore();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final feedState = ref.watch(topicFeedNotifierProvider);
    final hasMore = ref.watch(topicFeedHasMoreProvider);
    final isLoadingMore = ref.watch(topicFeedLoadingMoreProvider);
    final loadMoreError = ref.watch(topicFeedLoadMoreErrorProvider);

    return RefreshIndicator(
      onRefresh: () => ref.read(topicFeedNotifierProvider.notifier).reload(),
      child: feedState.when(
        data: (items) {
          if (items.isEmpty) {
            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                SizedBox(
                  height: MediaQuery.of(context).size.height * 0.65,
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                        l10n.topicFeedEmpty(widget.topicName),
                        style: Theme.of(context).textTheme.bodyLarge,
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
                ),
              ],
            );
          }

          return ListView.builder(
            controller: _scrollController,
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.only(top: 8, bottom: 24),
            itemCount: items.length + 1,
            itemBuilder: (context, index) {
              if (index == items.length) {
                if (!hasMore) {
                  return const SizedBox(height: 8);
                }

                if (isLoadingMore) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Center(
                      child: SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                  );
                }

                if (loadMoreError != null) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                    child: Column(
                      children: [
                        Text(
                          l10n.feedLoadMoreFailed,
                          style: Theme.of(context).textTheme.bodySmall,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        TextButton(
                          onPressed: () {
                            ref.read(topicFeedNotifierProvider.notifier).loadMore();
                          },
                          child: Text(l10n.retryAction),
                        ),
                      ],
                    ),
                  );
                }

                return const SizedBox(height: 8);
              }

              final item = items[index];
              return FeedArticleCard(
                item: item,
                isOpening: _openingArticleId == item.id,
                onTap: () {
                  ref.read(appAnalyticsProvider).trackFeedArticleOpen(
                        articleId: item.id,
                        source: 'topic_feed',
                      );
                  unawaited(_openArticleDetail(context, item));
                },
              );
            },
          );
        },
        error: (error, _) {
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.65,
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '$error',
                          style: Theme.of(context).textTheme.bodyMedium,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        FilledButton(
                          onPressed: () {
                            ref.invalidate(topicFeedNotifierProvider);
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
        loading: () => const FeedListSkeleton(),
      ),
    );
  }

  Future<void> _openArticleDetail(BuildContext context, FeedItem item) async {
    setState(() => _openingArticleId = item.id);

    try {
      await ref
          .read(articleDetailRepositoryProvider)
          .cachePreviewFromFeedItem(item);
      if (!context.mounted) {
        return;
      }
      await context.push('/feed/article/${item.id}');
    } finally {
      if (mounted) {
        setState(() => _openingArticleId = null);
      }
    }
  }
}
