import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newsflow_frontend/features/billing/presentation/utils/freemium_error_mapper.dart';
import 'package:newsflow_frontend/l10n/app_localizations.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('parseFreemiumError', () {
    test('returns subscription limit code', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/subscriptions/subscribe'),
        type: DioExceptionType.badResponse,
        response: Response(
          requestOptions: RequestOptions(path: '/subscriptions/subscribe'),
          statusCode: 403,
          data: {
            'detail': {
              'code': 'SUBSCRIPTION_LIMIT_REACHED',
              'limit': 5,
              'used': 5,
            },
          },
        ),
      );

      final parsed = parseFreemiumError(error);
      expect(parsed?.code, FreemiumErrorCode.subscriptionLimitReached);
      expect(parsed?.limit, 5);
      expect(parsed?.shouldOfferUpgrade, isTrue);
    });

    test('returns null for non-403 responses', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/articles/a-1'),
        type: DioExceptionType.badResponse,
        response: Response(
          requestOptions: RequestOptions(path: '/articles/a-1'),
          statusCode: 404,
        ),
      );

      expect(parseFreemiumError(error), isNull);
    });
  });

  group('mapFreemiumError', () {
    late AppLocalizations l10n;

    setUpAll(() async {
      l10n = await AppLocalizations.delegate.load(const Locale('en'));
    });

    test('maps daily view limit with limit value', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/articles/a-1'),
        type: DioExceptionType.badResponse,
        response: Response(
          requestOptions: RequestOptions(path: '/articles/a-1'),
          statusCode: 403,
          data: {
            'detail': {
              'code': 'DAILY_VIEW_LIMIT_REACHED',
              'limit': 20,
              'used': 20,
            },
          },
        ),
      );

      expect(
        mapFreemiumError(error, l10n),
        l10n.freemiumDailyViewLimitReached(20),
      );
    });
  });
}
