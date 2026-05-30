import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/auth/auth_token_provider.dart';
import '../../../../core/analytics/analytics_providers.dart';
import '../../../../core/network/dio_error_utils.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import '../providers/feed_data_providers.dart';
import '../providers/feed_notifier.dart';
import '../widgets/feed_article_card.dart';
import '../widgets/feed_cache_banner.dart';
import '../widgets/feed_list_skeleton.dart';
import '../widgets/feed_login_required.dart';
import '../widgets/feed_sign_in_banner.dart';

class FeedScreen extends ConsumerStatefulWidget {
  const FeedScreen({super.key});

  @override
  ConsumerState<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends ConsumerState<FeedScreen> {
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

    final hasMore = ref.read(feedHasMoreProvider);
    final isLoadingMore = ref.read(feedLoadingMoreProvider);
    if (!hasMore || isLoadingMore) {
      return;
    }

    ref.read(feedNotifierProvider.notifier).loadMore();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final hasToken = ref.watch(accessTokenValueProvider).trim().isNotEmpty;
    final feedState = ref.watch(feedNotifierProvider);
    final hasMore = ref.watch(feedHasMoreProvider);
    final isLoadingMore = ref.watch(feedLoadingMoreProvider);
    final loadMoreError = ref.watch(feedLoadMoreErrorProvider);
    final showCached = ref.watch(feedFromCacheProvider);
    final showOffline = ref.watch(feedOfflineFallbackProvider);

    return RefreshIndicator(
      onRefresh: () => ref.read(feedNotifierProvider.notifier).reload(),
      child: feedState.when(
        data: (items) {
          if (items.isEmpty) {
            if (!hasToken) {
              return const FeedLoginRequired();
            }

            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                SizedBox(
                  height: MediaQuery.of(context).size.height * 0.7,
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            l10n.feedHeadline,
                            style: Theme.of(context).textTheme.headlineSmall,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            l10n.feedEmptyDescription,
                            style: Theme.of(context).textTheme.bodyMedium,
                            textAlign: TextAlign.center,
                          ),
                        ],
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
            itemCount: (hasToken ? 0 : 1) + (showCached || showOffline ? 1 : 0) + items.length + 1,
            itemBuilder: (context, index) {
              var cursor = 0;

              if (!hasToken) {
                if (index == cursor++) {
                  return const FeedSignInBanner();
                }
              }

              if (showCached || showOffline) {
                if (index == cursor++) {
                  return FeedCacheBanner(
                    showCached: showCached,
                    showOffline: showOffline,
                  );
                }
              }

              final contentIndex = index - cursor;

              if (contentIndex == items.length) {
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
                            ref.read(feedNotifierProvider.notifier).loadMore();
                          },
                          child: Text(l10n.retryAction),
                        ),
                      ],
                    ),
                  );
                }

                return const SizedBox(height: 8);
              }

              final item = items[contentIndex];

              return FeedArticleCard(
                item: item,
                isOpening: _openingArticleId == item.id,
                onTap: () {
                  ref.read(appAnalyticsProvider).trackFeedArticleOpen(
                        articleId: item.id,
                        source: 'feed_list',
                      );
                  unawaited(_openArticleDetail(context, ref, item));
                },
              );
            },
          );
        },
        error: (error, _) {
          if (!hasToken && isUnauthorizedError(error)) {
            return const FeedLoginRequired();
          }

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.7,
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
                            ref.invalidate(feedNotifierProvider);
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

  Future<void> _openArticleDetail(
    BuildContext context,
    WidgetRef ref,
    FeedItem item,
  ) async {
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
