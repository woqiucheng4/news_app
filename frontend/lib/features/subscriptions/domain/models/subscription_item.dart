class SubscriptionItem {
  const SubscriptionItem({
    required this.topicId,
    required this.topicName,
    required this.topicCategory,
    required this.priority,
    required this.pushEnabled,
    required this.pushBreakingOnly,
    required this.isActive,
  });

  final String topicId;
  final String topicName;
  final String? topicCategory;
  final int priority;
  final bool pushEnabled;
  final bool pushBreakingOnly;
  final bool isActive;

  SubscriptionItem copyWith({
    int? priority,
    bool? pushEnabled,
    bool? pushBreakingOnly,
    bool? isActive,
  }) {
    return SubscriptionItem(
      topicId: topicId,
      topicName: topicName,
      topicCategory: topicCategory,
      priority: priority ?? this.priority,
      pushEnabled: pushEnabled ?? this.pushEnabled,
      pushBreakingOnly: pushBreakingOnly ?? this.pushBreakingOnly,
      isActive: isActive ?? this.isActive,
    );
  }

  factory SubscriptionItem.fromJson(Map<String, dynamic> json) {
    final topic = (json['topic'] as Map?)?.cast<String, dynamic>() ?? <String, dynamic>{};

    return SubscriptionItem(
      topicId: (topic['id'] ?? '') as String,
      topicName: (topic['name'] ?? '') as String,
      topicCategory: topic['category'] as String?,
      priority: (json['priority'] ?? 0) as int,
      pushEnabled: (json['push_enabled'] ?? false) as bool,
      pushBreakingOnly: (json['push_breaking_only'] ?? false) as bool,
      isActive: (json['is_active'] ?? true) as bool,
    );
  }
}
