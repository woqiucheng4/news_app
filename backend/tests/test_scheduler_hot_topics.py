from types import SimpleNamespace

import pytest

from tasks.scheduler import IngestionScheduler


@pytest.mark.asyncio
async def test_run_hot_topics_crawl_invokes_service(monkeypatch):
    calls: list[int] = []

    class FakeContentIngestionService:
        def __init__(self, **kwargs):
            pass

        async def crawl_hot_topics(self):
            calls.append(1)
            return [{"platform": "hackernews", "inserted_articles": 3}]

    monkeypatch.setattr("tasks.scheduler.ContentIngestionService", FakeContentIngestionService)

    class FakeSessionContext:
        async def __aenter__(self):
            return SimpleNamespace()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("tasks.scheduler.db_manager.get_write_session", lambda: FakeSessionContext())

    scheduler = IngestionScheduler()
    await scheduler._run_hot_topics_crawl()

    assert len(calls) == 1
