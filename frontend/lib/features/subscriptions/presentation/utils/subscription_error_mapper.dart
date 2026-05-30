import 'package:dio/dio.dart';

import '../../../../l10n/app_localizations.dart';

String mapSubscriptionError(Object error, AppLocalizations l10n) {
  if (error is! DioException) {
    return l10n.errorUnknown;
  }

  switch (error.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return l10n.errorTimeout;
    case DioExceptionType.connectionError:
    case DioExceptionType.unknown:
      return l10n.errorNetwork;
    case DioExceptionType.badResponse:
      final statusCode = error.response?.statusCode ?? 0;
      if (statusCode == 401) return l10n.errorUnauthorized;
      if (statusCode == 403) return l10n.errorForbidden;
      if (statusCode == 404) return l10n.errorNotFound;
      if (statusCode == 429) return l10n.errorRateLimited;
      if (statusCode >= 500) return l10n.errorServer;
      return l10n.errorUnknown;
    case DioExceptionType.cancel:
    case DioExceptionType.badCertificate:
      return l10n.errorUnknown;
  }
}
