class DeepAnalysisResult {
  const DeepAnalysisResult({
    required this.found,
    this.articleId,
    this.model,
    this.analysis,
  });

  final bool found;
  final String? articleId;
  final String? model;
  final String? analysis;

  factory DeepAnalysisResult.fromJson(Map<String, dynamic> json) {
    return DeepAnalysisResult(
      found: (json['found'] ?? false) as bool,
      articleId: json['article_id'] as String?,
      model: json['model'] as String?,
      analysis: json['analysis'] as String?,
    );
  }
}
