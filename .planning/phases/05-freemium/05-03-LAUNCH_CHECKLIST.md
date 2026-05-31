# Phase 5-03: App Store Launch Checklist

## MVP status

Backend freemium + Flutter upgrade UX + IAP client integration are implemented. **Store submission still requires manual steps** — use this checklist before release.

## Completed in codebase

- [x] Flutter `in_app_purchase` client wired to `/billing/verify-purchase`
- [x] Premium priority FCM delivery
- [x] Privacy policy document + in-app link
- [x] Dev purchase stub for local testing (`DEBUG=true` or `ALLOW_DEV_PURCHASE_VERIFY=true`)

## App Store (iOS)

- [ ] Apple Developer account + App ID
- [ ] Privacy policy URL (GDPR: data processing disclosure)
- [ ] App Store Connect listing (screenshots, description, keywords)
- [ ] In-App Purchase product `newsflow_premium_monthly` (auto-renewable subscription)
- [ ] Replace dev purchase stub with StoreKit 2 receipt validation
- [ ] Push notification entitlement + APNs key in Firebase
- [ ] TestFlight beta → review submission

## Google Play (Android)

- [ ] Play Console app + signing key
- [ ] Privacy policy URL
- [ ] Store listing assets
- [ ] Subscription product matching `PREMIUM_PRODUCT_ID`
- [ ] Play Billing Library + server-side purchase token verify
- [ ] FCM `google-services.json` for release build
- [ ] Internal testing → production rollout

## Compliance

- [ ] GDPR: account export/delete flows verified (`/users/me/export`, `/users/me` DELETE)
- [ ] Copyright: summaries + link-out only (no full-text cache)
- [ ] Age rating questionnaire

## Env (production)

```env
ALLOW_DEV_PURCHASE_VERIFY=false
DEBUG=false
PREMIUM_PRODUCT_ID=newsflow_premium_monthly
FREE_MAX_TOPIC_SUBSCRIPTIONS=5
FREE_DAILY_ARTICLE_VIEWS=20
```
