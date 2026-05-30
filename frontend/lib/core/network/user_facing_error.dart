import 'package:dio/dio.dart';

import '../../l10n/app_localizations.dart';
import 'dio_error_utils.dart';
import 'network_error_utils.dart';

String resolveUserFacingError(
  Object error,
  AppLocalizations l10n, {
  required String fallback,
  String? networkFallback,
}) {
  if (isNetworkError(error)) {
    return networkFallback ?? l10n.articleDetailRelatedNetworkFailed;
  }

  if (error is DioException) {
    final statusCode = error.response?.statusCode;
    if (statusCode == 401) {
      return l10n.feedLoginRequiredTitle;
    }
    if (statusCode == 404) {
      return l10n.articleDetailRelatedEmpty;
    }
  }

  return fallback;
}
