# Phase 1 Closure: Ingestion Pipeline Gaps

## Delivers (this batch)

### 01-06 Budget enforcement
- `CostService.get_degradation_level()` adds `cache_only` tier (≥95% budget)
- `ArticleService.generate_summary()` respects `paused` / `cache_only`
- Scheduler summary batch reduced when `degraded`, skipped when `paused`

### 01-07 Hot topics scheduler
- APScheduler job `hot_topics_crawl` every 20 minutes
- Calls `ContentIngestionService.crawl_hot_topics()`

### 01-03 Custom sources API
- `GET /api/v1/sources/me` — list user feeds
- `POST /api/v1/sources/rss` — register RSS + immediate fetch
- `POST /api/v1/sources/url` — ingest single web page
- `UserFeedRepository` + ingestion helpers in `ContentIngestionService`

## Verification

```bash
cd backend && .venv/bin/python -m pytest -q
# Custom sources
curl -X POST http://localhost:8000/api/v1/sources/rss \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feed_url":"https://hnrss.org/frontpage","name":"HN"}'
```

## Post-MVP / UAT

- Run `.planning/phases/01-foundation-ingestion/01-UAT.md`
- robots.txt compliance for crawlers
- Source failure alerting (beyond deactivate)
- Production hot-platform endpoint monitoring
