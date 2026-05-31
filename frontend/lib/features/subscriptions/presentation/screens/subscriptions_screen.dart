import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/auth/auth_token_provider.dart';
import '../../../../core/network/dio_error_utils.dart';
import '../../../../l10n/app_localizations.dart';
import '../providers/subscriptions_notifier.dart';

class SubscriptionsScreen extends ConsumerWidget {
  const SubscriptionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final subscriptionsState = ref.watch(subscriptionsNotifierProvider);

    return RefreshIndicator(
      onRefresh: () => ref.read(subscriptionsNotifierProvider.notifier).refresh(),
      child: subscriptionsState.when(
        data: (items) {
          final listChildren = <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: FilledButton.icon(
                  onPressed: () => context.push('/subscriptions/discover'),
                  icon: const Icon(Icons.explore_outlined),
                  label: Text(l10n.discoverTopicsAction),
                ),
              ),
            ),
          ];

          if (items.isEmpty) {
            listChildren.add(
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: Center(
                  child: Text(
                    l10n.emptySubscriptions,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ),
              ),
            );

            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: listChildren,
            );
          }

          for (var index = 0; index < items.length; index++) {
            final item = items[index];
            listChildren.add(
              ListTile(
                title: Text(item.topicName),
                subtitle: Text(item.topicCategory ?? ''),
                onTap: () {
                  final encodedName = Uri.encodeQueryComponent(item.topicName);
                  context.push(
                    '/subscriptions/topic/${item.topicId}?name=$encodedName',
                  );
                },
                trailing: SizedBox(
                  width: 170,
                  child: Row(
                    children: [
                      Expanded(
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            Text(l10n.subscriptionPush),
                            Switch(
                              value: item.pushEnabled,
                              onChanged: (enabled) {
                                ref
                                    .read(subscriptionsNotifierProvider.notifier)
                                    .togglePush(item.topicId, enabled);
                              },
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: l10n.unsubscribeAction,
                        onPressed: () {
                          ref
                              .read(subscriptionsNotifierProvider.notifier)
                              .removeSubscription(item.topicId);
                        },
                        icon: const Icon(Icons.remove_circle_outline),
                      ),
                    ],
                  ),
                ),
              ),
            );

            if (index < items.length - 1) {
              listChildren.add(const Divider(height: 1));
            }
          }

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: listChildren,
          );
        },
        error: (error, _) {
          final hasToken = ref.watch(accessTokenValueProvider).trim().isNotEmpty;
          if (!hasToken && isUnauthorizedError(error)) {
            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                SizedBox(
                  height: MediaQuery.of(context).size.height * 0.7,
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            l10n.subscriptionsLoginRequiredTitle,
                            style: Theme.of(context).textTheme.titleMedium,
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            l10n.subscriptionsLoginRequiredDescription,
                            style: Theme.of(context).textTheme.bodyMedium,
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 20),
                          FilledButton(
                            onPressed: () => context.push('/login'),
                            child: Text(l10n.settingsSignInAction),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            );
          }

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.7,
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${l10n.loadFailed}: $error',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: () {
                            ref.read(subscriptionsNotifierProvider.notifier).refresh();
                          },
                          child: Text(l10n.retryAction),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          );
        },
        loading: () => const Center(
          child: CircularProgressIndicator(),
        ),
      ),
    );
  }
}
