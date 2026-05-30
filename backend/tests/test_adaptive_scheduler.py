from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import os
import sys

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tasks.scheduler import IngestionScheduler


def test_map_fetch_interval_minutes():
    assert IngestionScheduler._map_fetch_interval_minutes(60) == 5
    assert IngestionScheduler._map_fetch_interval_minutes(25) == 15
    assert IngestionScheduler._map_fetch_interval_minutes(8) == 30
    assert IngestionScheduler._map_fetch_interval_minutes(2) == 120
    assert IngestionScheduler._map_fetch_interval_minutes(0) == 360


def test_calculate_heat_score_formula():
    # heat_score = articles_24h * 0.6 + subscribers * 0.4
    score = IngestionScheduler._calculate_heat_score(article_count=20, subscriber_count=10)
    assert score == pytest.approx(16.0)


def test_is_source_due_respects_fetch_interval():
    now = datetime.utcnow()
    source = SimpleNamespace(
        last_fetched_at=now - timedelta(minutes=31),
        fetch_interval_minutes=30,
    )
    assert IngestionScheduler._is_source_due(source, now) is True

    source = SimpleNamespace(
        last_fetched_at=now - timedelta(minutes=10),
        fetch_interval_minutes=30,
    )
    assert IngestionScheduler._is_source_due(source, now) is False
