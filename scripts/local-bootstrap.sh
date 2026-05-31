#!/usr/bin/env bash
# Bootstrap local NewsFlow backend (Postgres/Redis via Docker, API via venv).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"

cd "$BACKEND"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created backend/.env — set OPENAI_API_KEY before summaries work."
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

echo "== Starting Postgres + Redis =="
docker compose up -d postgres redis

echo "== Migrations =="
.venv/bin/alembic upgrade head

echo "== Seed (sources + topics) =="
.venv/bin/python scripts/seed_sources.py
.venv/bin/python scripts/seed_topics.py

if [[ "${1:-}" == "--demo" ]]; then
  echo "== Demo user + articles =="
  .venv/bin/python scripts/seed_demo_all.py
fi

echo ""
echo "Done. Start API:"
echo "  cd backend && set -a && source .env && set +a && make run"
echo "  curl http://localhost:8000/health"
