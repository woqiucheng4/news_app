import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/feed/presentation/screens/article_detail_screen.dart';
import '../../features/feed/presentation/screens/feed_screen.dart';
import '../../features/settings/presentation/screens/settings_screen.dart';
import '../../features/search/presentation/screens/search_screen.dart';
import '../../features/subscriptions/presentation/screens/subscriptions_screen.dart';
import '../../features/subscriptions/presentation/screens/topics_discovery_screen.dart';
import '../../l10n/app_localizations.dart';
import 'feed_article_page_transition.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/feed',
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/search',
        name: 'search',
        builder: (context, state) => const SearchScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return AppShell(
            navigationShell: navigationShell,
            location: state.uri.path,
          );
        },
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/feed',
                name: 'feed',
                builder: (context, state) => const Scaffold(body: FeedScreen()),
                routes: [
                  GoRoute(
                    path: 'article/:id',
                    name: 'feed-article',
                    pageBuilder: (context, state) {
                      final articleId = state.pathParameters['id'] ?? '';
                      return buildFeedArticleTransitionPage(
                        state: state,
                        child: ArticleDetailScreen(articleId: articleId),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/subscriptions',
                name: 'subscriptions',
                builder: (context, state) => const Scaffold(body: SubscriptionsScreen()),
                routes: [
                  GoRoute(
                    path: 'discover',
                    name: 'topics-discover',
                    builder: (context, state) => const TopicsDiscoveryScreen(),
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/settings',
                name: 'settings',
                builder: (context, state) => const Scaffold(body: SettingsScreen()),
              ),
            ],
          ),
        ],
      ),
    ],
  );
});

class AppShell extends StatelessWidget {
  const AppShell({
    super.key,
    required this.navigationShell,
    required this.location,
  });

  final StatefulNavigationShell navigationShell;
  final String location;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isArticleDetail = location.startsWith('/feed/article/');
    final title = isArticleDetail
        ? null
        : location == '/subscriptions/discover'
            ? l10n.discoverTopicsAction
            : l10n.appTitle;
    final showBackButton = !isArticleDetail &&
        location == '/subscriptions/discover';
    final showSearchAction = !isArticleDetail &&
        location != '/subscriptions/discover';

    return Scaffold(
      appBar: isArticleDetail
          ? null
          : AppBar(
              leading: showBackButton
                  ? BackButton(onPressed: () => GoRouter.of(context).pop())
                  : null,
              title: title == null ? null : Text(title!),
              actions: [
                if (showSearchAction)
                  IconButton(
                    icon: const Icon(Icons.search),
                    tooltip: l10n.globalSearchAction,
                    onPressed: () => context.push('/search'),
                  ),
              ],
            ),
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) {
          navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
          );
        },
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.dynamic_feed_outlined),
            selectedIcon: const Icon(Icons.dynamic_feed),
            label: l10n.feedTab,
          ),
          NavigationDestination(
            icon: const Icon(Icons.bookmark_border),
            selectedIcon: const Icon(Icons.bookmark),
            label: l10n.subscriptionsTab,
          ),
          NavigationDestination(
            icon: const Icon(Icons.settings_outlined),
            selectedIcon: const Icon(Icons.settings),
            label: l10n.settingsTab,
          ),
        ],
      ),
    );
  }
}
