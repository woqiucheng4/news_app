from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sqlalchemy.dialects import postgresql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import articles as articles_module
from api.v1.router import api_router
from repositories.sqlalchemy.article import ArticleRepository


class FakeTopicFeedService:
    async def get_feed(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        topic_id=None,
        topic_name=None,
    ):
        if topic_id:
            return {
                "page": page,
                "page_size": page_size,
                "articles": [
                    {
                        "id": f"{topic_id}-article-{page}",
                        "title": f"{topic_name} headline",
                        "url": "https://example.com/topic",
                        "excerpt": None,
                        "summary": f"Summary for {topic_name}",
                        "author": None,
                        "source": None,
                        "category": "tech",
                        "tags": [],
                        "published_at": "2026-05-29T08:00:00",
                        "created_at": "2026-05-29T08:00:00",
                        "view_count": 0,
                        "bookmark_count": 0,
                    }
                ],
                "has_more": False,
                "topic_id": topic_id,
            }

        return {
            "page": page,
            "page_size": page_size,
            "articles": [],
            "has_more": False,
        }


class _FakeExecuteResult:
    def scalars(self):
        return self

    def all(self):
        return []


class _CaptureSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _FakeExecuteResult()


def _build_test_app(*, subscribed: bool = True, topic_exists: bool = True):
    app = FastAPI()
    app.include_router(api_router)

    async def override_article_service():
        return FakeTopicFeedService()

    async def override_db():
        yield SimpleNamespace()

    class FakeSubscriptionRepo:
        def __init__(self, _db):
            pass

        async def is_subscribed(self, user_id: str, topic_id: str) -> bool:
            return subscribed

    class FakeTopicRepo:
        def __init__(self, _db):
            pass

        async def get_by_id(self, topic_id: str):
            if not topic_exists:
                return None
            return SimpleNamespace(id=topic_id, name="AI")

    app.dependency_overrides[articles_module.get_article_service] = override_article_service
    app.dependency_overrides[articles_module.get_db] = override_db
    articles_module.SubscriptionRepository = FakeSubscriptionRepo
    articles_module.TopicRepository = FakeTopicRepo
    return app


def test_topic_feed_returns_filtered_payload():
    client = TestClient(_build_test_app())
    headers = {"x-user-id": "user-1"}

    resp = client.get(
        "/api/v1/articles/feed",
        params={"topic_id": "topic-ai", "page": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["topic_id"] == "topic-ai"
    assert payload["articles"][0]["title"] == "AI headline"


def test_topic_feed_requires_subscription():
    client = TestClient(_build_test_app(subscribed=False))
    headers = {"x-user-id": "user-1"}

    resp = client.get(
        "/api/v1/articles/feed",
        params={"topic_id": "topic-ai"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_topic_feed_requires_auth_for_guest():
    client = TestClient(_build_test_app())

    resp = client.get(
        "/api/v1/articles/feed",
        params={"topic_id": "topic-ai"},
    )
    assert resp.status_code == 401


def test_topic_feed_returns_404_for_missing_topic():
    client = TestClient(_build_test_app(topic_exists=False))
    headers = {"x-user-id": "user-1"}

    resp = client.get(
        "/api/v1/articles/feed",
        params={"topic_id": "missing-topic"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_repository_list_for_topic_uses_topic_name_pattern():
    session = _CaptureSession()
    repo = ArticleRepository(session)

    await repo.list_for_topic("AI", limit=10, offset=5)
    assert session.statement is not None

    compiled = session.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled).lower()
    params = compiled.params

    assert "articles.is_deleted = false" in sql
    assert sql.count("ilike") >= 3
    assert "limit" in sql
    assert "offset" in sql
    assert any("AI" in str(value) for value in params.values())
