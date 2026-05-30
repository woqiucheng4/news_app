class AnalyticsFunnel {
  const AnalyticsFunnel({
    required this.days,
    required this.searchCount,
    required this.categorySelectCount,
    required this.subscribeAttempts,
    required this.subscribeSuccess,
    required this.searchToSubscribeAttempt,
    required this.subscribeAttemptToSuccess,
  });

  final int days;
  final int searchCount;
  final int categorySelectCount;
  final int subscribeAttempts;
  final int subscribeSuccess;
  final double? searchToSubscribeAttempt;
  final double? subscribeAttemptToSuccess;

  factory AnalyticsFunnel.fromJson(Map<String, dynamic> json) {
    final steps = (json['steps'] as Map?)?.cast<String, dynamic>() ?? const {};
    final rates =
        (json['conversion_rates'] as Map?)?.cast<String, dynamic>() ?? const {};

    double? readRate(Object? value) {
      if (value is num) {
        return value.toDouble();
      }
      return null;
    }

    return AnalyticsFunnel(
      days: (json['days'] as num?)?.toInt() ?? 7,
      searchCount: (steps['search'] as num?)?.toInt() ?? 0,
      categorySelectCount: (steps['category_select'] as num?)?.toInt() ?? 0,
      subscribeAttempts: (steps['subscribe_attempts'] as num?)?.toInt() ?? 0,
      subscribeSuccess: (steps['subscribe_success'] as num?)?.toInt() ?? 0,
      searchToSubscribeAttempt:
          readRate(rates['search_to_subscribe_attempt']),
      subscribeAttemptToSuccess:
          readRate(rates['subscribe_attempt_to_success']),
    );
  }
}

class AnalyticsInsights {
  const AnalyticsInsights({
    required this.userFunnel,
    required this.sessionFunnel,
    required this.userRelatedFunnel,
    required this.sessionRelatedFunnel,
    required this.sessionId,
  });

  final AnalyticsFunnel userFunnel;
  final AnalyticsFunnel sessionFunnel;
  final RelatedAnalyticsFunnel userRelatedFunnel;
  final RelatedAnalyticsFunnel sessionRelatedFunnel;
  final String sessionId;
}

class RelatedAnalyticsFunnel {
  const RelatedAnalyticsFunnel({
    required this.days,
    required this.impressionCount,
    required this.swipeCount,
    required this.clickCount,
    required this.viewAllCount,
    required this.articleOpenCount,
    required this.impressionToClick,
    required this.impressionToViewAll,
    required this.clickToOpen,
  });

  final int days;
  final int impressionCount;
  final int swipeCount;
  final int clickCount;
  final int viewAllCount;
  final int articleOpenCount;
  final double? impressionToClick;
  final double? impressionToViewAll;
  final double? clickToOpen;

  factory RelatedAnalyticsFunnel.fromJson(Map<String, dynamic> json) {
    final steps = (json['steps'] as Map?)?.cast<String, dynamic>() ?? const {};
    final rates =
        (json['conversion_rates'] as Map?)?.cast<String, dynamic>() ?? const {};

    double? readRate(Object? value) {
      if (value is num) {
        return value.toDouble();
      }
      return null;
    }

    return RelatedAnalyticsFunnel(
      days: (json['days'] as num?)?.toInt() ?? 7,
      impressionCount: (steps['impression'] as num?)?.toInt() ?? 0,
      swipeCount: (steps['swipe'] as num?)?.toInt() ?? 0,
      clickCount: (steps['click'] as num?)?.toInt() ?? 0,
      viewAllCount: (steps['view_all'] as num?)?.toInt() ?? 0,
      articleOpenCount: (steps['article_open'] as num?)?.toInt() ?? 0,
      impressionToClick: readRate(rates['impression_to_click']),
      impressionToViewAll: readRate(rates['impression_to_view_all']),
      clickToOpen: readRate(rates['click_to_open']),
    );
  }
}
