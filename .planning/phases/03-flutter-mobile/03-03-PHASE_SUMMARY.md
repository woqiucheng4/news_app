# 03-03 Mobile Release Readiness

**Status:** ✅ Done (2026-05-31)

## Delivers

- Generated `android/` and `ios/` platform projects (`com.newsflow.newsflow_frontend`)
- Android: minSdk 23, app label **NewsFlow**, debug cleartext for local API
- iOS: display name **NewsFlow**, `NSAllowsLocalNetworking` for simulator/local backend
- Script: `frontend/scripts/smoke_build.sh` (analyze + test + APK + iOS sim build on macOS)
- CI: `.github/workflows/flutter-mobile-build.yml` (Android APK on Ubuntu, iOS sim on macOS)
- Manual smoke checklist: [`03-03-SMOKE_CHECKLIST.md`](./03-03-SMOKE_CHECKLIST.md)

## Prerequisites

| Tool | Version |
|------|---------|
| Flutter | 3.x stable |
| Xcode | 15+ (iOS, macOS only) |
| Android Studio / SDK | API 34+ |
| CocoaPods | latest (iOS plugins) |

## One-command smoke build

```bash
cd frontend
chmod +x scripts/smoke_build.sh
./scripts/smoke_build.sh
```

## Emulator API URL

Default `apiBaseUrl` is `http://localhost:8000/api/v1`. On emulators use:

| Platform | Backend URL |
|----------|-------------|
| Android emulator | `http://10.0.2.2:8000/api/v1` |
| iOS simulator | `http://127.0.0.1:8000/api/v1` |
| Physical device | Your machine LAN IP, e.g. `http://192.168.1.10:8000/api/v1` |

```bash
flutter run \
  --dart-define=NEWSFLOW_API_BASE_URL=http://10.0.2.2:8000/api/v1
```

> `AppConstants.apiBaseUrl` reads `NEWSFLOW_API_BASE_URL` when set (see `app_constants.dart`).

## Release signing (not automated)

- **Android:** create `android/key.properties` + upload keystore; switch `signingConfig` in `android/app/build.gradle.kts`
- **iOS:** configure Team + provisioning in Xcode (`ios/Runner.xcworkspace`)

## Open hardening (post-MVP)

- Firebase `google-services.json` / `GoogleService-Info.plist` for FCM
- Google Sign-In URL schemes (iOS `Info.plist`, Android SHA-1)
- App Store / Play Store listing assets
