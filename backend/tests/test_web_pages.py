from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.web import router as web_router
from core.dependencies import get_db
from repositories.sqlalchemy.analytics import AnalyticsRepository
from repositories.sqlalchemy.article import ArticleRepository


def _make_article(
    article_id: str,
    title: str,
    category: str = "tech",
    platform: str = "reddit",
    event_id: str = None,
):
    return SimpleNamespace(
        id=article_id,
        title=title,
        url=f"https://example.com/{article_id}",
        excerpt=f"{title} excerpt",
        summary=f"{title} summary",
        source=SimpleNamespace(name="SourceName"),
        category=category,
        metadata_={"platform": platform},
        published_at=datetime(2026, 5, 28, 10, 0, 0),
        created_at=datetime(2026, 5, 28, 10, 0, 0),
        event_id=event_id,
        is_deleted=False,
    )


def _build_app():
    app = FastAPI()
    app.include_router(web_router, prefix="/web")

    async def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    return app


def test_web_feed_page_renders_articles_and_filters(monkeypatch):
    app = _build_app()
    client = TestClient(app)

    async def fake_list(self, filters=None, order_by=None, limit=100, offset=0):
        if filters:
            return [_make_article("a-1", "Tech One", category=filters.get("category", "tech"))]
        return [
            _make_article("a-1", "Tech One", category="tech"),
            _make_article("a-2", "World One", category="world"),
        ]

    monkeypatch.setattr(ArticleRepository, "list", fake_list)

    resp = client.get("/web/feed")
    assert resp.status_code == 200
    assert "Tech One" in resp.text
    assert "World One" in resp.text
    assert "All" in resp.text

    resp_filtered = client.get("/web/feed?category=tech")
    assert resp_filtered.status_code == 200
    assert "Tech One" in resp_filtered.text


def test_web_hot_page_groups_by_platform(monkeypatch):
    app = _build_app()
    client = TestClient(app)

    async def fake_recent(self, category=None, limit=20):
        return [
            _make_article("h-1", "Hot A", category="hot", platform="reddit"),
            _make_article("h-2", "Hot B", category="hot", platform="reddit"),
            _make_article("h-3", "Hot C", category="hot", platform="hackernews"),
        ]

    monkeypatch.setattr(ArticleRepository, "get_recent", fake_recent)

    resp = client.get("/web/hot")
    assert resp.status_code == 200
    assert "Hot A" in resp.text
    assert "hackernews" in resp.text


def test_web_article_detail_and_not_found(monkeypatch):
    app = _build_app()
    client = TestClient(app)
    article = _make_article("d-1", "Detail One", event_id="evt-1")

    async def fake_get_by_id(self, article_id):
        return article if article_id == "d-1" else None

    async def fake_get_by_event_id(self, event_id):
        return [
            _make_article("d-1", "Detail One", event_id=event_id),
            _make_article("d-2", "Related One", event_id=event_id),
        ]

    monkeypatch.setattr(ArticleRepository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(ArticleRepository, "get_by_event_id", fake_get_by_event_id)

    resp_detail = client.get("/web/articles/d-1")
    assert resp_detail.status_code == 200
    assert "Detail One" in resp_detail.text
    assert "Related Coverage" in resp_detail.text

    resp_404 = client.get("/web/articles/not-found")
    assert resp_404.status_code == 404


def test_web_analytics_page_renders_summary(monkeypatch):
    app = _build_app()
    client = TestClient(app)

    async def fake_summary(self, *, days=7, user_id=None, session_id=None, event_name=None):
        return {
            "days": days,
            "total_events": 2,
            "events_by_name": [{"event": "discover_search", "count": 2}],
            "daily_counts": [{"date": "2026-05-29", "count": 2}],
            "user_id": user_id,
            "session_id": session_id,
            "event_filter": event_name,
        }

    async def fake_funnel(self, *, days=7, user_id=None, session_id=None):
        return {
            "days": days,
            "user_id": user_id,
            "session_id": session_id,
            "steps": {
                "search": 10,
                "category_select": 4,
                "topic_subscribe_attempts": 3,
                "topic_subscribe_success": 2,
                "keyword_subscribe_attempts": 1,
                "keyword_subscribe_success": 1,
                "subscribe_attempts": 4,
                "subscribe_success": 3,
            },
            "conversion_rates": {
                "search_to_category": 0.4,
                "search_to_subscribe_attempt": 0.4,
                "subscribe_attempt_to_success": 0.75,
            },
        }

    async def fake_related_funnel(self, *, days=7, user_id=None, session_id=None):
        return {
            "days": days,
            "user_id": user_id,
            "session_id": session_id,
            "steps": {
                "impression": 8,
                "swipe": 3,
                "click": 2,
                "view_all": 1,
                "article_open": 2,
            },
            "conversion_rates": {
                "impression_to_click": 0.25,
                "impression_to_view_all": 0.125,
                "swipe_to_click": 0.6667,
                "click_to_open": 1.0,
            },
        }

    async def fake_recent(self, *, limit=50, event_name=None, user_id=None, session_id=None):
        return [
            SimpleNamespace(
                id="evt-1",
                event_name="discover_search",
                params={"source": "button"},
                event_at=datetime(2026, 5, 29, 10, 0, 0),
                user_id="user-1",
                client_ip="127.0.0.1",
            )
        ]

    monkeypatch.setattr(AnalyticsRepository, "get_summary", fake_summary)
    monkeypatch.setattr(AnalyticsRepository, "get_funnel", fake_funnel)
    monkeypatch.setattr(AnalyticsRepository, "get_related_funnel", fake_related_funnel)
    monkeypatch.setattr(AnalyticsRepository, "list_recent_events", fake_recent)

    resp = client.get("/web/analytics?days=7")
    assert resp.status_code == 200
    assert "Client Analytics" in resp.text
    assert "discover_search" in resp.text
    assert "Total events" in resp.text
    assert "Discovery funnel" in resp.text
    assert "Related coverage funnel" in resp.text
    assert "Events by module" in resp.text
