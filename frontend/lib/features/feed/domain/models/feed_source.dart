class FeedSource {
  const FeedSource({
    this.id,
    this.name,
    this.url,
  });

  final String? id;
  final String? name;
  final String? url;

  factory FeedSource.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const FeedSource();
    }

    return FeedSource(
      id: json['id'] as String?,
      name: json['name'] as String?,
      url: json['url'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (url != null) 'url': url,
    };
  }
}
