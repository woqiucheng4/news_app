import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../l10n/app_localizations.dart';
import '../../../feed/domain/models/feed_item.dart';
import '../../../feed/presentation/providers/feed_data_providers.dart';
import '../../../feed/presentation/widgets/feed_article_card.dart';
import '../providers/article_search_notifier.dart';

class SearchResultsArticles extends ConsumerStatefulWidget {
  const SearchResultsArticles({super.key});

  @override
  ConsumerState<SearchResultsArticles> createState() =>
      _SearchResultsArticlesState();
}

class _SearchResultsArticlesState extends ConsumerState<SearchResultsArticles> {
  String? _openingArticleId;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final results = ref.watch(articleSearchNotifierProvider);

    return results.when(
      data: (articles) {
        if (articles.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                l10n.globalSearchArticlesEmpty,
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.only(top: 8, bottom: 24),
          itemCount: articles.length,
          itemBuilder: (context, index) {
            final item = articles[index];
            return FeedArticleCard(
              item: item,
              isOpening: _openingArticleId == item.id,
              onTap: () => _openArticle(context, item),
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                l10n.globalSearchFailed,
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                '$error',
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () {
                  ref.invalidate(articleSearchNotifierProvider);
                },
                child: Text(l10n.retryAction),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _openArticle(BuildContext context, FeedItem item) async {
    setState(() => _openingArticleId = item.id);

    try {
      ref.read(appAnalyticsProvider).trackFeedArticleOpen(
            articleId: item.id,
            source: 'search',
          );
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
