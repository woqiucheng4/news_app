import 'package:flutter_test/flutter_test.dart';
import 'package:newsflow_frontend/core/analytics/analytics_related_events.dart';

void main() {
  group('isFeedRelatedAnalyticsEvent', () {
    test('matches feed_related_* events', () {
      expect(isFeedRelatedAnalyticsEvent('feed_related_impression'), isTrue);
      expect(isFeedRelatedAnalyticsEvent('feed_related_swipe'), isTrue);
      expect(isFeedRelatedAnalyticsEvent('feed_related_click'), isTrue);
      expect(isFeedRelatedAnalyticsEvent('feed_related_view_all'), isTrue);
    });

    test('matches feed_article_open from related article taps', () {
      expect(
        isFeedRelatedAnalyticsEvent(
          'feed_article_open',
          {'article_id': 'a-2', 'source': 'related_article'},
        ),
        isTrue,
      );
    });

    test('ignores unrelated events', () {
      expect(isFeedRelatedAnalyticsEvent('feed_refresh'), isFalse);
      expect(
        isFeedRelatedAnalyticsEvent(
          'feed_article_open',
          {'article_id': 'a-1', 'source': 'feed_list'},
        ),
        isFalse,
      );
    });
  });
}
