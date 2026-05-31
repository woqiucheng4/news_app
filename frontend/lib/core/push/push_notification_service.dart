import 'dart:async';
import 'dart:io';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import 'fcm_topic_name.dart';
import 'notifications_api_service.dart';

/// Optional FCM integration for topic push and token registration.
class PushNotificationService {
  PushNotificationService(this._apiService);

  static const enabled = bool.fromEnvironment('NEWSFLOW_ENABLE_PUSH');

  final NotificationsApiService _apiService;
  StreamSubscription<String>? _tokenRefreshSubscription;

  static Future<void> firebaseBackgroundHandler(RemoteMessage message) async {
    debugPrint('[push] background message: ${message.messageId}');
  }

  Future<void> initialize() async {
    if (!enabled || kIsWeb) {
      return;
    }

    try {
      FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);

      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission();
      debugPrint('[push] permission: ${settings.authorizationStatus}');

      final token = await messaging.getToken();
      if (token != null) {
        await _registerToken(token);
      }

      _tokenRefreshSubscription?.cancel();
      _tokenRefreshSubscription = messaging.onTokenRefresh.listen(_registerToken);
    } catch (error, stackTrace) {
      debugPrint('[push] initialize skipped: $error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }

  Future<void> dispose() async {
    await _tokenRefreshSubscription?.cancel();
    _tokenRefreshSubscription = null;
  }

  Future<void> syncTopicSubscriptions({
    required Iterable<String> topicIds,
    required bool pushEnabled,
  }) async {
    if (!enabled || kIsWeb) {
      return;
    }

    try {
      final messaging = FirebaseMessaging.instance;
      for (final topicId in topicIds) {
        final topicName = buildFcmTopicName(topicId);
        if (pushEnabled) {
          await messaging.subscribeToTopic(topicName);
        } else {
          await messaging.unsubscribeFromTopic(topicName);
        }
      }
    } catch (error, stackTrace) {
      debugPrint('[push] sync topics failed: $error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }

  Future<void> subscribeToTopic(String topicId) {
    return syncTopicSubscriptions(topicIds: [topicId], pushEnabled: true);
  }

  Future<void> unsubscribeFromTopic(String topicId) {
    return syncTopicSubscriptions(topicIds: [topicId], pushEnabled: false);
  }

  Future<void> _registerToken(String token) async {
    try {
      await _apiService.registerPushToken(
        token: token,
        platform: _platformName(),
      );
    } catch (error, stackTrace) {
      debugPrint('[push] token register failed: $error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }

  String _platformName() {
    if (kIsWeb) {
      return 'web';
    }
    if (Platform.isIOS) {
      return 'ios';
    }
    if (Platform.isAndroid) {
      return 'android';
    }
    return 'web';
  }
}
