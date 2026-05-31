import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_token_provider.dart';
import '../../features/subscriptions/presentation/providers/subscriptions_notifier.dart';
import 'push_providers.dart';

/// Initializes FCM and keeps topic subscriptions in sync with backend state.
class PushBootstrap extends ConsumerStatefulWidget {
  const PushBootstrap({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<PushBootstrap> createState() => _PushBootstrapState();
}

class _PushBootstrapState extends ConsumerState<PushBootstrap> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(ref.read(pushNotificationServiceProvider).initialize());
    });
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<String?>(accessTokenValueProvider, (previous, next) {
      if (next != null && next.isNotEmpty && next != previous) {
        unawaited(ref.read(pushNotificationServiceProvider).initialize());
      }
    });

    ref.listen(subscriptionsNotifierProvider, (previous, next) {
      next.whenData((items) {
        unawaited(
          ref.read(pushTopicSyncProvider).syncAll(
                subscriptions: items
                    .map(
                      (item) => (
                        topicId: item.topicId,
                        pushEnabled: item.pushEnabled,
                      ),
                    )
                    .toList(growable: false),
              ),
        );
      });
    });

    return widget.child;
  }
}
