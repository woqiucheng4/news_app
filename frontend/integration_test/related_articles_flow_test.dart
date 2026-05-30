import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:newsflow_frontend/app/app.dart';
import 'package:newsflow_frontend/app/newsflow_bootstrap.dart';
import 'package:newsflow_frontend/app/router/app_router.dart';
import 'package:newsflow_frontend/core/analytics/analytics_debug_log_provider.dart';
import 'package:newsflow_frontend/features/feed/presentation/providers/feed_data_providers.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../test/helpers/integration_article_detail_repository.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('related articles end-to-end flow on article detail', (tester) async {
    final relatedArticles = [
      integrationRelatedItem('rel-1', 'Integration related one'),
      integrationRelatedItem('rel-2', 'Integration related two'),
      integrationRelatedItem('rel-3', 'Integration related three'),
    ];
    final article = buildIntegrationArticleDetail(
      articleId: 'parent-1',
      relatedArticles: relatedArticles,
      relatedTotal: 5,
    );

    final coreOverrides = await createNewsFlowCoreOverrides();
    final container = ProviderContainer(
      overrides: [
        ...coreOverrides,
        articleDetailRepositoryProvider.overrideWith(
          (ref) => IntegrationArticleDetailRepository(article),
        ),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const NewsFlowApp(),
      ),
    );
    await tester.pumpAndSettle();

    container.read(appRouterProvider).go('/feed/article/parent-1');
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('related_articles_section')), findsOneWidget);
    expect(find.text('Integration related one'), findsOneWidget);
    expect(find.text('View all (5)'), findsOneWidget);

    final carousel = find.byKey(const Key('related_articles_carousel'));
    expect(carousel, findsOneWidget);
    await tester.drag(carousel, const Offset(-220, 0));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    await tester.tap(find.text('Integration related one'));
    await tester.pumpAndSettle();

    final log = container.read(analyticsDebugLogProvider);
    expect(log.any((entry) => entry.eventName == 'feed_related_impression'), isTrue);
    expect(log.any((entry) => entry.eventName == 'feed_related_swipe'), isTrue);
    expect(log.any((entry) => entry.eventName == 'feed_related_click'), isTrue);
    expect(log.any((entry) => entry.eventName == 'feed_article_open'), isTrue);
  });
}
