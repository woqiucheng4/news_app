# Phase 4-01: FCM Topic Push + Token Registration

## Delivers

- Backend `NotificationService` with FCM topic push (`topic_{topic_id}`)
- `POST /api/v1/notifications/register` for device token persistence
- Article summary task triggers topic push for matching subscribed topics
- Flutter `PushNotificationService` + `PushBootstrap` topic sync on subscribe/unsubscribe

## Enable Push (dev)

1. Add Firebase project files:
   - `frontend/android/app/google-services.json`
   - `frontend/ios/Runner/GoogleService-Info.plist`
2. Set backend credentials: `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_CREDENTIALS_JSON`
3. Run Flutter with:

```bash
flutter run \
  --dart-define=NEWSFLOW_ENABLE_FIREBASE=true \
  --dart-define=NEWSFLOW_ENABLE_PUSH=true
```

## Verification

```bash
cd backend && .venv/bin/python -m pytest tests/test_notifications_api.py -q
cd frontend && flutter test test/core/push/fcm_topic_name_test.dart
```

## Known Limits (04-02 follow-up)

- Daily briefing job not implemented
- Per-user `push_breaking_only` not enforced at FCM topic level
- `push_max_per_day` rate limiting not implemented
