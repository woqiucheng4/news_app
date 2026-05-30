import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../core/network/user_facing_error.dart';
import '../../../../l10n/app_localizations.dart';
import '../../domain/models/feed_item.dart';
import '../providers/feed_data_providers.dart';
import 'related_article_tile.dart';

class RelatedArticlesSheet extends ConsumerStatefulWidget {
  const RelatedArticlesSheet({
    super.key,
    required this.articleId,
    required this.initialArticles,
    required this.totalCount,
    required this.onArticleTap,
  });

  final String articleId;
  final List<FeedItem> initialArticles;
  final int totalCount;
  final ValueChanged<FeedItem> onArticleTap;

  static Future<void> show(
    BuildContext context, {
    required String articleId,
    required List<FeedItem> initialArticles,
    required int totalCount,
    required ValueChanged<FeedItem> onArticleTap,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) {
        return RelatedArticlesSheet(
          articleId: articleId,
          initialArticles: initialArticles,
          totalCount: totalCount,
          onArticleTap: onArticleTap,
        );
      },
    );
  }

  @override
  ConsumerState<RelatedArticlesSheet> createState() =>
      _RelatedArticlesSheetState();
}

class _RelatedArticlesSheetState extends ConsumerState<RelatedArticlesSheet> {
  late List<FeedItem> _articles;
  var _page = 1;
  var _hasMore = false;
  var _isLoadingMore = false;
  var _isInitialLoading = false;
  var _sheetUserScrolled = false;
  var _sheetImpressionTracked = false;
  int? _resolvedTotalCount;
  String? _loadErrorMessage;

  int get _effectiveTotalCount => _resolvedTotalCount ?? widget.totalCount;

  @override
  void initState() {
    super.initState();
    _articles = [...widget.initialArticles];
    _hasMore = widget.totalCount > _articles.length;

    if (_articles.isEmpty && widget.totalCount > 0) {
      _isInitialLoading = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        unawaited(_loadPage(1, replaceExisting: true));
      });
    } else {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _trackSheetImpressionIfNeeded();
      });
    }
  }

  void _trackSheetImpressionIfNeeded() {
    if (_sheetImpressionTracked) {
      return;
    }

    if (_isInitialLoading && _articles.isEmpty && widget.totalCount > 0) {
      return;
    }

    _sheetImpressionTracked = true;
    ref.read(appAnalyticsProvider).trackFeedRelatedImpression(
          articleId: widget.articleId,
          visibleCount: _articles.length,
          totalCount: _effectiveTotalCount,
          source: 'related_sheet',
          displayState: _articles.isEmpty ? 'empty' : 'content',
        );
  }

  Future<void> _loadPage(int page, {required bool replaceExisting}) async {
    if (_isLoadingMore) {
      return;
    }

    final l10n = AppLocalizations.of(context)!;

    setState(() {
      _isLoadingMore = true;
      _loadErrorMessage = null;
      if (replaceExisting) {
        _isInitialLoading = true;
      }
    });

    try {
      final result = await ref
          .read(articleDetailRepositoryProvider)
          .fetchRelatedArticles(widget.articleId, page: page);

      if (!mounted) {
        return;
      }

      setState(() {
        _page = page;
        _articles = replaceExisting
            ? [...result.articles]
            : [..._articles, ...result.articles];
        _hasMore = result.hasMore;
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
          _isLoadingMore = false;
          _isInitialLoading = false;
        });
        _trackSheetImpressionIfNeeded();
      }
    }
  }

  Future<void> _loadMore() async {
    if (_isLoadingMore || !_hasMore || _loadErrorMessage != null) {
      return;
    }

    await _loadPage(_page + 1, replaceExisting: false);
  }

  Future<void> _retry() async {
    if (_articles.isEmpty) {
      await _loadPage(1, replaceExisting: true);
      return;
    }

    await _loadPage(_page + 1, replaceExisting: false);
  }

  bool _onScroll(ScrollNotification notification) {
    if (notification is UserScrollNotification &&
        notification.direction != ScrollDirection.idle) {
      _sheetUserScrolled = true;
    }

    if (notification is ScrollEndNotification &&
        notification.depth == 0 &&
        _sheetUserScrolled) {
      _sheetUserScrolled = false;
      final metrics = notification.metrics;
      if (metrics.pixels > 0) {
        ref.read(appAnalyticsProvider).trackFeedRelatedSwipe(
              articleId: widget.articleId,
              source: 'related_sheet',
              scrollOffset: metrics.pixels.round(),
              maxScrollExtent: metrics.maxScrollExtent.round(),
            );
      }
    }

    if (!_hasMore || _isLoadingMore || _loadErrorMessage != null) {
      return false;
    }

    if (notification.metrics.pixels >=
        notification.metrics.maxScrollExtent - 160) {
      unawaited(_loadMore());
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.72,
      minChildSize: 0.4,
      maxChildSize: 0.92,
      builder: (context, scrollController) {
        return Material(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        l10n.articleDetailRelatedTitle,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: _buildBody(
                  context,
                  l10n,
                  scrollController,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildBody(
    BuildContext context,
    AppLocalizations l10n,
    ScrollController scrollController,
  ) {
    if (_isInitialLoading && _articles.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_articles.isEmpty && _loadErrorMessage != null) {
      return _RelatedSheetErrorState(
        message: _loadErrorMessage!,
        retryLabel: l10n.retryAction,
        onRetry: () => unawaited(_retry()),
      );
    }

    if (_articles.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            l10n.articleDetailRelatedEmpty,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
        ),
      );
    }

    return NotificationListener<ScrollNotification>(
      onNotification: _onScroll,
      child: ListView.builder(
        controller: scrollController,
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
        itemCount: _articles.length + _footerItemCount,
        itemBuilder: (context, index) {
          if (index >= _articles.length) {
            return _buildFooter(context, l10n);
          }

          final item = _articles[index];
          return RelatedArticleTile(
            item: item,
            onTap: () {
              ref.read(appAnalyticsProvider).trackFeedRelatedClick(
                    articleId: widget.articleId,
                    relatedArticleId: item.id,
                    source: 'related_sheet',
                  );
              Navigator.of(context).pop();
              widget.onArticleTap(item);
            },
          );
        },
      ),
    );
  }

  int get _footerItemCount {
    if (_isLoadingMore) {
      return 1;
    }
    if (_loadErrorMessage != null && _hasMore) {
      return 1;
    }
    return 0;
  }

  Widget _buildFooter(BuildContext context, AppLocalizations l10n) {
    if (_isLoadingMore) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 16),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return _RelatedSheetErrorState(
      message: _loadErrorMessage ?? l10n.articleDetailRelatedLoadFailed,
      retryLabel: l10n.retryAction,
      onRetry: () => unawaited(_retry()),
      compact: true,
    );
  }
}

class _RelatedSheetErrorState extends StatelessWidget {
  const _RelatedSheetErrorState({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
    this.compact = false,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final padding = compact ? 16.0 : 24.0;

    return Padding(
      padding: EdgeInsets.all(padding),
      child: Column(
        mainAxisAlignment:
            compact ? MainAxisAlignment.start : MainAxisAlignment.center,
        mainAxisSize: compact ? MainAxisSize.min : MainAxisSize.max,
        children: [
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: onRetry,
            child: Text(retryLabel),
          ),
        ],
      ),
    );
  }
}
