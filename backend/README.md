# NewsFlow Backend

AI-powered information aggregation backend built with FastAPI.

## Architecture

```
backend/
├── core/                    # Core infrastructure
│   ├── config.py           # Configuration management
│   ├── database.py         # Database connection pool
│   ├── cache.py            # Multi-level cache (L1: local, L2: Redis)
│   ├── tasks.py            # Task queue (APScheduler / Celery)
│   ├── storage.py          # File storage (Local / S3)
│   ├── ai.py               # AI service (OpenAI / Anthropic)
│   └── dependencies.py     # FastAPI dependency injection
├── models/                  # SQLAlchemy models
├── repositories/            # Data access layer (Repository pattern)
│   ├── interfaces.py       # Abstract interfaces
│   └── sqlalchemy/         # SQLAlchemy implementations
├── services/                # Business logic layer
│   ├── interfaces.py       # Abstract interfaces
│   └── *.py                # Service implementations
├── api/                     # API routes
│   └── v1/                 # API version 1
├── middleware/              # Middleware
│   └── rate_limit.py       # Rate limiting
├── tasks/                   # Background tasks
├── alembic/                 # Database migrations
├── main.py                  # Application entry point
├── Dockerfile               # Docker build
├── docker-compose.yml       # Docker Compose
└── requirements.txt         # Python dependencies
```

## Key Features

### Scalability

- **API Layer**: Stateless, horizontal scaling with load balancer
- **Database**: Connection pool + read/write separation support
- **Cache**: Multi-level cache (local memory + Redis)
- **Task Queue**: Pluggable (APScheduler → Celery)
- **Storage**: Pluggable (Local → S3)
- **AI Service**: Multi-model support with cost control

### Extensibility

- **Repository Pattern**: Abstract interfaces, swap implementations
- **Service Pattern**: Business logic separated from data access
- **Dependency Injection**: Easy testing and configuration
- **Configuration Externalization**: Environment variables

### Production Ready

- **Health Checks**: Database, Redis, AI service
- **Rate Limiting**: Per-endpoint, per-user
- **Cost Monitoring**: Daily/monthly budgets, automatic degradation
- **Docker Support**: Multi-stage build, health checks
- **Database Migrations**: Alembic

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
vim .env
```

### 2. Docker (Recommended)

```bash
# One-command startup (includes PostgreSQL + Redis + API)
# API container automatically runs:
#   1) alembic upgrade head
#   2) python scripts/seed_sources.py
#   3) python scripts/seed_topics.py
#   4) uvicorn main:app
docker compose up --build -d

# Check service status
docker compose ps

# View API logs
docker compose logs -f api

# (Optional) enable demo data seeding in startup chain
ENABLE_DEMO_SEED=true docker compose up --build -d
```

### 2.1 Local Acceptance Checks (01-01)

```bash
# Swagger
open http://localhost:8000/docs

# Health endpoint should return status=healthy
curl http://localhost:8000/health

# Verify seeded RSS source count = 20
docker compose exec -T postgres \
  psql -U postgres -d newflow \
  -c "SELECT COUNT(*) AS rss_source_count FROM sources WHERE source_type='rss';"

# Verify seeded topic count = 20
docker compose exec -T postgres \
  psql -U postgres -d newflow \
  -c "SELECT COUNT(*) AS topic_count FROM topics WHERE is_deleted=false;"
```

### 3. Local Development

> Tip: 常用命令已封装在 `backend/Makefile`，可直接 `make help` 查看。
> 例如 `make install`、`make migrate`、`make seed`、`make demo-seed`、`make run`、`make demo-up`。

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed initial sources/topics
python scripts/seed_sources.py
python scripts/seed_topics.py

# Optional: seed one demo user + subscriptions for UI smoke tests
python scripts/seed_demo_user_and_subscriptions.py

# Optional: seed demo feed articles for stable UI preview
python scripts/seed_demo_articles.py

# One-command demo seed (topics + demo user/subscriptions + demo articles)
python scripts/seed_demo_all.py

# Start development server
uvicorn main:app --reload --port 8000
```

### 3.1 Demo User Seed (Optional)

For quick frontend smoke tests, seed one demo user and initial subscriptions:

```bash
python scripts/seed_demo_user_and_subscriptions.py
```

Customizable environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_USER_EMAIL` | `demo@newsflow.app` | Demo user email |
| `DEMO_USER_DISPLAY_NAME` | `NewsFlow Demo` | Demo display name |
| `DEMO_TOPIC_SLUGS` | `ai,machine-learning,us-market,global-politics,movies` | Comma-separated topic slugs to subscribe |

Quick verification:

```bash
docker compose exec -T postgres \
  psql -U postgres -d newflow \
  -c "SELECT email, id FROM users WHERE email='demo@newsflow.app';"

docker compose exec -T postgres \
  psql -U postgres -d newflow \
  -c "SELECT COUNT(*) AS demo_subscription_count \
      FROM subscriptions s JOIN users u ON u.id=s.user_id \
      WHERE u.email='demo@newsflow.app' AND s.is_deleted=false AND s.is_active=true;"
```

### 3.2 Demo Articles Seed (Optional)

Seed a stable set of demo articles for feed UI testing:

```bash
python scripts/seed_demo_articles.py
```

Quick verification:

```bash
docker compose exec -T postgres \
  psql -U postgres -d newflow \
  -c "SELECT COUNT(*) AS demo_article_count FROM articles WHERE summary_model='demo-seed' AND is_deleted=false;"
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health
- Web Feed (MVP UI): http://localhost:8000/web/feed
- Web Hot Topics: http://localhost:8000/web/hot

### Auth Endpoints (Phase 2 / 02-01)

- `POST /api/v1/auth/register` — 邮箱注册
- `POST /api/v1/auth/login` — 邮箱登录
- `POST /api/v1/auth/oauth/{provider}` — OAuth 登录（`google` / `apple`）
- `POST /api/v1/auth/refresh` — 刷新 access token

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key (optional) |
| `GITHUB_TOKEN` | - | GitHub API token for higher trending API quota (optional) |
| `PRODUCT_HUNT_BEARER_TOKEN` | - | Product Hunt bearer token reserved for authenticated API mode (optional) |
| `AI_DAILY_BUDGET_USD` | `5.0` | Daily AI cost budget |
| `STORAGE_TYPE` | `local` | Storage type (local/s3) |
| `USE_CELERY` | `false` | Use Celery for tasks |
| `DEBUG` | `false` | Debug mode |
| `WORKERS` | `4` | Number of workers |
| `ENABLE_DEMO_SEED` | `false` | Docker startup toggle for running `scripts/seed_demo_all.py` |

### Scaling Configuration

```bash
# MVP (0-100 users)
WORKERS=2
DB_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=50

# Growth (100-1K users)
WORKERS=4
DB_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=100

# Scale (1K-10K users)
WORKERS=8
DB_POOL_SIZE=50
DB_READ_URLS=...  # Add read replicas
USE_CELERY=true
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest -q

# Core unit/integration set (phase 01)
pytest tests/test_dedup.py tests/test_cost_service.py tests/test_rss_collector.py \
  tests/test_crawler.py tests/test_summarizer.py tests/test_integration_ingestion_flow.py -q

# API endpoint smoke tests
pytest tests/test_api_endpoints.py -q

# Coverage report (target for core modules: >=70%)
pytest --cov=services --cov=repositories --cov=api --cov-report=term-missing
```

### Test Notes

- `tests/conftest.py` injects minimal required env vars for test import/collection.
- AI responses are mocked in tests; no external model API call is required.
- Some tests rely on monkeypatch/fake repositories to avoid real DB/Redis dependencies.

## Deployment

### Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch
fly launch

# Deploy
fly deploy
```

### Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

## License

Proprietary
