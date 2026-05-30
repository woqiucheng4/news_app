import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../core/utils/external_url_launcher.dart';
import '../../../../core/utils/published_at_formatter.dart';
import '../../../../core/utils/source_favicon_url.dart';
import '../../../../l10n/app_localizations.dart';
import '../../../../shared/widgets/skeleton_line.dart';
import '../../../../shared/widgets/skeleton_pulse.dart';
import '../../domain/models/feed_item.dart';
import '../providers/article_detail_provider.dart';
import '../providers/feed_data_providers.dart';
import '../utils/article_source_label.dart';
import '../widgets/article_detail_preview_extras.dart';
import '../widgets/article_detail_skeleton.dart';
import '../widgets/article_hero.dart';
import '../widgets/feed_cache_banner.dart';
import '../widgets/related_articles_section.dart';
import '../widgets/related_articles_sheet.dart';

class ArticleDetailScreen extends ConsumerWidget {
  const ArticleDetailScreen({
    super.key,
    required this.articleId,
  });

  final String articleId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final articleState = ref.watch(articleDetailProvider(articleId));

    return articleState.when(
      loading: () => Column(
        children: [
          SafeArea(
            bottom: false,
            child: Align(
              alignment: Alignment.centerLeft,
              child: BackButton(onPressed: () => context.pop()),
            ),
          ),
          const Expanded(child: ArticleDetailSkeleton()),
        ],
      ),
      skipLoadingOnRefresh: true,
      skipLoadingOnReload: true,
      error: (error, _) => Column(
        children: [
          SafeArea(
            bottom: false,
            child: Align(
              alignment: Alignment.centerLeft,
              child: BackButton(onPressed: () => context.pop()),
            ),
          ),
          Expanded(
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('$error', textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: () {
                        ref
                            .read(articleDetailProvider(articleId).notifier)
                            .refreshFromNetwork();
                      },
                      child: Text(l10n.retryAction),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
      data: (viewData) {
        final article = viewData.article;
        final localeName = Localizations.localeOf(context).toLanguageTag();
        final publishedLabel = formatPublishedAt(
          raw: article.publishedAt,
          l10n: l10n,
          localeName: localeName,
        );
        final sourceLabel = resolveArticleSourceLabel(article, l10n);
        final faviconUrl = resolveSourceFaviconUrl(
          sourceSiteUrl: article.source?.url,
          articleUrl: article.url,
        );
        final sourceMetaLabel = [
          sourceLabel,
          if (publishedLabel.isNotEmpty) publishedLabel,
        ].join(' · ');
        final metaStyle = Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            );

        return RefreshIndicator(
          onRefresh: () => ref
              .read(articleDetailProvider(articleId).notifier)
              .refreshFromNetwork(),
          child: SkeletonPulse(
            child: CustomScrollView(
              physics: const AlwaysScrollableScrollPhysics(
                parent: BouncingScrollPhysics(),
              ),
              slivers: [
                if (viewData.showPreview ||
                    viewData.showCached ||
                    viewData.showOffline)
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                      child: FeedCacheBanner(
                        showPreview: viewData.showPreview,
                        showCached: viewData.showCached,
                        showOffline: viewData.showOffline,
                        margin: EdgeInsets.zero,
                      ),
                    ),
                  ),
                if (article.category != null && article.category!.isNotEmpty)
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                      child: ArticleCategoryHero(
                        articleId: article.id,
                        category: article.category!,
                      ),
                    ),
                  ),
                SliverAppBar(
                  pinned: true,
                  stretch: true,
                  leading: BackButton(onPressed: () => context.pop()),
                  expandedHeight: 132,
                  flexibleSpace: FlexibleSpaceBar(
                    stretchModes: const [
                      StretchMode.zoomBackground,
                      StretchMode.blurBackground,
                    ],
                    titlePadding: const EdgeInsetsDirectional.only(
                      start: 56,
                      end: 16,
                      bottom: 16,
                    ),
                    centerTitle: false,
                    title: Text(
                      article.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    background: SafeArea(
                      bottom: false,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 56, 16, 16),
                        child: Align(
                          alignment: Alignment.bottomLeft,
                          child: ArticleTitleHero(
                            articleId: article.id,
                            title: article.title,
                            style: Theme.of(context).textTheme.headlineSmall,
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                  sliver: SliverList(
                    delegate: SliverChildListDelegate([
                      if (sourceMetaLabel.isNotEmpty)
                        ArticleSourceMetaHero(
                          articleId: article.id,
                          faviconUrl: faviconUrl,
                          label: sourceMetaLabel,
                          style: metaStyle,
                        ),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 220),
                        switchInCurve: Curves.easeOut,
                        switchOutCurve: Curves.easeIn,
                        child: article.author != null && article.author!.isNotEmpty
                            ? Padding(
                                key: ValueKey('author-${article.author}'),
                                padding: const EdgeInsets.only(top: 8),
                                child: Text(
                                  article.author!,
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              )
                            : viewData.showPreview
                                ? const Padding(
                                    key: ValueKey('author-skeleton'),
                                    padding: EdgeInsets.only(top: 8),
                                    child: SkeletonLine(width: 140, height: 12),
                                  )
                                : const SizedBox.shrink(
                                    key: ValueKey('author-empty'),
                                  ),
                      ),
                      const SizedBox(height: 16),
                      if (article.displaySummary.isNotEmpty)
                        AnimatedSize(
                          duration: const Duration(milliseconds: 240),
                          curve: Curves.easeOut,
                          alignment: Alignment.topCenter,
                          child: viewData.showPreview
                              ? ArticleSummaryHero(
                                  key: ValueKey(
                                    'summary-hero-${article.displaySummary}',
                                  ),
                                  articleId: article.id,
                                  summary: article.displaySummary,
                                  style: Theme.of(context).textTheme.bodyLarge,
                                )
                              : AnimatedSwitcher(
                                  duration: const Duration(milliseconds: 220),
                                  switchInCurve: Curves.easeOut,
                                  switchOutCurve: Curves.easeIn,
                                  child: Text(
                                    article.displaySummary,
                                    key: ValueKey(article.displaySummary),
                                    style:
                                        Theme.of(context).textTheme.bodyLarge,
                                  ),
                                ),
                        )
                      else
                        Text(
                          l10n.articleDetailNoSummary,
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      AnimatedSize(
                        duration: const Duration(milliseconds: 240),
                        curve: Curves.easeOut,
                        alignment: Alignment.topCenter,
                        child: viewData.showPreview
                            ? const Column(
                                key: ValueKey('preview-extras'),
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  SizedBox(height: 16),
                                  ArticleDetailPreviewExtras(),
                                ],
                              )
                            : const SizedBox.shrink(
                                key: ValueKey('preview-extras-empty'),
                              ),
                      ),
                      const SizedBox(height: 24),
                      FilledButton.icon(
                        onPressed: article.url.trim().isEmpty
                            ? null
                            : () async {
                                ref
                                    .read(appAnalyticsProvider)
                                    .trackFeedArticleOpen(
                                      articleId: article.id,
                                      source: 'detail_screen',
                                    );

                                final launched =
                                    await launchExternalUrl(article.url);
                                if (!launched && context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(l10n.feedOpenLinkFailed),
                                    ),
                                  );
                                }
                              },
                        icon: const Icon(Icons.open_in_new),
                        label: Text(l10n.articleReadOriginalAction),
                      ),
                      RelatedArticlesSection(
                        articleId: article.id,
                        articles: article.relatedArticles,
                        totalCount: article.relatedArticlesTotal,
                        isPreview: viewData.showPreview,
                        onArticleTap: (related) {
                          unawaited(
                            _openRelatedArticle(
                              context,
                              ref,
                              related,
                              parentArticleId: article.id,
                              source: 'detail_section',
                            ),
                          );
                        },
                        onViewAll: () {
                          ref.read(appAnalyticsProvider).trackFeedRelatedViewAll(
                                articleId: article.id,
                                totalCount: article.relatedArticlesTotal,
                              );
                          RelatedArticlesSheet.show(
                            context,
                            articleId: article.id,
                            initialArticles: article.relatedArticles,
                            totalCount: article.relatedArticlesTotal,
                            onArticleTap: (related) {
                              unawaited(
                                _openRelatedArticle(
                                  context,
                                  ref,
                                  related,
                                  parentArticleId: article.id,
                                  source: 'related_sheet',
                                ),
                              );
                            },
                          );
                        },
                      ),
                    ]),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

Future<void> _openRelatedArticle(
  BuildContext context,
  WidgetRef ref,
  FeedItem item, {
  required String parentArticleId,
  required String source,
}) async {
  ref.read(appAnalyticsProvider).trackFeedRelatedClick(
        articleId: parentArticleId,
        relatedArticleId: item.id,
        source: source,
      );
  ref.read(appAnalyticsProvider).trackFeedArticleOpen(
        articleId: item.id,
        source: 'related_article',
      );
  await ref.read(articleDetailRepositoryProvider).cachePreviewFromFeedItem(item);
  if (!context.mounted) {
    return;
  }
  await context.push('/feed/article/${item.id}');
}
