import 'dart:async';

import 'package:flutter/foundation.dart';

import 'analytics_backend.dart';
import 'analytics_event_sanitizer.dart';

class DiscoveryAnalytics {
  const DiscoveryAnalytics({
    required DiscoveryAnalyticsAdapter adapter,
  }) : _adapter = adapter;

  final DiscoveryAnalyticsAdapter _adapter;

  void trackEvent({
    required String eventName,
    required Map<String, Object?> params,
  }) {
    _adapter.track(eventName: eventName, params: params);
  }

  void trackSearchSubmitted({
    required String query,
    required String source,
    required String? category,
  }) {
    trackEvent(
      eventName: 'discover_search',
      params: {
        'query': query,
        'source': source,
        'category': category ?? '',
      },
    );
  }

  void trackCategorySelected({
    required String category,
    required String source,
  }) {
    trackEvent(
      eventName: 'discover_category_select',
      params: {
        'category': category,
        'source': source,
      },
    );
  }

  void trackTopicSubscribe({
    required String topicId,
    required bool success,
  }) {
    trackEvent(
      eventName: 'discover_topic_subscribe',
      params: {
        'topic_id': topicId,
        'success': success,
      },
    );
  }

  void trackKeywordSubscribe({
    required String keyword,
    required bool success,
  }) {
    trackEvent(
      eventName: 'discover_keyword_subscribe',
      params: {
        'keyword': keyword,
        'success': success,
      },
    );
  }

  void trackRecentSearchDeleted({
    required String query,
  }) {
    trackEvent(
      eventName: 'discover_recent_search_delete',
      params: {
        'query': query,
      },
    );
  }

  void trackRecentSearchesCleared({
    required int previousCount,
  }) {
    trackEvent(
      eventName: 'discover_recent_searches_clear',
      params: {
        'previous_count': previousCount,
      },
    );
  }

  void trackFeedRefresh({required String source}) {
    trackEvent(
      eventName: 'feed_refresh',
      params: {'source': source},
    );
  }

  void trackFeedArticleOpen({
    required String articleId,
    required String source,
  }) {
    trackEvent(
      eventName: 'feed_article_open',
      params: {
        'article_id': articleId,
        'source': source,
      },
    );
  }

  void trackFeedRelatedImpression({
    required String articleId,
    required int visibleCount,
    required int totalCount,
    required String source,
    required String displayState,
  }) {
    trackEvent(
      eventName: 'feed_related_impression',
      params: {
        'article_id': articleId,
        'visible_count': visibleCount,
        'total_count': totalCount,
        'source': source,
        'display_state': displayState,
      },
    );
  }

  void trackFeedRelatedViewAll({
    required String articleId,
    required int totalCount,
  }) {
    trackEvent(
      eventName: 'feed_related_view_all',
      params: {
        'article_id': articleId,
        'total_count': totalCount,
      },
    );
  }

  void trackFeedRelatedSwipe({
    required String articleId,
    required String source,
    required int scrollOffset,
    required int maxScrollExtent,
  }) {
    trackEvent(
      eventName: 'feed_related_swipe',
      params: {
        'article_id': articleId,
        'source': source,
        'scroll_offset': scrollOffset,
        'max_scroll_extent': maxScrollExtent,
      },
    );
  }

  void trackFeedRelatedClick({
    required String articleId,
    required String relatedArticleId,
    required String source,
  }) {
    trackEvent(
      eventName: 'feed_related_click',
      params: {
        'article_id': articleId,
        'related_article_id': relatedArticleId,
        'source': source,
      },
    );
  }

  void trackSubscriptionPushToggle({
    required String topicId,
    required bool enabled,
    required bool success,
  }) {
    trackEvent(
      eventName: 'subscription_push_toggle',
      params: {
        'topic_id': topicId,
        'enabled': enabled,
        'success': success,
      },
    );
  }

  void trackSubscriptionUnsubscribe({
    required String topicId,
    required bool success,
  }) {
    trackEvent(
      eventName: 'subscription_unsubscribe',
      params: {
        'topic_id': topicId,
        'success': success,
      },
    );
  }

  void trackSubscriptionListRefresh({required String source}) {
    trackEvent(
      eventName: 'subscription_list_refresh',
      params: {'source': source},
    );
  }
}

/// Alias for app-wide analytics tracker.
typedef AppAnalytics = DiscoveryAnalytics;

abstract class DiscoveryAnalyticsAdapter {
  const DiscoveryAnalyticsAdapter({
    required this.sanitizer,
  });

  final AnalyticsEventSanitizer sanitizer;

  void track({
    required String eventName,
    required Map<String, Object?> params,
  }) {
    final sanitized = sanitizer.sanitize(eventName: eventName, params: params);
    if (sanitized.isEmpty) return;
    emit(eventName: eventName, params: sanitized);
  }

  void emit({
    required String eventName,
    required Map<String, Object> params,
  });
}

class DebugDiscoveryAnalyticsAdapter extends DiscoveryAnalyticsAdapter {
  const DebugDiscoveryAnalyticsAdapter({
    required super.sanitizer,
  });

  @override
  void emit({
    required String eventName,
    required Map<String, Object> params,
  }) {
    debugPrint('[analytics][$eventName] $params');
  }
}

class ProductionDiscoveryAnalyticsAdapter extends DiscoveryAnalyticsAdapter {
  const ProductionDiscoveryAnalyticsAdapter({
    required super.sanitizer,
    required AnalyticsBackend backend,
  }) : _backend = backend;

  final AnalyticsBackend _backend;

  @override
  void emit({
    required String eventName,
    required Map<String, Object> params,
  }) {
    unawaited(_backend.send(eventName: eventName, params: params));
  }
}

class LoggingDiscoveryAnalyticsAdapter extends DiscoveryAnalyticsAdapter {
  const LoggingDiscoveryAnalyticsAdapter({
    required super.sanitizer,
    required DiscoveryAnalyticsAdapter delegate,
    required bool Function() isEnabled,
    required void Function(String eventName, Map<String, Object> params) onLogged,
  })  : _delegate = delegate,
        _isEnabled = isEnabled,
        _onLogged = onLogged;

  final DiscoveryAnalyticsAdapter _delegate;
  final bool Function() _isEnabled;
  final void Function(String eventName, Map<String, Object> params) _onLogged;

  @override
  void track({
    required String eventName,
    required Map<String, Object?> params,
  }) {
    final sanitized = sanitizer.sanitize(eventName: eventName, params: params);
    if (sanitized.isEmpty) {
      return;
    }

    _onLogged(eventName, sanitized);
    if (!_isEnabled()) {
      return;
    }

    _delegate.emit(eventName: eventName, params: sanitized);
  }
}
