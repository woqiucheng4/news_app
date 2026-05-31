import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/utils/external_url_launcher.dart';
import '../../../../core/analytics/analytics_related_events.dart';
import '../../../../core/analytics/analytics_funnel.dart';
import '../../../../core/analytics/analytics_insights_provider.dart';
import '../../../../core/analytics/analytics_preferences_provider.dart';
import '../../../../core/analytics/analytics_session_provider.dart';
import '../../../../core/auth/auth_token_provider.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/theme_mode_provider.dart';
import '../../../feed/presentation/providers/feed_local_cache.dart';
import '../../../feed/presentation/providers/feed_notifier.dart';
import '../../../billing/presentation/providers/entitlements_provider.dart';
import '../providers/current_user_provider.dart';
import '../../../../l10n/app_localizations.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final analyticsEnabled = ref.watch(analyticsEnabledProvider);
    final insights = ref.watch(analyticsInsightsProvider);
    final sessionId = ref.watch(analyticsSessionIdProvider);
    final hasToken = ref.watch(accessTokenValueProvider).trim().isNotEmpty;
    final tokenLockedByEnv = ref.watch(accessTokenLockedByEnvProvider);
    final themeModeAsync = ref.watch(themeModeProvider);
    final themeMode = themeModeAsync.value ?? ThemeMode.system;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          l10n.settingsHeadline,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        Text(
          l10n.settingsDescription,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 24),
        Text(
          l10n.settingsAccountSectionTitle,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        if (!hasToken)
          Card(
            child: ListTile(
              title: Text(l10n.settingsSignInAction),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/login'),
            ),
          )
        else
          ref.watch(currentUserProvider).when(
                loading: () => Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        const SizedBox(width: 12),
                        Text(l10n.analyticsInsightsLoading),
                      ],
                    ),
                  ),
                ),
                error: (_, __) => Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            l10n.settingsAccountLoadFailed,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ),
                        TextButton(
                          onPressed: () => ref.invalidate(currentUserProvider),
                          child: Text(l10n.retryAction),
                        ),
                      ],
                    ),
                  ),
                ),
                data: (user) {
                  if (user == null) {
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(l10n.settingsAccountLoginRequired),
                      ),
                    );
                  }

                  final yesNo = (bool value) =>
                      value ? l10n.settingsAccountYes : l10n.settingsAccountNo;

                  return Card(
                    child: Column(
                      children: [
                        ListTile(
                          title: Text(l10n.settingsAccountEmail),
                          subtitle: Text(user.email),
                        ),
                        if (user.displayName != null &&
                            user.displayName!.trim().isNotEmpty) ...[
                          const Divider(height: 1),
                          ListTile(
                            title: Text(l10n.settingsAccountDisplayName),
                            subtitle: Text(user.displayName!),
                          ),
                        ],
                        const Divider(height: 1),
                        ListTile(
                          title: Text(l10n.settingsAccountPremium),
                          subtitle: Text(yesNo(user.isPremium)),
                          trailing: user.isPremium
                              ? null
                              : const Icon(Icons.chevron_right),
                          onTap: user.isPremium
                              ? null
                              : () => context.push('/upgrade'),
                        ),
                        if (user.isAdmin) ...[
                          const Divider(height: 1),
                          ListTile(
                            title: Text(l10n.settingsAccountAdmin),
                            subtitle: Text(l10n.settingsAccountYes),
                          ),
                        ],
                      ],
                    ),
                  );
                },
              ),
        if (hasToken) ...[
          const SizedBox(height: 8),
          ref.watch(entitlementsProvider).when(
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
                data: (entitlements) {
                  if (entitlements == null || entitlements.isPremium) {
                    return const SizedBox.shrink();
                  }

                  String formatUsage(int used, int? limit) {
                    if (limit == null) {
                      return l10n.settingsEntitlementsUnlimited;
                    }
                    return l10n.settingsEntitlementsUsage(used, limit);
                  }

                  return Card(
                    child: Column(
                      children: [
                        ListTile(
                          title: Text(l10n.upgradeUsageTitle),
                          subtitle: Text(l10n.upgradeDescription),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => context.push('/upgrade'),
                        ),
                        const Divider(height: 1),
                        ListTile(
                          title: Text(l10n.upgradeUsageTopics),
                          subtitle: Text(
                            formatUsage(
                              entitlements.topicSubscriptionsUsed,
                              entitlements.maxTopicSubscriptions,
                            ),
                          ),
                        ),
                        const Divider(height: 1),
                        ListTile(
                          title: Text(l10n.upgradeUsageDailyViews),
                          subtitle: Text(
                            formatUsage(
                              entitlements.dailyArticleViewsUsed,
                              entitlements.dailyArticleViewsLimit,
                            ),
                          ),
                        ),
                        const Divider(height: 1),
                        ListTile(
                          title: Text(l10n.settingsUpgradeAction),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => context.push('/upgrade'),
                        ),
                      ],
                    ),
                  );
                },
              ),
          const SizedBox(height: 8),
          Card(
            child: ListTile(
              title: Text(
                l10n.settingsSignOutAction,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
              subtitle: tokenLockedByEnv
                  ? Text(l10n.settingsSignOutEnvLocked)
                  : null,
              enabled: !tokenLockedByEnv,
                  onTap: tokenLockedByEnv
                  ? null
                  : () async {
                      await ref.read(accessTokenProvider.notifier).logout();
                      await ref.read(clearFeedLocalCachesProvider)();
                      ref.invalidate(currentUserProvider);
                      ref.invalidate(analyticsInsightsProvider);
                      ref.invalidate(feedNotifierProvider);
                    },
            ),
          ),
        ],
        const SizedBox(height: 24),
        Text(
          l10n.settingsAppearanceSectionTitle,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Card(
          child: ListTile(
            title: Text(l10n.settingsThemeTitle),
            trailing: DropdownButton<ThemeMode>(
              value: themeMode,
              underline: const SizedBox.shrink(),
              onChanged: themeModeAsync.isLoading
                  ? null
                  : (mode) {
                      if (mode == null) {
                        return;
                      }
                      ref.read(themeModeProvider.notifier).setThemeMode(mode);
                    },
              items: [
                DropdownMenuItem(
                  value: ThemeMode.system,
                  child: Text(l10n.settingsThemeSystem),
                ),
                DropdownMenuItem(
                  value: ThemeMode.light,
                  child: Text(l10n.settingsThemeLight),
                ),
                DropdownMenuItem(
                  value: ThemeMode.dark,
                  child: Text(l10n.settingsThemeDark),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          l10n.settingsLegalSectionTitle,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Card(
          child: ListTile(
            title: Text(l10n.settingsPrivacyPolicyAction),
            subtitle: Text(l10n.settingsPrivacyPolicyDescription),
            trailing: const Icon(Icons.open_in_new),
            onTap: () async {
              final launched =
                  await launchExternalUrl(AppConstants.privacyPolicyUrl);
              if (!launched && context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(l10n.feedOpenLinkFailed)),
                );
              }
            },
          ),
        ),
        const SizedBox(height: 24),
        Text(
          l10n.analyticsSectionTitle,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Card(
          child: Column(
            children: [
              SwitchListTile(
                title: Text(l10n.analyticsEnabledTitle),
                subtitle: Text(l10n.analyticsEnabledDescription),
                value: analyticsEnabled.value ?? true,
                onChanged: analyticsEnabled.isLoading
                    ? null
                    : (value) {
                        ref
                            .read(analyticsEnabledProvider.notifier)
                            .setEnabled(value);
                      },
              ),
              const Divider(height: 1),
              ListTile(
                title: Text(l10n.analyticsAdapterTitle),
                subtitle: Text(AppConstants.analyticsAdapter),
              ),
              ListTile(
                title: Text(l10n.analyticsTransportTitle),
                subtitle: Text(AppConstants.analyticsTransport),
              ),
              sessionId.when(
                data: (value) => ListTile(
                  title: Text(l10n.analyticsSessionIdTitle),
                  subtitle: Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                loading: () => ListTile(
                  title: Text(l10n.analyticsSessionIdTitle),
                  subtitle: Text(l10n.analyticsInsightsLoading),
                ),
                error: (_, __) => const SizedBox.shrink(),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          l10n.analyticsFunnelTitle,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        if (!hasToken)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                l10n.analyticsFunnelLoginRequired,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          )
        else
          insights.when(
            loading: () => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 12),
                    Text(l10n.analyticsInsightsLoading),
                  ],
                ),
              ),
            ),
            error: (_, __) => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        l10n.analyticsInsightsLoadFailed,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                    TextButton(
                      onPressed: () => ref.invalidate(analyticsInsightsProvider),
                      child: Text(l10n.retryAction),
                    ),
                  ],
                ),
              ),
            ),
            data: (value) {
              if (value == null) {
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(l10n.analyticsFunnelLoginRequired),
                  ),
                );
              }

              return Column(
                children: [
                  _FunnelCard(
                    title: l10n.analyticsFunnelUserScope,
                    funnel: value.userFunnel,
                    formatRate: _formatRate,
                    l10n: l10n,
                  ),
                  const SizedBox(height: 8),
                  _FunnelCard(
                    title: l10n.analyticsFunnelSessionScope,
                    funnel: value.sessionFunnel,
                    formatRate: _formatRate,
                    l10n: l10n,
                  ),
                ],
              );
            },
          ),
        const SizedBox(height: 16),
        Text(
          l10n.analyticsRelatedFunnelTitle,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        if (!hasToken)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                l10n.analyticsFunnelLoginRequired,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          )
        else
          insights.when(
            loading: () => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 12),
                    Text(l10n.analyticsInsightsLoading),
                  ],
                ),
              ),
            ),
            error: (_, __) => const SizedBox.shrink(),
            data: (value) {
              if (value == null) {
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(l10n.analyticsFunnelLoginRequired),
                  ),
                );
              }

              return Column(
                children: [
                  _RelatedFunnelCard(
                    title: l10n.analyticsFunnelUserScope,
                    funnel: value.userRelatedFunnel,
                    formatRate: _formatRate,
                    l10n: l10n,
                  ),
                  const SizedBox(height: 8),
                  _RelatedFunnelCard(
                    title: l10n.analyticsFunnelSessionScope,
                    funnel: value.sessionRelatedFunnel,
                    formatRate: _formatRate,
                    l10n: l10n,
                  ),
                ],
              );
            },
          ),
        const SizedBox(height: 16),
        const _AnalyticsDebugLogSection(),
      ],
    );
  }

  static String _formatRate(double? rate) {
    if (rate == null) {
      return '—';
    }
    return '${(rate * 100).toStringAsFixed(1)}%';
  }
}

class _FunnelCard extends StatelessWidget {
  const _FunnelCard({
    required this.title,
    required this.funnel,
    required this.formatRate,
    required this.l10n,
  });

  final String title;
  final AnalyticsFunnel funnel;
  final String Function(double? rate) formatRate;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            _MetricRow(label: l10n.analyticsFunnelSearch, value: '${funnel.searchCount}'),
            _MetricRow(
              label: l10n.analyticsFunnelSubscribeAttempts,
              value: '${funnel.subscribeAttempts}',
            ),
            _MetricRow(
              label: l10n.analyticsFunnelSubscribeSuccess,
              value: '${funnel.subscribeSuccess}',
            ),
            _MetricRow(
              label: l10n.analyticsFunnelSearchToSubscribe,
              value: formatRate(funnel.searchToSubscribeAttempt),
            ),
            _MetricRow(
              label: l10n.analyticsFunnelAttemptToSuccess,
              value: formatRate(funnel.subscribeAttemptToSuccess),
            ),
          ],
        ),
      ),
    );
  }
}

class _RelatedFunnelCard extends StatelessWidget {
  const _RelatedFunnelCard({
    required this.title,
    required this.funnel,
    required this.formatRate,
    required this.l10n,
  });

  final String title;
  final RelatedAnalyticsFunnel funnel;
  final String Function(double? rate) formatRate;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelImpression,
              value: '${funnel.impressionCount}',
            ),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelSwipe,
              value: '${funnel.swipeCount}',
            ),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelClick,
              value: '${funnel.clickCount}',
            ),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelViewAll,
              value: '${funnel.viewAllCount}',
            ),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelArticleOpen,
              value: '${funnel.articleOpenCount}',
            ),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelImpressionToClick,
              value: formatRate(funnel.impressionToClick),
            ),
            _MetricRow(
              label: l10n.analyticsRelatedFunnelClickToOpen,
              value: formatRate(funnel.clickToOpen),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  const _MetricRow({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
          ),
        ],
      ),
    );
  }
}

enum _AnalyticsDebugLogFilter { all, feedRelated }

class _AnalyticsDebugLogSection extends ConsumerStatefulWidget {
  const _AnalyticsDebugLogSection();

  @override
  ConsumerState<_AnalyticsDebugLogSection> createState() =>
      _AnalyticsDebugLogSectionState();
}

class _AnalyticsDebugLogSectionState
    extends ConsumerState<_AnalyticsDebugLogSection> {
  _AnalyticsDebugLogFilter _filter = _AnalyticsDebugLogFilter.all;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final debugLog = ref.watch(analyticsDebugLogProvider);
    final timeFormat = DateFormat.Hms();
    final colorScheme = Theme.of(context).colorScheme;

    final visibleEntries = switch (_filter) {
      _AnalyticsDebugLogFilter.all => debugLog,
      _AnalyticsDebugLogFilter.feedRelated => debugLog
          .where(
            (entry) => isFeedRelatedAnalyticsEvent(
              entry.eventName,
              entry.params,
            ),
          )
          .toList(growable: false),
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                l10n.analyticsDebugLogTitle,
                style: Theme.of(context).textTheme.titleSmall,
              ),
            ),
            if (debugLog.isNotEmpty)
              TextButton(
                onPressed: () {
                  ref.read(analyticsDebugLogProvider.notifier).clear();
                },
                child: Text(l10n.analyticsClearLogAction),
              ),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: [
            FilterChip(
              label: Text(l10n.analyticsDebugLogFilterAll),
              selected: _filter == _AnalyticsDebugLogFilter.all,
              onSelected: (_) {
                setState(() => _filter = _AnalyticsDebugLogFilter.all);
              },
            ),
            FilterChip(
              label: Text(l10n.analyticsDebugLogFilterRelated),
              selected: _filter == _AnalyticsDebugLogFilter.feedRelated,
              onSelected: (_) {
                setState(() => _filter = _AnalyticsDebugLogFilter.feedRelated);
              },
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (debugLog.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                l10n.analyticsDebugLogEmpty,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          )
        else if (visibleEntries.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                l10n.analyticsDebugLogFilterEmpty,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          )
        else
          ...visibleEntries.map((entry) {
            final isRelated = isFeedRelatedAnalyticsEvent(
              entry.eventName,
              entry.params,
            );
            final highlight =
                isRelated && _filter == _AnalyticsDebugLogFilter.all;

            return Card(
              color: highlight ? colorScheme.primaryContainer : null,
              child: ListTile(
                leading: isRelated
                    ? Icon(
                        Icons.article_outlined,
                        color: colorScheme.onPrimaryContainer,
                      )
                    : null,
                title: Text(
                  entry.eventName,
                  style: highlight
                      ? TextStyle(color: colorScheme.onPrimaryContainer)
                      : null,
                ),
                subtitle: Text(
                  '${timeFormat.format(entry.recordedAt)} · ${entry.params}',
                  style: highlight
                      ? TextStyle(color: colorScheme.onPrimaryContainer)
                      : null,
                ),
                isThreeLine: true,
              ),
            );
          }),
      ],
    );
  }
}
