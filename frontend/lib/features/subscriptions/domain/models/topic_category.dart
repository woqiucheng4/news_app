class TopicCategory {
  const TopicCategory({
    required this.name,
    required this.topicCount,
  });

  final String name;
  final int topicCount;

  factory TopicCategory.fromJson(Map<String, dynamic> json) {
    return TopicCategory(
      name: (json['name'] ?? '') as String,
      topicCount: (json['topic_count'] ?? 0) as int,
    );
  }
}
