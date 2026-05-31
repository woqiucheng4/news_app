#!/usr/bin/env bash
# Phase 1 UAT — automated slice (see .planning/phases/01-foundation-ingestion/01-UAT.md)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"

cd "$BACKEND"
PY="${BACKEND}/.venv/bin/python"
PYTEST="${BACKEND}/.venv/bin/pytest"

if [[ ! -x "$PYTEST" ]]; then
  echo "Missing venv. Run: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "== Phase 1: full suite =="
"$PYTEST" -q

echo "== Phase 1: targeted modules =="
"$PYTEST" -q \
  tests/test_dedup.py \
  tests/test_rss_collector.py \
  tests/test_integration_ingestion_flow.py \
  tests/test_summarizer.py \
  tests/test_cost_service.py \
  tests/test_hot_platform_fetchers.py \
  tests/test_crawler.py \
  tests/test_adaptive_scheduler.py \
  tests/test_event_clustering.py \
  tests/test_api_endpoints.py

echo "== Phase 1: coverage gate (services+core, .coveragerc) =="
"$PYTEST" --cov=services --cov=core --cov-config=.coveragerc --cov-report=term -q \
  | tail -3

if docker info >/dev/null 2>&1; then
  echo "== Phase 1: docker stack (optional) =="
  if make docker-up && sleep 5 && curl -sf "http://localhost:8000/health" | head -c 200; then
    echo ""
    make docker-down || true
  else
    echo "Docker stack check failed (image pull or health). See 01-UAT.md tests 1-3, 12-13, 19-21."
  fi
else
  echo "== Docker skipped (daemon not running). Run tests 1-3, 12-13, 19-21 manually per 01-UAT.md =="
fi

echo "Phase 1 automated UAT: OK"
