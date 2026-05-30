# NewsFlow Backend Makefile
#
# Usage:
#   make help            # show available targets
#   make install         # install Python deps into local venv
#   make migrate         # run alembic upgrade head
#   make seed            # seed sources + topics
#   make demo-seed       # one-shot demo data (topics + demo user/subs + demo articles)
#   make run             # run uvicorn dev server
#   make test            # run pytest suite
#   make docker-up       # docker compose up --build -d
#   make demo-up         # ENABLE_DEMO_SEED=true docker compose up --build -d
#   make docker-down     # docker compose down
#   make docker-logs     # tail api logs

PY ?= .venv/bin/python
PIP ?= .venv/bin/pip
PYTEST ?= .venv/bin/pytest
ALEMBIC ?= .venv/bin/alembic
UVICORN ?= .venv/bin/uvicorn

.PHONY: help install venv migrate seed demo-seed run test \
        docker-up demo-up docker-down docker-logs

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## Create local virtualenv at .venv if missing
	@test -d .venv || python3 -m venv .venv

install: venv ## Install backend dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

migrate: ## Apply latest alembic migrations
	$(ALEMBIC) upgrade head

seed: ## Seed RSS sources + topic catalog
	$(PY) scripts/seed_sources.py
	$(PY) scripts/seed_topics.py

demo-seed: ## Seed full demo dataset (topics + demo user/subs + demo articles)
	$(PY) scripts/seed_demo_all.py

run: ## Run FastAPI dev server with reload
	$(UVICORN) main:app --reload --port 8000

test: ## Run pytest
	$(PYTEST) -q

docker-up: ## Start backend stack via docker compose
	docker compose up --build -d

demo-up: ## Start backend stack with demo seed enabled
	ENABLE_DEMO_SEED=true docker compose up --build -d

docker-down: ## Stop backend stack
	docker compose down

docker-logs: ## Follow API logs
	docker compose logs -f api
