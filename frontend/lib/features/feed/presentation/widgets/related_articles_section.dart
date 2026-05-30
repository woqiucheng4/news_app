import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../core/network/user_facing_error.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import '../providers/feed_data_providers.dart';
import 'related_article_tile.dart';

enum RelatedArticlesSectionState {
  hidden,
  loading,
  error,
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
  var _isFetching = false;
  var _fetchAttempted = false;
  var _fetchedArticles = <FeedItem>[];
  int? _resolvedTotalCount;
  String? _loadErrorMessage;

  List<FeedItem> get _effectiveArticles =>
      widget.articles.isNotEmpty ? widget.articles : _fetchedArticles;

  int get _effectiveTotalCount => widget.articles.isNotEmpty
      ? widget.totalCount
      : (_resolvedTotalCount ?? widget.totalCount);

  RelatedArticlesSectionState get _state {
    if (_effectiveArticles.isNotEmpty) {
      return RelatedArticlesSectionState.content;
    }
    if (widget.isPreview) {
      return RelatedArticlesSectionState.hidden;
    }
    if (_loadErrorMessage != null && _fetchAttempted) {
      return RelatedArticlesSectionState.error;
    }
    if (_isFetching || _shouldFetch) {
      return RelatedArticlesSectionState.loading;
    }
    return RelatedArticlesSectionState.empty;
  }

  bool get _shouldFetch =>
      !widget.isPreview &&
      widget.articles.isEmpty &&
      widget.totalCount > 0 &&
      !_fetchAttempted;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scheduleFetchIfNeeded();
      _trackImpressionIfNeeded();
    });
  }

  @override
  void didUpdateWidget(covariant RelatedArticlesSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isPreview && !widget.isPreview) {
      _impressionTracked = false;
      _carouselUserScrolled = false;
      _resetFetchState();
    }

    if (widget.articles.isNotEmpty) {
      _fetchAttempted = true;
      _loadErrorMessage = null;
      _fetchedArticles = [];
      _resolvedTotalCount = null;
    } else if (oldWidget.totalCount != widget.totalCount ||
        oldWidget.articleId != widget.articleId) {
      _resetFetchState();
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scheduleFetchIfNeeded();
      _trackImpressionIfNeeded();
    });
  }

  void _resetFetchState() {
    _fetchAttempted = false;
    _isFetching = false;
    _fetchedArticles = [];
    _resolvedTotalCount = null;
    _loadErrorMessage = null;
  }

  void _scheduleFetchIfNeeded() {
    if (!_shouldFetch || _isFetching) {
      return;
    }
    unawaited(_fetchPreview());
  }

  Future<void> _fetchPreview() async {
    if (!_shouldFetch || _isFetching) {
      return;
    }

    final l10n = AppLocalizations.of(context)!;

    setState(() {
      _isFetching = true;
      _loadErrorMessage = null;
    });

    try {
      final result = await ref
          .read(articleDetailRepositoryProvider)
          .fetchRelatedArticles(widget.articleId, page: 1);

      if (!mounted) {
        return;
      }

      if (widget.articles.isNotEmpty) {
        return;
      }

      setState(() {
        _fetchedArticles = [...result.articles];
        _resolvedTotalCount = result.total;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loadErrorMessage = resolveUserFacingError(
          error,
          l10n,
          fallback: l10n.articleDetailRelatedLoadFailed,
        );
      });
    } finally {
      if (mounted) {
        setState(() {
          _isFetching = false;
          _fetchAttempted = true;
          _impressionTracked = false;
        });
        _trackImpressionIfNeeded();
      }
    }
  }

  void _retryFetch() {
    setState(() {
      _fetchAttempted = false;
      _loadErrorMessage = null;
      _impressionTracked = false;
    });
    unawaited(_fetchPreview());
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
        state == RelatedArticlesSectionState.loading ||
        state == RelatedArticlesSectionState.error) {
      return;
    }

    _impressionTracked = true;
    ref.read(appAnalyticsProvider).trackFeedRelatedImpression(
          articleId: widget.articleId,
          visibleCount: _effectiveArticles.length,
          totalCount: _effectiveTotalCount,
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
    final articles = _effectiveArticles;

    if (state == RelatedArticlesSectionState.hidden) {
      return const SizedBox.shrink();
    }

    return Column(
      key: const Key('related_articles_section'),
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
                _effectiveTotalCount > articles.length)
              TextButton(
                onPressed: () {
                  ref.read(appAnalyticsProvider).trackFeedRelatedViewAll(
                        articleId: widget.articleId,
                        totalCount: _effectiveTotalCount,
                      );
                  widget.onViewAll();
                },
                child: Text(l10n.articleDetailRelatedViewAll(_effectiveTotalCount)),
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
          RelatedArticlesSectionState.error => _RelatedArticlesErrorCard(
              message: _loadErrorMessage ?? l10n.articleDetailRelatedLoadFailed,
              retryLabel: l10n.retryAction,
              onRetry: _retryFetch,
            ),
          RelatedArticlesSectionState.empty => _RelatedArticlesEmptyCard(
              message: l10n.articleDetailRelatedEmpty,
            ),
          RelatedArticlesSectionState.content => SizedBox(
              height: RelatedArticlesSection.carouselHeight,
              child: NotificationListener<ScrollNotification>(
                onNotification: _onCarouselScroll,
                child: ListView.separated(
                  key: const Key('related_articles_carousel'),
                  scrollDirection: Axis.horizontal,
                  itemCount: articles.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 12),
                  itemBuilder: (context, index) {
                    final related = articles[index];
                    return SizedBox(
                      width: RelatedArticlesSection.cardWidth,
                      child: RelatedArticleTile(
                        item: related,
                        compact: true,
                        onTap: () {
                          ref.read(appAnalyticsProvider).trackFeedRelatedClick(
                                articleId: widget.articleId,
                                relatedArticleId: related.id,
                                source: 'detail_section',
                              );
                          widget.onArticleTap(related);
                        },
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

class _RelatedArticlesErrorCard extends StatelessWidget {
  const _RelatedArticlesErrorCard({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerLeft,
              child: FilledButton(
                onPressed: onRetry,
                child: Text(retryLabel),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
