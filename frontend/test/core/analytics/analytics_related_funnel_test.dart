import 'package:flutter_test/flutter_test.dart';
import 'package:newsflow_frontend/core/analytics/analytics_funnel.dart';

void main() {
  test('RelatedAnalyticsFunnel.fromJson parses related funnel payload', () {
    final funnel = RelatedAnalyticsFunnel.fromJson({
      'days': 7,
      'steps': {
        'impression': 10,
        'swipe': 4,
        'click': 3,
        'view_all': 1,
        'article_open': 2,
      },
      'conversion_rates': {
        'impression_to_click': 0.3,
        'impression_to_view_all': 0.1,
        'click_to_open': 0.6667,
      },
    });

    expect(funnel.impressionCount, 10);
    expect(funnel.clickCount, 3);
    expect(funnel.impressionToClick, 0.3);
    expect(funnel.clickToOpen, closeTo(0.6667, 0.0001));
  });
}
