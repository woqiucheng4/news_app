import 'package:flutter/material.dart';

import '../../../../core/utils/published_at_formatter.dart';
import '../../../../core/utils/source_favicon_url.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import 'article_hero.dart';

class FeedArticleCard extends StatelessWidget {
  const FeedArticleCard({
    super.key,
    required this.item,
    required this.onTap,
    this.isOpening = false,
  });

  final FeedItem item;
  final VoidCallback onTap;
  final bool isOpening;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final localeName = Localizations.localeOf(context).toLanguageTag();
    final publishedLabel = formatPublishedAt(
      raw: item.publishedAt,
      l10n: l10n,
      localeName: localeName,
    );
    final sourceLabel = item.sourceName.isNotEmpty
        ? item.sourceName
        : l10n.feedSourceUnknown;
    final faviconUrl = resolveSourceFaviconUrl(
      sourceSiteUrl: item.source?.url,
      articleUrl: item.sourceUrl,
    );

    final sourceMetaLabel = [
      sourceLabel,
      if (publishedLabel.isNotEmpty) publishedLabel,
    ].join(' · ');
    final metaStyle = Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        );

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: isOpening ? null : onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AnimatedOpacity(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              opacity: isOpening ? 0.72 : 1,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (item.category != null && item.category!.trim().isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: ArticleCategoryHero(
                            articleId: item.id,
                            category: item.category!.trim(),
                          ),
                        ),
                      ),
                    ArticleTitleHero(
                      articleId: item.id,
                      title: item.title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    if (sourceMetaLabel.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      ArticleSourceMetaHero(
                        articleId: item.id,
                        faviconUrl: faviconUrl,
                        label: sourceMetaLabel,
                        style: metaStyle,
                      ),
                    ],
                    if (item.summary.trim().isNotEmpty) ...[
                      const SizedBox(height: 12),
                      ArticleSummaryHero(
                        articleId: item.id,
                        summary: item.summary,
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ],
                ),
              ),
            ),
            AnimatedSize(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              alignment: Alignment.topCenter,
              child: isOpening
                  ? const LinearProgressIndicator(minHeight: 2)
                  : const SizedBox(width: double.infinity, height: 0),
            ),
          ],
        ),
      ),
    );
  }
}
