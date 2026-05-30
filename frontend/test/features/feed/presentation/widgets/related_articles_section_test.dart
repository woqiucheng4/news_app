import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newsflow_frontend/core/analytics/analytics_debug_log_provider.dart';
import 'package:newsflow_frontend/features/feed/domain/models/feed_item.dart';
import 'package:newsflow_frontend/features/feed/presentation/widgets/related_articles_section.dart';
import 'package:newsflow_frontend/l10n/app_localizations.dart';
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

  group('RelatedArticlesSection analytics', () {
    testWidgets('tracks impression after content renders', (tester) async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      await tester.pumpWidget(
        _buildHarness(
          container: container,
          child: RelatedArticlesSection(
            articleId: 'parent-1',
            articles: [
              _relatedItem('rel-1', 'Related one'),
              _relatedItem('rel-2', 'Related two'),
            ],
            totalCount: 2,
            isPreview: false,
            onArticleTap: (_) {},
            onViewAll: () {},
          ),
        ),
      );

      await tester.pump();
      await tester.pump();

      final log = container.read(analyticsDebugLogProvider);
      expect(log.any((entry) => entry.eventName == 'feed_related_impression'), isTrue);
      final impression = log.firstWhere(
        (entry) => entry.eventName == 'feed_related_impression',
      );
      expect(impression.params['article_id'], 'parent-1');
      expect(impression.params['source'], 'detail_section');
    });

    testWidgets('tracks swipe after horizontal drag', (tester) async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      await tester.pumpWidget(
        _buildHarness(
          container: container,
          child: SizedBox(
            width: 360,
            child: RelatedArticlesSection(
              articleId: 'parent-1',
              articles: [
                _relatedItem('rel-1', 'Related one'),
                _relatedItem('rel-2', 'Related two'),
                _relatedItem('rel-3', 'Related three'),
              ],
              totalCount: 3,
              isPreview: false,
              onArticleTap: (_) {},
              onViewAll: () {},
            ),
          ),
        ),
      );

      await tester.pump();
      await tester.pump();

      final listFinder = find.byType(ListView);
      expect(listFinder, findsOneWidget);

      await tester.drag(listFinder, const Offset(-200, 0));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      final log = container.read(analyticsDebugLogProvider);
      expect(log.any((entry) => entry.eventName == 'feed_related_swipe'), isTrue);
      final swipe = log.firstWhere(
        (entry) => entry.eventName == 'feed_related_swipe',
      );
      expect(swipe.params['article_id'], 'parent-1');
      expect(swipe.params['source'], 'detail_section');
    });
  });
}
