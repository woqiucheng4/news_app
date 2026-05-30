from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import analytics as analytics_module
from api.v1.router import api_router
from core import dependencies as deps_module
from services.analytics import AnalyticsService


class FakeAnalyticsRepository:
    """In-memory analytics repository for API tests."""

    def __init__(self):
        self.events: list[dict] = []

    async def create_event(self, data: dict):
        event = {
            "id": uuid4(),
            "event_name": data["event_name"],
            "params": data.get("params", {}),
            "event_at": data["event_at"],
            "user_id": data.get("user_id"),
            "session_id": data.get("session_id"),
            "client_ip": data.get("client_ip"),
            "is_deleted": False,
        }
        self.events.append(event)
        return SimpleNamespace(**event)

    async def get_summary(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: Optional[str] = None,
    ):
        since = datetime.now(timezone.utc) - timedelta(days=days)
        active = [
            event
            for event in self.events
            if not event["is_deleted"]
            and event["event_at"] >= since.replace(tzinfo=None)
            and (user_id is None or event.get("user_id") == user_id)
            and (session_id is None or event.get("session_id") == session_id)
            and (event_name is None or event["event_name"] == event_name)
        ]

        by_name: dict[str, int] = {}
        daily: dict[str, int] = {}
        for event in active:
            by_name[event["event_name"]] = by_name.get(event["event_name"], 0) + 1
            day = event["event_at"].date().isoformat()
            daily[day] = daily.get(day, 0) + 1

        return {
            "days": days,
            "total_events": len(active),
            "events_by_name": [
                {"event": name, "count": count}
                for name, count in sorted(by_name.items(), key=lambda item: item[1], reverse=True)
            ],
            "daily_counts": [
                {"date": day, "count": count}
                for day, count in sorted(daily.items())
            ],
            "user_id": user_id,
            "session_id": session_id,
            "event_filter": event_name,
        }

    async def list_recent_events(
        self,
        *,
        limit: int = 50,
        event_name: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        rows = [
            event
            for event in self.events
            if not event["is_deleted"]
            and (event_name is None or event["event_name"] == event_name)
            and (user_id is None or event.get("user_id") == user_id)
            and (session_id is None or event.get("session_id") == session_id)
        ]
        rows.sort(key=lambda item: item["event_at"], reverse=True)
        return [SimpleNamespace(**row) for row in rows[:limit]]

    async def purge_events_older_than(self, *, retention_days: int):
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = 0
        kept = []
        for event in self.events:
            if event["event_at"] < cutoff.replace(tzinfo=None):
                deleted += 1
            else:
                kept.append(event)
        self.events = kept
        return deleted

    async def get_funnel(self, *, days: int = 7, user_id: Optional[str] = None, session_id: Optional[str] = None):
        since = datetime.now(timezone.utc) - timedelta(days=days)

        def _count(event_name: str, success: Optional[bool] = None) -> int:
            total = 0
            for event in self.events:
                if event["is_deleted"]:
                    continue
                if event["event_at"] < since.replace(tzinfo=None):
                    continue
                if event["event_name"] != event_name:
                    continue
                if user_id is not None and event.get("user_id") != user_id:
                    continue
                if session_id is not None and event.get("session_id") != session_id:
                    continue
                if success is not None and event.get("params", {}).get("success") != success:
                    continue
                total += 1
            return total

        search_count = _count("discover_search")
        category_count = _count("discover_category_select")
        topic_attempts = _count("discover_topic_subscribe")
        topic_success = _count("discover_topic_subscribe", success=True)
        keyword_attempts = _count("discover_keyword_subscribe")
        keyword_success = _count("discover_keyword_subscribe", success=True)
        subscribe_attempts = topic_attempts + keyword_attempts
        subscribe_success = topic_success + keyword_success

        def _rate(numerator: int, denominator: int):
            if denominator <= 0:
                return None
            return round(numerator / denominator, 4)

        return {
            "days": days,
            "user_id": user_id,
            "session_id": session_id,
            "steps": {
                "search": search_count,
                "category_select": category_count,
                "topic_subscribe_attempts": topic_attempts,
                "topic_subscribe_success": topic_success,
                "keyword_subscribe_attempts": keyword_attempts,
                "keyword_subscribe_success": keyword_success,
                "subscribe_attempts": subscribe_attempts,
                "subscribe_success": subscribe_success,
            },
            "conversion_rates": {
                "search_to_category": _rate(category_count, search_count),
                "search_to_subscribe_attempt": _rate(subscribe_attempts, search_count),
                "subscribe_attempt_to_success": _rate(subscribe_success, subscribe_attempts),
            },
        }

    async def get_related_funnel(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        since = datetime.now(timezone.utc) - timedelta(days=days)

        def _count(event_name: str) -> int:
            total = 0
            for event in self.events:
                if event["is_deleted"]:
                    continue
                if event["event_at"] < since.replace(tzinfo=None):
                    continue
                if event["event_name"] != event_name:
                    continue
                if user_id is not None and event.get("user_id") != user_id:
                    continue
                if session_id is not None and event.get("session_id") != session_id:
                    continue
                total += 1
            return total

        def _count_param(event_name: str, param_key: str, param_value: str) -> int:
            total = 0
            for event in self.events:
                if event["is_deleted"]:
                    continue
                if event["event_at"] < since.replace(tzinfo=None):
                    continue
                if event["event_name"] != event_name:
                    continue
                if event.get("params", {}).get(param_key) != param_value:
                    continue
                if user_id is not None and event.get("user_id") != user_id:
                    continue
                if session_id is not None and event.get("session_id") != session_id:
                    continue
                total += 1
            return total

        impression = _count("feed_related_impression")
        swipe = _count("feed_related_swipe")
        click = _count("feed_related_click")
        view_all = _count("feed_related_view_all")
        article_open = _count_param("feed_article_open", "source", "related_article")

        def _rate(numerator: int, denominator: int):
            if denominator <= 0:
                return None
            return round(numerator / denominator, 4)

        return {
            "days": days,
            "user_id": user_id,
            "session_id": session_id,
            "steps": {
                "impression": impression,
                "swipe": swipe,
                "click": click,
                "view_all": view_all,
                "article_open": article_open,
            },
            "conversion_rates": {
                "impression_to_click": _rate(click, impression),
                "impression_to_view_all": _rate(view_all, impression),
                "swipe_to_click": _rate(click, swipe),
                "click_to_open": _rate(article_open, click),
            },
        }


def _build_test_app(fake_repo: Optional[FakeAnalyticsRepository] = None):
    app = FastAPI()
    app.include_router(api_router)
    repo = fake_repo or FakeAnalyticsRepository()

    async def override_analytics_service():
        return AnalyticsService(repo)

    async def override_current_user_id():
        return "user-1"

    app.dependency_overrides[analytics_module.get_analytics_service] = override_analytics_service
    app.dependency_overrides[deps_module.get_current_user_id] = override_current_user_id
    return app, repo


def test_ingest_analytics_event_success():
    app, repo = _build_test_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event": "discover_search",
            "params": {
                "query": "ai",
                "source": "button",
                "category": "tech",
                "unexpected": "ignored",
            },
            "ts": "2026-05-29T10:00:00Z",
        },
        headers={"X-User-Id": "user-1"},
    )

    assert response.status_code == 202
    assert response.json()["success"] is True
    assert repo.events[0]["user_id"] == "user-1"


def test_ingest_analytics_event_stores_session_id():
    app, repo = _build_test_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event": "discover_search",
            "params": {"query": "ai", "source": "button", "category": ""},
        },
        headers={"X-Session-Id": "session-abc"},
    )

    assert response.status_code == 202
    assert repo.events[0]["session_id"] == "session-abc"


def test_ingest_analytics_event_rejects_unknown_event():
    client = TestClient(_build_test_app()[0])

    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event": "unknown_event",
            "params": {"foo": "bar"},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported event"


def test_ingest_analytics_event_rejects_invalid_event_name():
    client = TestClient(_build_test_app()[0])

    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event": "Bad-Event",
            "params": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid event name"


def test_get_analytics_summary():
    app, repo = _build_test_app()
    repo.events.append(
        {
            "id": uuid4(),
            "event_name": "discover_search",
            "params": {"query": "ai", "source": "button"},
            "event_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "user_id": "user-1",
            "client_ip": "127.0.0.1",
            "is_deleted": False,
        }
    )
    client = TestClient(app)

    response = client.get("/api/v1/analytics/summary?days=7")

    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 1
    assert body["events_by_name"][0]["event"] == "discover_search"
    assert body["events_by_name"][0]["count"] == 1


def test_get_recent_analytics_events():
    app, repo = _build_test_app()
    repo.events.append(
        {
            "id": uuid4(),
            "event_name": "discover_category_select",
            "params": {"category": "tech", "source": "chip"},
            "event_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "user_id": None,
            "client_ip": None,
            "is_deleted": False,
        }
    )
    client = TestClient(app)

    response = client.get("/api/v1/analytics/events/recent?limit=10")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["event"] == "discover_category_select"
    assert body[0]["params"]["category"] == "tech"


def test_get_analytics_summary_filters_by_user():
    app, repo = _build_test_app()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo.events.extend(
        [
            {
                "id": uuid4(),
                "event_name": "discover_search",
                "params": {},
                "event_at": now,
                "user_id": "user-a",
                "client_ip": None,
                "is_deleted": False,
            },
            {
                "id": uuid4(),
                "event_name": "discover_search",
                "params": {},
                "event_at": now,
                "user_id": "user-b",
                "client_ip": None,
                "is_deleted": False,
            },
        ]
    )
    client = TestClient(app)

    response = client.get("/api/v1/analytics/summary?days=7&user_id=user-a")

    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 1
    assert body["user_id"] == "user-a"


def test_purge_old_events():
    repo = FakeAnalyticsRepository()
    service = AnalyticsService(repo)
    old = datetime.now(timezone.utc) - timedelta(days=120)
    repo.events.append(
        {
            "id": uuid4(),
            "event_name": "discover_search",
            "params": {},
            "event_at": old.replace(tzinfo=None),
            "user_id": None,
            "client_ip": None,
            "is_deleted": False,
        }
    )

    import asyncio

    deleted_count = asyncio.run(service.purge_old_events(retention_days=90))

    assert deleted_count == 1
    assert len(repo.events) == 0


def test_get_analytics_funnel():
    app, repo = _build_test_app()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo.events.extend(
        [
            {
                "id": uuid4(),
                "event_name": "discover_search",
                "params": {"query": "ai", "source": "button"},
                "event_at": now,
                "user_id": "user-1",
                "client_ip": None,
                "is_deleted": False,
            },
            {
                "id": uuid4(),
                "event_name": "discover_topic_subscribe",
                "params": {"topic_id": "t-1", "success": True},
                "event_at": now,
                "user_id": "user-1",
                "client_ip": None,
                "is_deleted": False,
            },
        ]
    )
    client = TestClient(app)

    response = client.get("/api/v1/analytics/funnel?days=7")

    assert response.status_code == 200
    body = response.json()
    assert body["steps"]["search"] == 1
    assert body["steps"]["topic_subscribe_success"] == 1
    assert body["conversion_rates"]["search_to_subscribe_attempt"] == 1.0


def test_get_related_analytics_funnel():
    app, repo = _build_test_app()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo.events.extend(
        [
            {
                "id": uuid4(),
                "event_name": "feed_related_impression",
                "params": {"article_id": "a-1", "source": "detail_section"},
                "event_at": now,
                "user_id": "user-1",
                "client_ip": None,
                "is_deleted": False,
            },
            {
                "id": uuid4(),
                "event_name": "feed_related_click",
                "params": {
                    "article_id": "a-1",
                    "related_article_id": "a-2",
                    "source": "detail_section",
                },
                "event_at": now,
                "user_id": "user-1",
                "client_ip": None,
                "is_deleted": False,
            },
            {
                "id": uuid4(),
                "event_name": "feed_article_open",
                "params": {"article_id": "a-2", "source": "related_article"},
                "event_at": now,
                "user_id": "user-1",
                "client_ip": None,
                "is_deleted": False,
            },
        ]
    )
    client = TestClient(app)

    response = client.get("/api/v1/analytics/related-funnel?days=7")

    assert response.status_code == 200
    body = response.json()
    assert body["steps"]["impression"] == 1
    assert body["steps"]["click"] == 1
    assert body["steps"]["article_open"] == 1
    assert body["conversion_rates"]["impression_to_click"] == 1.0
    assert body["conversion_rates"]["click_to_open"] == 1.0


def test_my_related_analytics_funnel():
    app, repo = _build_test_app()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo.events.append(
        {
            "id": uuid4(),
            "event_name": "feed_related_impression",
            "params": {"article_id": "a-1", "source": "detail_section"},
            "event_at": now,
            "user_id": "user-1",
            "session_id": "session-xyz",
            "client_ip": None,
            "is_deleted": False,
        }
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics/me/related-funnel?days=7&scope=session&session_id=session-xyz"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["steps"]["impression"] == 1
    assert body["session_id"] == "session-xyz"


def test_analytics_summary_requires_dashboard_token_when_configured(monkeypatch):
    monkeypatch.setenv("ANALYTICS_DASHBOARD_TOKEN", "secret-token")

    from core.config import get_settings

    get_settings.cache_clear()
    try:
        client = TestClient(_build_test_app()[0])

        denied = client.get("/api/v1/analytics/summary?days=7")
        assert denied.status_code == 403

        allowed = client.get(
            "/api/v1/analytics/summary?days=7",
            headers={"X-Analytics-Token": "secret-token"},
        )
        assert allowed.status_code == 200
    finally:
        monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)
        get_settings.cache_clear()


def test_ingest_feed_and_subscription_events():
    app, repo = _build_test_app()
    client = TestClient(app)

    events = [
        ("feed_refresh", {"source": "pull"}),
        ("feed_article_open", {"article_id": "a-1", "source": "feed_list"}),
        (
            "feed_related_click",
            {
                "article_id": "a-1",
                "related_article_id": "a-2",
                "source": "detail_section",
            },
        ),
        (
            "feed_related_impression",
            {
                "article_id": "a-1",
                "visible_count": 3,
                "total_count": 5,
                "source": "detail_section",
                "display_state": "content",
            },
        ),
        (
            "feed_related_swipe",
            {
                "article_id": "a-1",
                "source": "detail_section",
                "scroll_offset": 120,
                "max_scroll_extent": 480,
            },
        ),
        ("subscription_push_toggle", {"topic_id": "t-1", "enabled": True, "success": True}),
        ("subscription_unsubscribe", {"topic_id": "t-2", "success": True}),
        ("subscription_list_refresh", {"source": "pull"}),
    ]

    for event_name, params in events:
        response = client.post(
            "/api/v1/analytics/events",
            json={"event": event_name, "params": params},
        )
        assert response.status_code == 202, event_name

    assert len(repo.events) == len(events)


def test_my_analytics_funnel_user_scope():
    app, repo = _build_test_app()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo.events.extend(
        [
            {
                "id": uuid4(),
                "event_name": "discover_search",
                "params": {"query": "ai", "source": "button", "category": ""},
                "event_at": now,
                "user_id": "user-1",
                "session_id": "session-1",
                "client_ip": None,
                "is_deleted": False,
            },
            {
                "id": uuid4(),
                "event_name": "discover_search",
                "params": {"query": "ml", "source": "button", "category": ""},
                "event_at": now,
                "user_id": "user-2",
                "session_id": "session-2",
                "client_ip": None,
                "is_deleted": False,
            },
        ]
    )
    client = TestClient(app)

    response = client.get("/api/v1/analytics/me/funnel?days=7&scope=user")

    assert response.status_code == 200
    body = response.json()
    assert body["steps"]["search"] == 1
    assert body["user_id"] == "user-1"


def test_my_analytics_funnel_session_scope():
    app, repo = _build_test_app()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    repo.events.append(
        {
            "id": uuid4(),
            "event_name": "discover_topic_subscribe",
            "params": {"topic_id": "t-1", "success": True},
            "event_at": now,
            "user_id": "user-1",
            "session_id": "session-xyz",
            "client_ip": None,
            "is_deleted": False,
        }
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics/me/funnel?days=7&scope=session&session_id=session-xyz"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["steps"]["topic_subscribe_success"] == 1
    assert body["session_id"] == "session-xyz"


def test_analytics_summary_allows_admin_jwt(monkeypatch):
    monkeypatch.setenv("ANALYTICS_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)

    from core.config import get_settings
    from core.security import create_access_token

    get_settings.cache_clear()
    try:
        client = TestClient(_build_test_app()[0])
        token = create_access_token(subject="admin-1", email="admin@example.com", is_admin=True)

        response = client.get(
            "/api/v1/analytics/summary?days=7",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
    finally:
        monkeypatch.delenv("ANALYTICS_ADMIN_EMAILS", raising=False)
        get_settings.cache_clear()


def test_analytics_export_csv_requires_dashboard_token(monkeypatch):
    monkeypatch.setenv("ANALYTICS_DASHBOARD_TOKEN", "secret-token")
    monkeypatch.delenv("ANALYTICS_ADMIN_EMAILS", raising=False)

    from core.config import get_settings

    get_settings.cache_clear()
    try:
        client = TestClient(_build_test_app()[0])
        response = client.get("/api/v1/analytics/export.csv?days=7")
        assert response.status_code == 403
    finally:
        monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)
        get_settings.cache_clear()


def test_analytics_export_csv_returns_attachment(monkeypatch):
    monkeypatch.setenv("ANALYTICS_DASHBOARD_TOKEN", "export-token")

    from core.config import get_settings

    get_settings.cache_clear()
    try:
        app, _repo = _build_test_app()
        client = TestClient(app)

        client.post(
            "/api/v1/analytics/events",
            json={"event": "discover_search", "params": {"query": "ai"}},
        )

        response = client.get(
            "/api/v1/analytics/export.csv?days=7",
            headers={"X-Analytics-Token": "export-token"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "discover_search" in response.text
        assert "section,metric,value" in response.text
    finally:
        monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)
        get_settings.cache_clear()
