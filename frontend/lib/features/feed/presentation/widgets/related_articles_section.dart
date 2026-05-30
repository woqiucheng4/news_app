import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import 'related_article_tile.dart';

enum RelatedArticlesSectionState {
  hidden,
  loading,
  empty,
  content,
}

class RelatedArticlesSection extends ConsumerStatefulWidget {
  const RelatedArticlesSection({
    super.key,
    required this.articleId,
    required this.articles,
    required this.totalCount,
    required this.isPreview,
    required this.onArticleTap,
    required this.onViewAll,
  });

  final String articleId;
  final List<FeedItem> articles;
  final int totalCount;
  final bool isPreview;
  final ValueChanged<FeedItem> onArticleTap;
  final VoidCallback onViewAll;

  static const carouselHeight = 128.0;
  static const cardWidth = 280.0;

  @override
  ConsumerState<RelatedArticlesSection> createState() =>
      _RelatedArticlesSectionState();
}

class _RelatedArticlesSectionState extends ConsumerState<RelatedArticlesSection> {
  var _impressionTracked = false;
  var _carouselUserScrolled = false;

  RelatedArticlesSectionState get _state {
    if (widget.articles.isNotEmpty) {
      return RelatedArticlesSectionState.content;
    }
    if (widget.isPreview) {
      return RelatedArticlesSectionState.hidden;
    }
    if (widget.totalCount > 0) {
      return RelatedArticlesSectionState.loading;
    }
    return RelatedArticlesSectionState.empty;
  }

  @override
  void didUpdateWidget(covariant RelatedArticlesSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isPreview && !widget.isPreview) {
      _impressionTracked = false;
      _carouselUserScrolled = false;
    }
  }

  bool _onCarouselScroll(ScrollNotification notification) {
    if (notification is UserScrollNotification &&
        notification.direction != ScrollDirection.idle) {
      _carouselUserScrolled = true;
      return false;
    }

    if (notification is! ScrollEndNotification ||
        notification.depth != 0 ||
        !_carouselUserScrolled) {
      return false;
    }

    _carouselUserScrolled = false;
    final metrics = notification.metrics;
    if (metrics.pixels <= 0) {
      return false;
    }

    ref.read(appAnalyticsProvider).trackFeedRelatedSwipe(
          articleId: widget.articleId,
          source: 'detail_section',
          scrollOffset: metrics.pixels.round(),
          maxScrollExtent: metrics.maxScrollExtent.round(),
        );
    return false;
  }

  void _trackImpressionIfNeeded() {
    if (_impressionTracked) {
      return;
    }

    final state = _state;
    if (state == RelatedArticlesSectionState.hidden ||
        state == RelatedArticlesSectionState.loading) {
      return;
    }

    _impressionTracked = true;
    ref.read(appAnalyticsProvider).trackFeedRelatedImpression(
          articleId: widget.articleId,
          visibleCount: widget.articles.length,
          totalCount: widget.totalCount,
          source: 'detail_section',
          displayState: state == RelatedArticlesSectionState.empty
              ? 'empty'
              : 'content',
        );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final state = _state;

    if (state == RelatedArticlesSectionState.hidden) {
      return const SizedBox.shrink();
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _trackImpressionIfNeeded();
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 32),
        Row(
          children: [
            Expanded(
              child: Text(
                l10n.articleDetailRelatedTitle,
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            if (state == RelatedArticlesSectionState.content &&
                widget.totalCount > widget.articles.length)
              TextButton(
                onPressed: widget.onViewAll,
                child: Text(l10n.articleDetailRelatedViewAll(widget.totalCount)),
              ),
          ],
        ),
        const SizedBox(height: 12),
        switch (state) {
          RelatedArticlesSectionState.loading => const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: CircularProgressIndicator(),
              ),
            ),
          RelatedArticlesSectionState.empty => _RelatedArticlesEmptyCard(
              message: l10n.articleDetailRelatedEmpty,
            ),
          RelatedArticlesSectionState.content => SizedBox(
              height: RelatedArticlesSection.carouselHeight,
              child: NotificationListener<ScrollNotification>(
                onNotification: _onCarouselScroll,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: widget.articles.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 12),
                  itemBuilder: (context, index) {
                    final related = widget.articles[index];
                    return SizedBox(
                      width: RelatedArticlesSection.cardWidth,
                      child: RelatedArticleTile(
                        item: related,
                        compact: true,
                        onTap: () => widget.onArticleTap(related),
                      ),
                    );
                  },
                ),
              ),
            ),
          RelatedArticlesSectionState.hidden => const SizedBox.shrink(),
        },
      ],
    );
  }
}

class _RelatedArticlesEmptyCard extends StatelessWidget {
  const _RelatedArticlesEmptyCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              Icons.article_outlined,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
