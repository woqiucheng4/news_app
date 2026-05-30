import 'package:flutter/material.dart';

import '../../../../core/utils/published_at_formatter.dart';
import '../../../../core/utils/source_favicon_url.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import 'source_favicon.dart';

class RelatedArticleTile extends StatelessWidget {
  const RelatedArticleTile({
    super.key,
    required this.item,
    required this.onTap,
    this.compact = false,
  });

  final FeedItem item;
  final VoidCallback onTap;
  final bool compact;

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
    final metaLabel = [
      sourceLabel,
      if (publishedLabel.isNotEmpty) publishedLabel,
    ].join(' · ');

    return Card(
      margin: compact ? EdgeInsets.zero : const EdgeInsets.only(bottom: 8),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: EdgeInsets.all(compact ? 12 : 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment:
                compact ? MainAxisAlignment.spaceBetween : MainAxisAlignment.start,
            children: [
              Text(
                item.title,
                maxLines: compact ? 2 : null,
                overflow: compact ? TextOverflow.ellipsis : null,
                style: Theme.of(context).textTheme.titleSmall,
              ),
              if (metaLabel.isNotEmpty) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    SourceFavicon(faviconUrl: faviconUrl, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        metaLabel,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant,
                            ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
