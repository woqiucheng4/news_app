import 'package:flutter/material.dart';

import 'source_favicon.dart';

String articleTitleHeroTag(String articleId) => 'article-title-$articleId';

String articleCategoryHeroTag(String articleId) => 'article-category-$articleId';

String articleSummaryHeroTag(String articleId) => 'article-summary-$articleId';

String articleSourceMetaHeroTag(String articleId) => 'article-source-$articleId';

class ArticleTitleHero extends StatelessWidget {
  const ArticleTitleHero({
    super.key,
    required this.articleId,
    required this.title,
    required this.style,
    this.maxLines,
    this.overflow,
  });

  final String articleId;
  final String title;
  final TextStyle? style;
  final int? maxLines;
  final TextOverflow? overflow;

  @override
  Widget build(BuildContext context) {
    return Hero(
      tag: articleTitleHeroTag(articleId),
      child: Material(
        color: Colors.transparent,
        child: Text(
          title,
          style: style,
          maxLines: maxLines,
          overflow: overflow,
        ),
      ),
    );
  }
}

class ArticleCategoryHero extends StatelessWidget {
  const ArticleCategoryHero({
    super.key,
    required this.articleId,
    required this.category,
    this.visualDensity = VisualDensity.compact,
  });

  final String articleId;
  final String category;
  final VisualDensity visualDensity;

  @override
  Widget build(BuildContext context) {
    return Hero(
      tag: articleCategoryHeroTag(articleId),
      child: Material(
        color: Colors.transparent,
        child: Chip(
          label: Text(category),
          visualDensity: visualDensity,
          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
      ),
    );
  }
}

class ArticleSummaryHero extends StatelessWidget {
  const ArticleSummaryHero({
    super.key,
    required this.articleId,
    required this.summary,
    required this.style,
    this.maxLines,
    this.overflow,
  });

  final String articleId;
  final String summary;
  final TextStyle? style;
  final int? maxLines;
  final TextOverflow? overflow;

  static Widget flightShuttleBuilder(
    BuildContext flightContext,
    Animation<double> animation,
    HeroFlightDirection flightDirection,
    BuildContext fromHeroContext,
    BuildContext toHeroContext,
  ) {
    final fromHero = fromHeroContext.widget as Hero;
    final toHero = toHeroContext.widget as Hero;

    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        return flightDirection == HeroFlightDirection.push
            ? fromHero.child
            : toHero.child;
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final normalizedSummary = summary.trim();
    if (normalizedSummary.isEmpty) {
      return const SizedBox.shrink();
    }

    return Hero(
      tag: articleSummaryHeroTag(articleId),
      flightShuttleBuilder: flightShuttleBuilder,
      child: Material(
        color: Colors.transparent,
        child: Text(
          normalizedSummary,
          style: style,
          maxLines: maxLines,
          overflow: overflow,
        ),
      ),
    );
  }
}

class ArticleSourceMetaHero extends StatelessWidget {
  const ArticleSourceMetaHero({
    super.key,
    required this.articleId,
    required this.label,
    required this.faviconUrl,
    this.style,
    this.iconSize = 18,
  });

  final String articleId;
  final String label;
  final String? faviconUrl;
  final TextStyle? style;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    final normalizedLabel = label.trim();
    if (normalizedLabel.isEmpty) {
      return const SizedBox.shrink();
    }

    return Hero(
      tag: articleSourceMetaHeroTag(articleId),
      child: Material(
        color: Colors.transparent,
        child: Row(
          children: [
            SourceFavicon(faviconUrl: faviconUrl, size: iconSize),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                normalizedLabel,
                style: style,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
