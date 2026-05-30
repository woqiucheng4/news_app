import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

import 'app/app.dart';
import 'app/newsflow_bootstrap.dart';
import 'core/analytics/firebase_app_bootstrap.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  usePathUrlStrategy();
  await FirebaseAppBootstrap.initializeIfConfigured();

  final coreOverrides = await createNewsFlowCoreOverrides();

  runApp(
    ProviderScope(
      overrides: coreOverrides,
      child: const NewsFlowApp(),
    ),
  );
}
