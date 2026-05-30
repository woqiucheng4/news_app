import '../../../../l10n/app_localizations.dart';
import '../../domain/models/article_detail.dart';

String resolveArticleSourceLabel(
  ArticleDetail article,
  AppLocalizations l10n,
) {
  if (article.sourceName.isNotEmpty) {
    return article.sourceName;
  }

  try {
    final host = Uri.parse(article.url.trim()).host;
    if (host.isNotEmpty) {
      return host.startsWith('www.') ? host.substring(4) : host;
    }
  } catch (_) {
    // Fall back to the generic unknown-source label.
  }

  return l10n.feedSourceUnknown;
}
