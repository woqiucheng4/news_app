import 'dart:convert';

/// Whitelist and redact analytics params before they leave the client.
class AnalyticsEventSanitizer {
  const AnalyticsEventSanitizer({
    this.redactSearchTerms = false,
    this.maxStringLength = 48,
  });

  final bool redactSearchTerms;
  final int maxStringLength;

  static const allowedParamsByEvent = <String, Set<String>>{
    'discover_search': {'query', 'source', 'category'},
    'discover_category_select': {'category', 'source'},
    'discover_topic_subscribe': {'topic_id', 'success'},
    'discover_keyword_subscribe': {'keyword', 'success'},
    'discover_recent_search_delete': {'query'},
    'discover_recent_searches_clear': {'previous_count'},
    'feed_refresh': {'source'},
    'feed_article_open': {'article_id', 'source'},
    'feed_related_impression': {
      'article_id',
      'visible_count',
      'total_count',
      'source',
      'display_state',
    },
    'feed_related_view_all': {'article_id', 'total_count'},
    'feed_related_swipe': {
      'article_id',
      'source',
      'scroll_offset',
      'max_scroll_extent',
    },
    'feed_related_click': {
      'article_id',
      'related_article_id',
      'source',
    },
    'subscription_push_toggle': {'topic_id', 'enabled', 'success'},
    'subscription_unsubscribe': {'topic_id', 'success'},
    'subscription_list_refresh': {'source'},
  };

  Map<String, Object> sanitize({
    required String eventName,
    required Map<String, Object?> params,
  }) {
    final allowed = allowedParamsByEvent[eventName];
    if (allowed == null) {
      return const {};
    }

    final sanitized = <String, Object>{};
    for (final key in allowed) {
      final value = params[key];
      if (value == null) continue;

      if (value is bool || value is int || value is double) {
        sanitized[key] = value;
        continue;
      }

      if (value is String) {
        sanitized[key] = _sanitizeString(key, value);
      }
    }

    return sanitized;
  }

  String _sanitizeString(String key, String value) {
    final normalized = value.trim().replaceAll(RegExp(r'[\x00-\x1F\x7F]'), '');
    if (normalized.isEmpty) return '';

    if (_isSearchLikeKey(key) && redactSearchTerms) {
      return _fingerprint(normalized);
    }

    if (normalized.length <= maxStringLength) {
      return normalized;
    }
    return '${normalized.substring(0, maxStringLength)}…';
  }

  bool _isSearchLikeKey(String key) {
    return key == 'query' || key == 'keyword';
  }

  String _fingerprint(String input) {
    final encoded = base64Url.encode(utf8.encode(input.toLowerCase()));
    return encoded.length <= 12 ? encoded : encoded.substring(0, 12);
  }
}
