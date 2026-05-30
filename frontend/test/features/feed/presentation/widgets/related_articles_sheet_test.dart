import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newsflow_frontend/core/analytics/analytics_debug_log_provider.dart';
import 'package:newsflow_frontend/features/feed/domain/models/feed_item.dart';
import 'package:newsflow_frontend/features/feed/domain/models/related_articles_page.dart';
import 'package:newsflow_frontend/features/feed/presentation/providers/feed_data_providers.dart';
import 'package:newsflow_frontend/features/feed/presentation/widgets/related_articles_sheet.dart';
import 'package:newsflow_frontend/l10n/app_localizations.dart';
import '../../../../../helpers/stub_article_detail_repository.dart';
import 'package:shared_preferences/shared_preferences.dart';

FeedItem _relatedItem(String id, String title) {
  return FeedItem(
    id: id,
    title: title,
    summary: 'Summary for $title',
    sourceUrl: 'https://example.com/$id',
  );
}

Widget _buildHarness({
  required ProviderContainer container,
  required Widget child,
}) {
  return UncontrolledProviderScope(
    container: container,
    child: MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(body: child),
    ),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('RelatedArticlesSheet analytics', () {
    testWidgets('tracks content impression after initial fetch', (tester) async {
      final container = ProviderContainer(
        overrides: [
          articleDetailRepositoryProvider.overrideWith(
            (ref) => StubArticleDetailRepository(
              (_) async => RelatedArticlesPage(
                page: 1,
                pageSize: 20,
                articles: [
                  _relatedItem('rel-1', 'Sheet related one'),
                  _relatedItem('rel-2', 'Sheet related two'),
                ],
                hasMore: false,
                total: 2,
              ),
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      await tester.pumpWidget(
        _buildHarness(
          container: container,
          child: SizedBox(
            height: 640,
            child: RelatedArticlesSheet(
              articleId: 'parent-1',
              initialArticles: const [],
              totalCount: 2,
              onArticleTap: (_) {},
            ),
          ),
        ),
      );

      await tester.pump();
      await tester.pumpAndSettle();

      expect(find.text('Sheet related one'), findsOneWidget);

      final impressions = container
          .read(analyticsDebugLogProvider)
          .where((entry) => entry.eventName == 'feed_related_impression')
          .toList();
      expect(impressions, hasLength(1));
      expect(impressions.single.params['source'], 'related_sheet');
      expect(impressions.single.params['display_state'], 'content');
      expect(impressions.single.params['visible_count'], 2);
    });

    testWidgets('does not track empty impression before fetch completes', (
      tester,
    ) async {
      final container = ProviderContainer(
        overrides: [
          articleDetailRepositoryProvider.overrideWith(
            (ref) => StubArticleDetailRepository(
              (_) async {
                await Future<void>.delayed(const Duration(milliseconds: 200));
                return RelatedArticlesPage(
                  page: 1,
                  pageSize: 20,
                  articles: [_relatedItem('rel-1', 'Delayed related')],
                  hasMore: false,
                  total: 1,
                );
              },
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      await tester.pumpWidget(
        _buildHarness(
          container: container,
          child: SizedBox(
            height: 640,
            child: RelatedArticlesSheet(
              articleId: 'parent-1',
              initialArticles: const [],
              totalCount: 1,
              onArticleTap: (_) {},
            ),
          ),
        ),
      );

      await tester.pump();
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      final earlyLog = container.read(analyticsDebugLogProvider);
      expect(
        earlyLog.any((entry) => entry.eventName == 'feed_related_impression'),
        isFalse,
      );

      await tester.pumpAndSettle();

      final impressions = container
          .read(analyticsDebugLogProvider)
          .where((entry) => entry.eventName == 'feed_related_impression')
          .toList();
      expect(impressions, hasLength(1));
      expect(impressions.single.params['display_state'], 'content');
    });

    testWidgets('tracks click when sheet item is tapped', (tester) async {
      final container = ProviderContainer(
        overrides: [
          articleDetailRepositoryProvider.overrideWith(
            (ref) => StubArticleDetailRepository(
              (_) async => RelatedArticlesPage(
                page: 1,
                pageSize: 20,
                articles: [_relatedItem('rel-1', 'Sheet related one')],
                hasMore: false,
                total: 1,
              ),
            ),
          ),
        ],
      );
      addTearDown(container.dispose);
      FeedItem? tapped;

      await tester.pumpWidget(
        _buildHarness(
          container: container,
          child: SizedBox(
            height: 640,
            child: RelatedArticlesSheet(
              articleId: 'parent-1',
              initialArticles: [_relatedItem('rel-1', 'Sheet related one')],
              totalCount: 1,
              onArticleTap: (item) => tapped = item,
            ),
          ),
        ),
      );

      await tester.pump();
      await tester.pumpAndSettle();

      await tester.tap(find.text('Sheet related one'));
      await tester.pumpAndSettle();

      expect(tapped?.id, 'rel-1');
      final log = container.read(analyticsDebugLogProvider);
      expect(log.any((entry) => entry.eventName == 'feed_related_click'), isTrue);
      final click = log.firstWhere(
        (entry) => entry.eventName == 'feed_related_click',
      );
      expect(click.params['source'], 'related_sheet');
    });
  });
}
