import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:newsflow_frontend/core/push/push_navigation.dart';

void main() {
  testWidgets('handlePushNavigation opens feed for daily briefing', (tester) async {
    final router = GoRouter(
      routes: [
        GoRoute(path: '/', builder: (_, __) => const SizedBox()),
        GoRoute(path: '/feed', builder: (_, __) => const SizedBox()),
        GoRoute(
          path: '/feed/article/:id',
          builder: (_, __) => const SizedBox(),
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(routerConfig: router));

    handlePushNavigation(
      router,
      RemoteMessage(
        data: const {'notification_type': 'daily_briefing'},
      ),
    );
    await tester.pumpAndSettle();

    expect(router.state.uri.path, '/feed');
  });
}
