import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../l10n/app_localizations.dart';
import '../providers/deep_analysis_provider.dart';
import '../providers/entitlements_provider.dart';
import '../utils/freemium_error_mapper.dart';

class DeepAnalysisSection extends ConsumerWidget {
  const DeepAnalysisSection({
    super.key,
    required this.articleId,
  });

  final String articleId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ProviderScope(
      overrides: [
        deepAnalysisScopeProvider.overrideWithValue(
          DeepAnalysisScope(articleId),
        ),
      ],
      child: _DeepAnalysisSectionContent(articleId: articleId),
    );
  }
}

class _DeepAnalysisSectionContent extends ConsumerWidget {
  const _DeepAnalysisSectionContent({required this.articleId});

  final String articleId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final entitlements = ref.watch(entitlementsProvider).value;
    final analysisState = ref.watch(deepAnalysisNotifierProvider);

    if (entitlements == null) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.deepAnalysisTitle,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        if (!entitlements.features.deepAnalysis)
          Card(
            child: ListTile(
              leading: const Icon(Icons.lock_outline),
              title: Text(l10n.deepAnalysisPremiumRequired),
              subtitle: Text(l10n.deepAnalysisPremiumHint),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/upgrade'),
            ),
          )
        else ...[
          OutlinedButton.icon(
            onPressed: analysisState.isLoading
                ? null
                : () => ref.read(deepAnalysisNotifierProvider.notifier).analyze(),
            icon: const Icon(Icons.auto_awesome_outlined),
            label: Text(l10n.deepAnalysisGenerateAction),
          ),
          analysisState.when(
            loading: () => const Padding(
              padding: EdgeInsets.only(top: 12),
              child: LinearProgressIndicator(),
            ),
            error: (error, _) {
              final freemiumError = parseFreemiumError(error);
              final message = mapFreemiumError(error, l10n);
              return Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      message,
                      style: TextStyle(color: Theme.of(context).colorScheme.error),
                    ),
                    if (freemiumError?.shouldOfferUpgrade ?? false) ...[
                      const SizedBox(height: 8),
                      TextButton(
                        onPressed: () => context.push('/upgrade'),
                        child: Text(l10n.upgradeAction),
                      ),
                    ],
                  ],
                ),
              );
            },
            data: (result) {
              if (result == null || (result.analysis ?? '').trim().isEmpty) {
                return const SizedBox.shrink();
              }
              return Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      result.analysis!,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ],
    );
  }
}
