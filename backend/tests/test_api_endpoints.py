from pathlib import Path
from types import SimpleNamespace
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import articles as articles_module
from api.v1 import dashboard as dashboard_module
from api.v1.router import api_router


class FakeArticleService:
    async def get_feed(self, user_id: str, page: int = 1, page_size: int = 20):
        return {
            "page": page,
            "page_size": page_size,
            "articles": [],
            "has_more": False,
        }

    async def search_articles(self, query: str, limit: int = 20):
        return []

    async def get_trending(self, limit: int = 20):
        return [
            {
                "id": "e-1",
                "title": "Event title",
                "summary": "Event summary",
                "category": "tech",
                "article_count": 3,
                "source_count": 2,
                "last_updated_at": "2026-01-01T00:00:00",
            }
        ]

    async def get_article(self, article_id: str):
        if article_id == "not-found":
            return None
        return {
            "id": article_id,
            "title": "Article",
            "url": "https://example.com/a",
            "excerpt": None,
            "summary": None,
            "author": None,
            "source": None,
            "category": None,
            "tags": [],
            "published_at": None,
            "created_at": "2026-01-01T00:00:00",
            "view_count": 0,
            "bookmark_count": 0,
            "related_articles": [],
            "related_articles_total": 0,
        }

    async def get_related_articles(self, article_id: str, page: int = 1, page_size: int = 20):
        if article_id == "not-found":
            return None
        return {
            "page": page,
            "page_size": page_size,
            "articles": [],
            "has_more": False,
            "total": 0,
        }

    async def generate_summary(self, article_id: str):
        if article_id == "not-found":
            return None
        return "summary text"


class FakeCostService:
    def __init__(self, *args, **kwargs):
        pass

    async def get_daily_summary(self, date_value=None):
        return {
            "date": "2026-05-28",
            "total_cost_usd": 0.12,
            "total_requests": 10,
            "total_tokens": 1000,
            "budget_usd": 5.0,
            "budget_used_percent": 2.4,
            "remaining_usd": 4.88,
            "degradation_level": "normal",
        }

    async def get_cost_trend(self, days: int = 7):
        return [
            {"date": "2026-05-27", "cost_usd": 0.1, "requests": 8},
            {"date": "2026-05-28", "cost_usd": 0.12, "requests": 10},
        ]


def _build_test_app():
    app = FastAPI()
    app.include_router(api_router)

    async def override_article_service():
        return FakeArticleService()

    async def override_db():
        yield object()

    app.dependency_overrides[articles_module.get_article_service] = override_article_service
    app.dependency_overrides[dashboard_module.get_db] = override_db
    return app


def test_articles_endpoints_basic_flow(monkeypatch):
    app = _build_test_app()
    client = TestClient(app)
    headers = {"x-user-id": "current_user_id"}

    resp_feed = client.get("/api/v1/articles/feed", headers=headers)
    assert resp_feed.status_code == 200
    assert resp_feed.json()["page"] == 1

    resp_search = client.get("/api/v1/articles/search", params={"q": "ai"}, headers=headers)
    assert resp_search.status_code == 200

    resp_trending = client.get("/api/v1/articles/trending", headers=headers)
    assert resp_trending.status_code == 200
    assert resp_trending.json()[0]["article_count"] == 3

    resp_detail = client.get("/api/v1/articles/a-1", headers=headers)
    assert resp_detail.status_code == 200
    assert resp_detail.json()["id"] == "a-1"
    assert resp_detail.json()["related_articles"] == []
    assert resp_detail.json()["related_articles_total"] == 0

    resp_related = client.get("/api/v1/articles/a-1/related", headers=headers)
    assert resp_related.status_code == 200
    assert resp_related.json()["total"] == 0

    resp_404 = client.get("/api/v1/articles/not-found", headers=headers)
    assert resp_404.status_code == 404

    resp_summary = client.post("/api/v1/articles/a-1/summary", headers=headers)
    assert resp_summary.status_code == 200
    assert resp_summary.json()["summary"] == "summary text"


def test_dashboard_endpoints_basic_flow(monkeypatch):
    app = _build_test_app()
    client = TestClient(app)

    monkeypatch.setattr(dashboard_module, "CostService", FakeCostService)
    monkeypatch.setattr(dashboard_module, "CostRepository", lambda _db: object())
    monkeypatch.setattr(
        dashboard_module,
        "get_settings",
        lambda: SimpleNamespace(ai=SimpleNamespace(ai_daily_budget_usd=5.0, ai_monthly_budget_usd=100.0)),
    )

    async def fake_health_check():
        return {
            "database": {"write": True, "read_engines": [{"index": 0, "status": True}]},
            "cache": {"redis": True},
            "tasks": True,
            "storage": True,
            "ai": {"openai": True},
        }

    monkeypatch.setattr(dashboard_module.services, "health_check", fake_health_check)

    resp_summary = client.get("/api/v1/dashboard/cost/summary")
    assert resp_summary.status_code == 200
    assert resp_summary.json()["degradation_level"] == "normal"

    resp_trend = client.get("/api/v1/dashboard/cost/trend", params={"days": 2})
    assert resp_trend.status_code == 200
    assert len(resp_trend.json()) == 2

    resp_health = client.get("/api/v1/dashboard/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["tasks"] is True
