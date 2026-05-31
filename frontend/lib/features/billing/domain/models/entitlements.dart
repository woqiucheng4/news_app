class EntitlementFeatures {
  const EntitlementFeatures({
    required this.deepAnalysis,
    required this.priorityPush,
    required this.unlimitedSubscriptions,
  });

  final bool deepAnalysis;
  final bool priorityPush;
  final bool unlimitedSubscriptions;

  factory EntitlementFeatures.fromJson(Map<String, dynamic> json) {
    return EntitlementFeatures(
      deepAnalysis: (json['deep_analysis'] ?? false) as bool,
      priorityPush: (json['priority_push'] ?? false) as bool,
      unlimitedSubscriptions: (json['unlimited_subscriptions'] ?? false) as bool,
    );
  }
}

class Entitlements {
  const Entitlements({
    required this.isPremium,
    required this.maxTopicSubscriptions,
    required this.topicSubscriptionsUsed,
    required this.dailyArticleViewsLimit,
    required this.dailyArticleViewsUsed,
    required this.canSubscribeMore,
    required this.canViewArticles,
    required this.features,
    required this.premiumProductId,
  });

  final bool isPremium;
  final int? maxTopicSubscriptions;
  final int topicSubscriptionsUsed;
  final int? dailyArticleViewsLimit;
  final int dailyArticleViewsUsed;
  final bool canSubscribeMore;
  final bool canViewArticles;
  final EntitlementFeatures features;
  final String premiumProductId;

  factory Entitlements.fromJson(Map<String, dynamic> json) {
    return Entitlements(
      isPremium: (json['is_premium'] ?? false) as bool,
      maxTopicSubscriptions: json['max_topic_subscriptions'] as int?,
      topicSubscriptionsUsed: (json['topic_subscriptions_used'] ?? 0) as int,
      dailyArticleViewsLimit: json['daily_article_views_limit'] as int?,
      dailyArticleViewsUsed: (json['daily_article_views_used'] ?? 0) as int,
      canSubscribeMore: (json['can_subscribe_more'] ?? true) as bool,
      canViewArticles: (json['can_view_articles'] ?? true) as bool,
      features: EntitlementFeatures.fromJson(
        (json['features'] as Map<String, dynamic>?) ?? const {},
      ),
      premiumProductId: (json['premium_product_id'] ?? '') as String,
    );
  }
}
