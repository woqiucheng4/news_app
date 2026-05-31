import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/models/deep_analysis_result.dart';
import 'billing_data_providers.dart';

class DeepAnalysisScope {
  const DeepAnalysisScope(this.articleId);

  final String articleId;
}

final deepAnalysisScopeProvider = Provider<DeepAnalysisScope>((ref) {
  throw UnimplementedError(
    'Override deepAnalysisScopeProvider in DeepAnalysisSection',
  );
});

final deepAnalysisNotifierProvider =
    AsyncNotifierProvider<DeepAnalysisNotifier, DeepAnalysisResult?>(
  DeepAnalysisNotifier.new,
);

class DeepAnalysisNotifier extends AsyncNotifier<DeepAnalysisResult?> {
  String get _articleId => ref.watch(deepAnalysisScopeProvider).articleId;

  @override
  Future<DeepAnalysisResult?> build() async {
    return null;
  }

  Future<void> analyze() async {
    state = const AsyncLoading<DeepAnalysisResult?>().copyWithPrevious(state);
    state = await AsyncValue.guard(() async {
      final api = ref.read(deepAnalysisApiServiceProvider);
      return api.analyzeArticle(_articleId);
    });
  }
}
