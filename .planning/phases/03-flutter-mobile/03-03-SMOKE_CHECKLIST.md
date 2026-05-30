# NewsFlow Mobile Smoke Checklist

Run after `./scripts/smoke_build.sh` passes or before a store submission candidate.

## Automated (CI / script)

- [ ] `flutter analyze` — no errors
- [ ] `flutter test` — all unit/widget tests pass
- [ ] `flutter build apk --debug` — succeeds
- [ ] `flutter build ios --simulator --no-codesign` — succeeds (macOS)

## Device smoke (manual)

**Setup:** Backend running (`docker-compose up` or `uvicorn`), Flutter app built with correct `NEWSFLOW_API_BASE_URL`.

### Launch & navigation

- [ ] App launches to Feed tab without crash
- [ ] Bottom nav switches Feed / Subscriptions / Settings
- [ ] Search icon opens global search; article + topic tabs respond

### Auth (optional if using dev token)

- [ ] Login screen reachable from Settings
- [ ] Email login or dev token loads personalized feed

### Core flows

- [ ] Feed loads articles (or empty state with login prompt)
- [ ] Tap article → detail opens; back returns to feed
- [ ] Related articles section renders when backend returns matches
- [ ] Subscriptions list loads; tap topic → topic feed
- [ ] Pull-to-refresh on feed and topic feed

### Offline / errors

- [ ] Airplane mode on feed shows cached/offline banner when cache exists
- [ ] Invalid API URL shows retry affordance, not a white screen

### Platform-specific

**Android**

- [ ] Cold start < 5s on mid-range device
- [ ] Back gesture returns from detail/search/topic feed

**iOS**

- [ ] Safe area respected on notch devices
- [ ] Swipe-back from detail works

## Sign-off

| Date | Device(s) | Tester | Result |
|------|-----------|--------|--------|
| | | | |
