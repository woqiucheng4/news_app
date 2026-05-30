import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../../shared/widgets/rotating_icon.dart';

class FeedCacheBanner extends StatelessWidget {
  const FeedCacheBanner({
    super.key,
    this.showPreview = false,
    required this.showCached,
    required this.showOffline,
    this.margin = const EdgeInsets.fromLTRB(16, 8, 16, 0),
  });

  final bool showPreview;
  final bool showCached;
  final bool showOffline;
  final EdgeInsetsGeometry margin;

  @override
  Widget build(BuildContext context) {
    if (!showPreview && !showCached && !showOffline) {
      return const SizedBox.shrink();
    }

    final l10n = AppLocalizations.of(context)!;
    final message = showOffline
        ? l10n.feedOfflineBanner
        : showPreview
            ? l10n.articleDetailPreviewBanner
            : l10n.feedCachedBanner;
    final color = showOffline
        ? Theme.of(context).colorScheme.errorContainer
        : showPreview
            ? Theme.of(context).colorScheme.primaryContainer
            : Theme.of(context).colorScheme.secondaryContainer;

    return Card(
      margin: margin,
      color: color,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (showPreview)
              const RotatingIcon(icon: Icons.sync)
            else
              Icon(
                showOffline ? Icons.cloud_off : Icons.history,
                size: 20,
              ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
