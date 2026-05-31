from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import sources as sources_module
from api.v1.router import api_router
from core.dependencies import get_db


class FakeIngestionService:
    def __init__(self):
        self.rss_calls: list[dict] = []
        self.url_calls: list[dict] = []

    async def register_user_rss_feed(self, **kwargs):
        self.rss_calls.append(kwargs)
        return {
            "source_id": str(uuid4()),
            "user_feed_id": str(uuid4()),
            "feed_url": kwargs["feed_url"],
            "inserted_articles": 2,
        }

    async def ingest_user_web_url(self, **kwargs):
        self.url_calls.append(kwargs)
        return {
            "source_id": str(uuid4()),
            "user_feed_id": str(uuid4()),
            "url": kwargs["page_url"],
            "article_id": str(uuid4()),
            "inserted": True,
        }


class FakeUserFeedRepo:
    def __init__(self, _session):
        self.feeds = [
            SimpleNamespace(
                id=uuid4(),
                feed_type="rss",
                custom_url="https://example.com/feed.xml",
                custom_name="Example",
                source_id=uuid4(),
                is_active=True,
            )
        ]

    async def list_for_user(self, user_id, limit=100):
        return self.feeds


@pytest.fixture
def client(monkeypatch):
    fake_service = FakeIngestionService()
    monkeypatch.setattr(sources_module, "_build_ingestion_service", lambda _db: fake_service)
    monkeypatch.setattr(sources_module, "UserFeedRepository", FakeUserFeedRepo)

    async def fake_get_db():
        session = SimpleNamespace()

        async def commit():
            return None

        session.commit = commit
        yield session

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[get_db] = fake_get_db
    app.state.fake_service = fake_service
    return TestClient(app)


def test_list_my_sources(client):
    response = client.get("/api/v1/sources/me", headers={"x-user-id": "user-1"})
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["feed_type"] == "rss"


def test_register_rss_source(client):
    response = client.post(
        "/api/v1/sources/rss",
        headers={"x-user-id": "user-1"},
        json={
            "feed_url": "https://example.com/feed.xml",
            "name": "Example Feed",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["inserted_articles"] == 2
    assert client.app.state.fake_service.rss_calls[0]["user_id"] == "user-1"


def test_ingest_web_url(client):
    response = client.post(
        "/api/v1/sources/url",
        headers={"x-user-id": "user-1"},
        json={
            "url": "https://example.com/article",
            "name": "Example Article",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["inserted"] is True
