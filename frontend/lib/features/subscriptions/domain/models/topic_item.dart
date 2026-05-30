class TopicItem {
  const TopicItem({
    required this.id,
    required this.name,
    required this.slug,
    required this.subscriberCount,
    required this.isSubscribed,
    this.description,
    this.category,
  });

  final String id;
  final String name;
  final String slug;
  final String? description;
  final String? category;
  final int subscriberCount;
  final bool isSubscribed;

  TopicItem copyWith({
    int? subscriberCount,
    bool? isSubscribed,
  }) {
    return TopicItem(
      id: id,
      name: name,
      slug: slug,
      description: description,
      category: category,
      subscriberCount: subscriberCount ?? this.subscriberCount,
      isSubscribed: isSubscribed ?? this.isSubscribed,
    );
  }

  factory TopicItem.fromJson(Map<String, dynamic> json) {
    return TopicItem(
      id: (json['id'] ?? '') as String,
      name: (json['name'] ?? '') as String,
      slug: (json['slug'] ?? '') as String,
      description: json['description'] as String?,
      category: json['category'] as String?,
      subscriberCount: (json['subscriber_count'] ?? 0) as int,
      isSubscribed: (json['is_subscribed'] ?? false) as bool,
    );
  }
}
