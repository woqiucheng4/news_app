# Phase 5-03: IAP + Launch Prep (partial)

## Delivers (code)

- Flutter `in_app_purchase` integration with store product query + purchase stream → backend verify
- Upgrade screen: store subscribe button + debug dev activation fallback
- Premium priority FCM pushes (high priority direct token delivery for premium subscribers)
- Premium daily briefing: 2× push quota + high-priority delivery
- Deep analysis multi-source synthesis (AI-06) from event-cluster related articles
- Privacy policy (`docs/PRIVACY_POLICY.md`) + Settings link

## Still manual (store submission)

- Apple Developer / Play Console accounts and listing assets
- Configure `newsflow_premium_monthly` subscription products in both stores
- Production receipt verification (replace dev stub when `DEBUG=false`)
- TestFlight / internal testing → public release

## Verification

```bash
cd backend && .venv/bin/python -m pytest tests/test_premium_push.py tests/test_deep_analysis.py -q
cd frontend && flutter test
```
