# Phase 5-02: Flutter Freemium UX

## Delivers

- `features/billing/` module: entitlements API, billing verify, deep analysis API
- `entitlementsProvider`, `UpgradeScreen` (`/upgrade`), dev purchase activation
- Settings: usage card + upgrade entry; article detail: deep analysis section + 403 upgrade prompts
- `freemium_error_mapper` for `SUBSCRIPTION_LIMIT_REACHED`, `DAILY_VIEW_LIMIT_REACHED`, `PREMIUM_REQUIRED`
- l10n (en/zh) for upgrade and limit copy

## Verification

```bash
cd frontend && flutter test
cd frontend && dart analyze lib/features/billing
```

## Post-MVP

- `in_app_purchase` integration for real store billing
- Invalidate JWT / refresh user after purchase for immediate premium UI
