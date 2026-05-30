import 'package:newsflow_frontend/core/analytics/analytics_event_sanitizer.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const sanitizer = AnalyticsEventSanitizer();

  group('feed_related events', () {
    test('sanitizes feed_related_click', () {
      final result = sanitizer.sanitize(
        eventName: 'feed_related_click',
        params: {
          'article_id': 'parent-1',
          'related_article_id': 'rel-1',
          'source': 'detail_section',
          'unexpected': 'drop-me',
        },
      );

      expect(result, {
        'article_id': 'parent-1',
        'related_article_id': 'rel-1',
        'source': 'detail_section',
      });
    });

    test('sanitizes feed_related_swipe', () {
      final result = sanitizer.sanitize(
        eventName: 'feed_related_swipe',
        params: {
          'article_id': 'parent-1',
          'source': 'related_sheet',
          'scroll_offset': 120,
          'max_scroll_extent': 480,
        },
      );

      expect(result['scroll_offset'], 120);
      expect(result['max_scroll_extent'], 480);
    });

    test('rejects unknown feed_related event names', () {
      final result = sanitizer.sanitize(
        eventName: 'feed_related_unknown',
        params: {'article_id': 'a-1'},
      );

      expect(result, isEmpty);
    });
  });
}
