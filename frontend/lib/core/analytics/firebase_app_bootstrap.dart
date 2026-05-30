import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';

/// Optional Firebase bootstrap for analytics transport.
class FirebaseAppBootstrap {
  const FirebaseAppBootstrap._();

  static const enabled = bool.fromEnvironment('NEWSFLOW_ENABLE_FIREBASE');

  static Future<void> initializeIfConfigured() async {
    if (!enabled) return;

    try {
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp();
      }
    } catch (error, stackTrace) {
      debugPrint('[firebase] initialize skipped: $error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }
}
