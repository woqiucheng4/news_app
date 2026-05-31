import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../settings/presentation/providers/current_user_provider.dart';
import '../providers/billing_data_providers.dart';
import '../providers/entitlements_provider.dart';
import '../utils/freemium_error_mapper.dart';

class UpgradeScreen extends ConsumerStatefulWidget {
  const UpgradeScreen({super.key});

  @override
  ConsumerState<UpgradeScreen> createState() => _UpgradeScreenState();
}

class _UpgradeScreenState extends ConsumerState<UpgradeScreen> {
  bool _isVerifying = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final entitlementsAsync = ref.watch(entitlementsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.upgradeTitle),
      ),
      body: entitlementsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => _ErrorBody(
          message: mapApiError(error, l10n),
          onRetry: () => ref.invalidate(entitlementsProvider),
          l10n: l10n,
        ),
        data: (entitlements) {
          if (entitlements == null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(l10n.upgradeLoginRequired),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () => context.push('/login'),
                      child: Text(l10n.settingsSignInAction),
                    ),
                  ],
                ),
              ),
            );
          }

          if (entitlements.isPremium) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.verified_outlined,
                      size: 48,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      l10n.upgradeAlreadyPremium,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                l10n.upgradeHeadline,
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(
                l10n.upgradeDescription,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 24),
              _BenefitTile(
                icon: Icons.auto_awesome_outlined,
                title: l10n.upgradeBenefitDeepAnalysis,
              ),
              _BenefitTile(
                icon: Icons.bookmark_added_outlined,
                title: l10n.upgradeBenefitUnlimitedSubscriptions,
              ),
              _BenefitTile(
                icon: Icons.article_outlined,
                title: l10n.upgradeBenefitUnlimitedViews,
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l10n.upgradeUsageTitle,
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 12),
                      _UsageRow(
                        label: l10n.upgradeUsageTopics,
                        used: entitlements.topicSubscriptionsUsed,
                        limit: entitlements.maxTopicSubscriptions,
                      ),
                      const SizedBox(height: 8),
                      _UsageRow(
                        label: l10n.upgradeUsageDailyViews,
                        used: entitlements.dailyArticleViewsUsed,
                        limit: entitlements.dailyArticleViewsLimit,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              if (_errorMessage != null) ...[
                Text(
                  _errorMessage!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
                const SizedBox(height: 12),
              ],
              FilledButton(
                onPressed: _isVerifying ? null : () => _verifyDevPurchase(entitlements),
                child: _isVerifying
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(l10n.upgradeDevPurchaseAction),
              ),
              if (!kDebugMode) ...[
                const SizedBox(height: 8),
                Text(
                  l10n.upgradeStoreComingSoon,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ],
          );
        },
      ),
    );
  }

  Future<void> _verifyDevPurchase(entitlements) async {
    final l10n = AppLocalizations.of(context)!;
    setState(() {
      _isVerifying = true;
      _errorMessage = null;
    });

    try {
      final platform = Platform.isIOS ? 'ios' : 'android';
      final billing = ref.read(billingApiServiceProvider);
      await billing.verifyPurchase(
        platform: platform,
        productId: entitlements.premiumProductId,
        purchaseToken: 'dev_stub_token',
      );
      ref.invalidate(entitlementsProvider);
      ref.invalidate(currentUserProvider);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.upgradeSuccessMessage)),
      );
      context.pop();
    } catch (error) {
      setState(() {
        _errorMessage = mapApiError(error, l10n);
      });
    } finally {
      if (mounted) {
        setState(() => _isVerifying = false);
      }
    }
  }
}

class _BenefitTile extends StatelessWidget {
  const _BenefitTile({
    required this.icon,
    required this.title,
  });

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon),
      title: Text(title),
    );
  }
}

class _UsageRow extends StatelessWidget {
  const _UsageRow({
    required this.label,
    required this.used,
    required this.limit,
  });

  final String label;
  final int used;
  final int? limit;

  @override
  Widget build(BuildContext context) {
    final value = limit == null ? '$used' : '$used / $limit';
    return Row(
      children: [
        Expanded(child: Text(label)),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
        ),
      ],
    );
  }
}

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({
    required this.message,
    required this.onRetry,
    required this.l10n,
  });

  final String message;
  final VoidCallback onRetry;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: onRetry,
              child: Text(l10n.retryAction),
            ),
          ],
        ),
      ),
    );
  }
}
