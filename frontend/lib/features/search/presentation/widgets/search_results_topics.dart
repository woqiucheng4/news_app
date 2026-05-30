import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_providers.dart';
import '../../../../l10n/app_localizations.dart';
import '../../../subscriptions/presentation/utils/subscription_error_mapper.dart';
import '../providers/search_page_topics_notifier.dart';

class SearchResultsTopics extends ConsumerWidget {
  const SearchResultsTopics({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final topicsState = ref.watch(searchPageTopicsNotifierProvider);

    return topicsState.when(
      data: (topics) {
        if (topics.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                l10n.globalSearchTopicsEmpty,
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: topics.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final topic = topics[index];
            return ListTile(
              title: Text(topic.name),
              subtitle: Text(
                [
                  if (topic.category != null && topic.category!.isNotEmpty)
                    topic.category!,
                  if (topic.description != null && topic.description!.isNotEmpty)
                    topic.description!,
                ].join(' · '),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: topic.isSubscribed
                  ? Text(
                      l10n.subscribedAction,
                      style: Theme.of(context).textTheme.labelMedium,
                    )
                  : FilledButton(
                      onPressed: () async {
                        try {
                          await ref
                              .read(searchPageTopicsNotifierProvider.notifier)
                              .subscribeTopic(topic.id);
                          ref.read(appAnalyticsProvider).trackTopicSubscribe(
                                topicId: topic.id,
                                success: true,
                              );
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(l10n.subscribeSuccess)),
                            );
                          }
                        } catch (error) {
                          ref.read(appAnalyticsProvider).trackTopicSubscribe(
                                topicId: topic.id,
                                success: false,
                              );
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(
                                  mapSubscriptionError(error, l10n),
                                ),
                              ),
                            );
                          }
                        }
                      },
                      child: Text(l10n.subscribeAction),
                    ),
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                l10n.globalSearchFailed,
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                '$error',
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () {
                  ref.invalidate(searchPageTopicsNotifierProvider);
                },
                child: Text(l10n.retryAction),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
