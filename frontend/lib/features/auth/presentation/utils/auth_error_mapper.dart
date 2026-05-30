import 'package:dio/dio.dart';

import '../../domain/models/oauth_identity.dart';
import '../../../../l10n/app_localizations.dart';

String mapAuthError(Object error, AppLocalizations l10n) {
  if (error is OAuthCancelledException) {
    return l10n.oauthCancelled;
  }
  if (error is OAuthUnavailableException) {
    return error.message.isNotEmpty ? error.message : l10n.oauthUnavailable;
  }
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
      final detail = _readDetail(error.response?.data);
      if (statusCode == 401) {
        return detail ?? l10n.authInvalidCredentials;
      }
      if (statusCode == 400) {
        return detail ?? l10n.errorUnknown;
      }
      if (statusCode == 429) return l10n.errorRateLimited;
      if (statusCode >= 500) return l10n.errorServer;
      return detail ?? l10n.errorUnknown;
    case DioExceptionType.cancel:
    case DioExceptionType.badCertificate:
      return l10n.errorUnknown;
  }
}

String? _readDetail(Object? data) {
  if (data is Map<String, dynamic>) {
    final detail = data['detail'];
    if (detail is String && detail.trim().isNotEmpty) {
      return detail.trim();
    }
  }
  return null;
}
