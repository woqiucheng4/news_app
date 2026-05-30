/// Identifies analytics events that belong to the related-articles funnel.
bool isFeedRelatedAnalyticsEvent(
  String eventName, [
  Map<String, Object>? params,
]) {
  if (eventName.startsWith('feed_related_')) {
    return true;
  }

  return eventName == 'feed_article_open' &&
      params?['source'] == 'related_article';
}
