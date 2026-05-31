import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:go_router/go_router.dart';

/// Navigate based on FCM payload data.
void handlePushNavigation(GoRouter router, RemoteMessage message) {
  final data = message.data;
  final type = data['notification_type'];
  final articleId = data['article_id'];

  if (type == 'daily_briefing') {
    router.go('/feed');
    return;
  }

  if (articleId != null && articleId.isNotEmpty) {
    router.push('/feed/article/$articleId');
  }
}
