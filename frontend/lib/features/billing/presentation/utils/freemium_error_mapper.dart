import 'package:dio/dio.dart';

import '../../../../l10n/app_localizations.dart';

enum FreemiumErrorCode {
  subscriptionLimitReached,
  dailyViewLimitReached,
  premiumRequired,
  unknown,
}

class FreemiumError {
  const FreemiumError({
    required this.code,
    this.limit,
    this.used,
    this.feature,
    this.message,
  });

  final FreemiumErrorCode code;
  final int? limit;
  final int? used;
  final String? feature;
  final String? message;

  bool get shouldOfferUpgrade =>
      code == FreemiumErrorCode.subscriptionLimitReached ||
      code == FreemiumErrorCode.dailyViewLimitReached ||
      code == FreemiumErrorCode.premiumRequired;
}

FreemiumError? parseFreemiumError(Object error) {
  if (error is! DioException || error.type != DioExceptionType.badResponse) {
    return null;
  }
  if (error.response?.statusCode != 403) {
    return null;
  }

  final detail = _readDetailMap(error.response?.data);
  if (detail == null) {
    return null;
  }

  final code = detail['code'] as String?;
  switch (code) {
    case 'SUBSCRIPTION_LIMIT_REACHED':
      return FreemiumError(
        code: FreemiumErrorCode.subscriptionLimitReached,
        limit: detail['limit'] as int?,
        used: detail['used'] as int?,
        message: detail['message'] as String?,
      );
    case 'DAILY_VIEW_LIMIT_REACHED':
      return FreemiumError(
        code: FreemiumErrorCode.dailyViewLimitReached,
        limit: detail['limit'] as int?,
        used: detail['used'] as int?,
        message: detail['message'] as String?,
      );
    case 'PREMIUM_REQUIRED':
      return FreemiumError(
        code: FreemiumErrorCode.premiumRequired,
        feature: detail['feature'] as String?,
        message: detail['message'] as String?,
      );
    default:
      return const FreemiumError(code: FreemiumErrorCode.unknown);
  }
}

String mapFreemiumError(Object error, AppLocalizations l10n) {
  final freemiumError = parseFreemiumError(error);
  if (freemiumError == null) {
    return mapApiError(error, l10n);
  }

  switch (freemiumError.code) {
    case FreemiumErrorCode.subscriptionLimitReached:
      final limit = freemiumError.limit;
      if (limit != null) {
        return l10n.freemiumSubscriptionLimitReached(limit);
      }
      return l10n.freemiumSubscriptionLimitReachedGeneric;
    case FreemiumErrorCode.dailyViewLimitReached:
      final limit = freemiumError.limit;
      if (limit != null) {
        return l10n.freemiumDailyViewLimitReached(limit);
      }
      return l10n.freemiumDailyViewLimitReachedGeneric;
    case FreemiumErrorCode.premiumRequired:
      return l10n.freemiumPremiumRequired;
    case FreemiumErrorCode.unknown:
      return freemiumError.message ?? l10n.errorForbidden;
  }
}

Map<String, dynamic>? _readDetailMap(Object? data) {
  if (data is! Map<String, dynamic>) {
    return null;
  }
  final detail = data['detail'];
  if (detail is Map<String, dynamic>) {
    return detail;
  }
  return null;
}

String mapApiError(Object error, AppLocalizations l10n) {
  if (error is DioException) {
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
        final detailMap = _readDetailMap(error.response?.data);
        final detailMessage = detailMap?['message'];
        if (detailMessage is String && detailMessage.trim().isNotEmpty) {
          return detailMessage.trim();
        }
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

  return l10n.errorUnknown;
}
