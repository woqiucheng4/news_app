# Phase 4-02: Daily Briefing

## Delivers

- `DailyBriefingService` aggregates last-24h subscribed-topic articles and generates an AI digest
- APScheduler cron job (`DAILY_BRIEFING_HOUR_UTC`, default 08:00 UTC)
- Per-device FCM push via registered tokens (not topic broadcast)
- Respects `push_daily_briefing`, `push_max_per_day`, quiet hours, one briefing per day
- Flutter tap handler navigates to `/feed` for `daily_briefing` payloads

## Verification

```bash
cd backend && .venv/bin/python -m pytest tests/test_daily_briefing.py -q
cd frontend && flutter test test/core/push/push_navigation_test.dart
```

## Post-MVP

- Per-user timezone scheduling
- In-app daily briefing screen
- Breaking news instant push policy (DIST-06)
