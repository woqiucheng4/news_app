# Phase 5-01: Backend Freemium + Billing

## Delivers

- `FreemiumSettings` in config (`FREE_MAX_TOPIC_SUBSCRIPTIONS`, `FREE_DAILY_ARTICLE_VIEWS`, `PREMIUM_PRODUCT_ID`, `ALLOW_DEV_PURCHASE_VERIFY`)
- `FreemiumService` — entitlements snapshot, subscription cap, daily article view counting (cache)
- `DeepAnalysisService` — premium-only Claude/GPT deep analysis
- `BillingService` — dev/stub IAP verify, 30-day premium activation
- APIs:
  - `GET /users/me/entitlements`
  - `POST /billing/verify-purchase`
  - `POST /articles/{id}/deep-analysis`
  - Article detail + subscribe endpoints enforce freemium limits (403 structured codes)

## Verification

```bash
cd backend && .venv/bin/python -m pytest tests/test_freemium.py tests/test_billing.py tests/test_user_subscription_api.py tests/test_api_endpoints.py -q
```

## Post-MVP

- Real App Store / Play receipt verification (501 in production today)
- Premium expiry renewal webhooks
