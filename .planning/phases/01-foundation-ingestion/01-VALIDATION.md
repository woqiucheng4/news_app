---
phase: 1
slug: foundation-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | pyproject.toml (none — Wave 0 installs) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 01-01 | Project scaffold | 0 | — | smoke | `python -c "from app.main import app"` | ⬜ pending |
| 01-02 | DB schema | 0 | CONT-01~07 | unit | `pytest tests/test_models.py -v` | ⬜ pending |
| 01-03 | RSS collector | 1 | CONT-01, CONT-02 | unit | `pytest tests/test_rss_collector.py -v` | ⬜ pending |
| 01-04 | URL crawler | 1 | CONT-03 | unit | `pytest tests/test_crawler.py -v` | ⬜ pending |
| 01-05 | Dedup engine | 1 | CONT-05 | unit | `pytest tests/test_dedup.py -v` | ⬜ pending |
| 01-06 | AI summarizer | 2 | AI-01, AI-02, AI-03 | unit | `pytest tests/test_summarizer.py -v` | ⬜ pending |
| 01-07 | Content API | 2 | CONT-04 | integration | `pytest tests/test_content_api.py -v` | ⬜ pending |
| 01-08 | Scheduler | 2 | CONT-06, CONT-07 | unit | `pytest tests/test_scheduler.py -v` | ⬜ pending |
| 01-09 | Content filter | 2 | AI-07, AI-08 | unit | `pytest tests/test_content_filter.py -v` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — project config with pytest, FastAPI, SQLAlchemy, etc.
- [ ] `tests/conftest.py` — shared fixtures (test DB, mock AI client)
- [ ] `pytest install` — `pip install pytest pytest-asyncio httpx`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RSS source health monitoring | CONT-06 | Requires live RSS feeds | Add test RSS feed, disable it, verify alert |
| AI cost stays under budget | AI-02 | Requires real API calls | Run 100 summaries, check cost < $1 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
