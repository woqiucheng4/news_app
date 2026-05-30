import 'package:intl/intl.dart';

import '../../../l10n/app_localizations.dart';

String formatPublishedAt({
  required String? raw,
  required AppLocalizations l10n,
  required String localeName,
}) {
  if (raw == null || raw.trim().isEmpty) {
    return '';
  }

  final parsed = DateTime.tryParse(raw);
  if (parsed == null) {
    return '';
  }

  final local = parsed.toLocal();
  final difference = DateTime.now().difference(local);

  if (difference.inMinutes < 1) {
    return l10n.feedPublishedJustNow;
  }
  if (difference.inHours < 1) {
    return l10n.feedPublishedMinutesAgo(difference.inMinutes);
  }
  if (difference.inHours < 24) {
    return l10n.feedPublishedHoursAgo(difference.inHours);
  }
  if (difference.inDays < 7) {
    return l10n.feedPublishedDaysAgo(difference.inDays);
  }

  return DateFormat.yMMMd(localeName).format(local);
}
