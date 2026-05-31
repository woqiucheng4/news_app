import 'package:dio/dio.dart';

import '../../domain/models/deep_analysis_result.dart';

class DeepAnalysisApiService {
  DeepAnalysisApiService(this._dio);

  final Dio _dio;

  Future<DeepAnalysisResult> analyzeArticle(String articleId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/articles/$articleId/deep-analysis',
    );
    return DeepAnalysisResult.fromJson(response.data ?? const {});
  }
}
