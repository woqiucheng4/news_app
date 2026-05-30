import os
from types import SimpleNamespace

import pytest


# Ensure required settings are always present during test collection/import.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("DEBUG", "true")


@pytest.fixture
def fake_ai_response():
    return SimpleNamespace(
        content='{"summary":"integration summary","relevance_score":88}',
        model="gpt-4o-mini",
        input_tokens=80,
        output_tokens=20,
        total_tokens=100,
        cost_usd=0.0012,
    )
