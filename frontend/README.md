# NewsFlow Frontend

Flutter client for NewsFlow.

## Quick Start

1. Install Flutter 3.x and ensure `flutter` is in PATH.
2. Start the backend (`http://localhost:8000` by default).
3. Install dependencies and run:

```bash
flutter pub get
flutter gen-l10n
flutter run
```

Optional dev token (skips login UI):

```bash
flutter run --dart-define=NEWSFLOW_ACCESS_TOKEN=<your_access_token>
```

## Authentication

- Email register/login at `/login`
- Google / Apple OAuth via native SDKs → `POST /api/v1/auth/oauth/{provider}`
- Access + refresh tokens stored in **Flutter Secure Storage** (migrated once from legacy SharedPreferences)
- Automatic refresh on `401` with **refresh token rotation** (`POST /api/v1/auth/refresh`)

### OAuth setup

**Google**

- Create OAuth client IDs in Google Cloud Console.
- Web: pass `NEWSFLOW_GOOGLE_WEB_CLIENT_ID`
- iOS: pass `NEWSFLOW_GOOGLE_IOS_CLIENT_ID`
- Android: add `google-services.json` under `android/app/`

```bash
flutter run \
  --dart-define=NEWSFLOW_GOOGLE_WEB_CLIENT_ID=<web-client-id> \
  --dart-define=NEWSFLOW_GOOGLE_IOS_CLIENT_ID=<ios-client-id>
```

**Apple**

- Enable Sign in with Apple in Xcode (iOS) and Apple Developer portal.
- Available on iOS / macOS / Android builds (hidden on Web).

Backend expects:

```http
POST /api/v1/auth/oauth/google
POST /api/v1/auth/oauth/apple
```

Body: `provider_id`, `email`, optional `display_name`, `avatar_url`.

## Offline cache

| Data | Storage | TTL | Limit |
|------|---------|-----|-------|
| Feed pages | SharedPreferences | 30 min | 5 pages |
| Article details | SharedPreferences | 7 days | 50 articles |

- Network failure falls back to stale cache with an offline banner.
- Feed list pre-writes article detail previews (tap + first page prefetch) for instant detail open.
- Detail page shows a preview banner while fetching the full article; banner clears after refresh.
- Preview mode keeps known fields visible and skeleton placeholders for pending content.
- Feed cards show a brief progress bar while opening an article.
- Preview banner uses a rotating sync icon; skeleton placeholders animate out when full content loads.
- Skeleton lines use a shared pulse animation; opening feed cards dim briefly with an animated progress bar.
- Feed-to-detail navigation uses Hero transitions on the title, category, summary preview, and source metadata row.
- Article detail uses a collapsing `SliverAppBar` with stretch overscroll and an in-page back button; the shell AppBar is hidden on detail routes.
- `ArticleDetail` parses the backend `source` object; preview cache preserves source metadata from feed items.
- Article detail API returns `related_articles` (same event cluster); the detail screen shows them in a horizontal carousel with preview cache on tap.
- `GET /articles/{id}/related` paginates the full related list; "View all" opens a bottom sheet with infinite scroll, retry, and empty states.
- Related coverage emits `feed_related_impression`, `feed_related_swipe`, `feed_related_click`, and `feed_related_view_all` analytics; load failures show user-facing messages instead of raw errors.
- Settings → Analytics debug log can filter and highlight related-article events (`feed_related_*` plus `feed_article_open` with `source=related_article`).
- Global search (`/search`): dual-tab article + topic search with debounce; article results open detail with `feed_article_open` source `search`.
- Topic feed: Subscriptions → tap a topic → `/subscriptions/topic/:id` loads `GET /articles/feed?topic_id=` with pagination.
- Cached article payloads are hydrated with `related_articles`, `related_articles_total`, and `source.url` when older cache entries omit them.
- Article detail route uses a fade + subtle slide custom page transition.
- Pulse and rotation animations pause automatically when tickers are disabled.
- Pull-to-refresh forces a network fetch (feed + article detail).
- Logout clears feed and article caches.

## Feed & subscriptions

- Feed: `GET /api/v1/articles/feed` with pagination and infinite scroll
- Article detail: `GET /api/v1/articles/{id}` with offline cache
- Subscriptions, topic discovery, keyword subscribe (see code under `lib/features/`)

## Analytics

```bash
flutter run \
  --dart-define=NEWSFLOW_ANALYTICS_ADAPTER=production \
  --dart-define=NEWSFLOW_ANALYTICS_TRANSPORT=http
```

Default ingest: `http://localhost:8000/api/v1/analytics/events`

Dashboard: `http://localhost:8000/web/analytics` (optional `?token=` or admin JWT)

Optional Firebase:

```bash
flutter run \
  --dart-define=NEWSFLOW_ENABLE_FIREBASE=true \
  --dart-define=NEWSFLOW_ANALYTICS_ADAPTER=production \
  --dart-define=NEWSFLOW_ANALYTICS_TRANSPORT=firebase
```

### Related-articles analytics (manual)

1. Generate localizations if needed: `flutter gen-l10n`
2. Run the app (debug adapter is fine — events appear in Settings → Analytics).
3. Open an article with related coverage; confirm `feed_related_impression` in the debug log.
4. Swipe the horizontal carousel; confirm `feed_related_swipe` (`source=detail_section`).
5. Tap a related card; confirm `feed_related_click` and `feed_article_open` (`source=related_article`).
6. Tap **View all**, scroll the sheet; confirm `feed_related_swipe` (`source=related_sheet`).
7. Switch the debug log filter to **Related articles** — all of the above should remain visible.

### Related-articles analytics (automated)

```bash
cd frontend
flutter gen-l10n
flutter test test/core/analytics/analytics_related_events_test.dart
flutter test test/features/feed/presentation/widgets/related_articles_section_test.dart
cd ../backend
.venv/bin/python -m pytest tests/test_analytics_api.py::test_ingest_feed_and_subscription_events -q
```

## API base URL

Configured in `lib/core/constants/app_constants.dart` (`apiBaseUrl`, default `http://localhost:8000/api/v1`).
