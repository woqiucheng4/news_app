from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import subscriptions as subscriptions_module
from api.v1 import users as users_module
from api.v1.router import api_router


class FakeUserService:
    async def get_user(self, user_id: str):
        if user_id == "current_user_id":
            return {
                "id": "u-1",
                "email": "user@example.com",
                "username": "tester",
                "display_name": "Tester",
                "avatar_url": None,
                "is_active": True,
                "is_verified": True,
                "is_premium": False,
                "created_at": "2026-01-01T00:00:00",
            }
        return None

    async def update_settings(self, user_id: str, settings: dict):
        return True

    async def export_user_data(self, user_id: str):
        return {"user": {"id": "u-1"}, "settings": {}, "exported_at": "2026-01-01T00:00:00"}

    async def delete_user(self, user_id: str):
        return True


class FakeTopicRepo:
    def __init__(self, _db):
        pass

    async def search(self, q: str, limit: int = 20):
        return [SimpleNamespace(id="t-1", name="AI", slug="ai", description="d", category="tech", subscriber_count=10)]

    async def get_by_category(self, category: str):
        return [SimpleNamespace(id="t-2", name="ML", slug="ml", description="d", category=category, subscriber_count=8)]

    async def get_popular(self, limit: int = 20):
        return [SimpleNamespace(id="t-3", name="News", slug="news", description="d", category="general", subscriber_count=20)]

    async def list_categories(self):
        return [
            {"name": "tech", "topic_count": 2},
            {"name": "finance", "topic_count": 1},
        ]

    async def get_by_id(self, topic_id: str):
        if topic_id == "missing-topic":
            return None
        return SimpleNamespace(id=topic_id, name="Topic", slug="topic", description="d", category="tech", subscriber_count=9)

    async def get_by_slug(self, slug: str):
        if slug == "keyword-ai":
            return SimpleNamespace(id="t-keyword", name="AI", slug=slug, description="d", category="custom", subscriber_count=5)
        return None

    async def create(self, data: dict):
        return SimpleNamespace(
            id="t-keyword-new",
            name=data["name"],
            slug=data["slug"],
            description=data.get("description"),
            category=data.get("category"),
            subscriber_count=0,
        )

    async def increment_subscriber(self, topic_id: str, delta: int):
        return True


class FakeSubscriptionRepo:
    def __init__(self, _db):
        self.existing = None

    async def get_user_subscriptions(self, user_id: str, limit: int = 100, offset: int = 0):
        topic = SimpleNamespace(id="t-1", name="AI", slug="ai", description="d", category="tech", subscriber_count=10)
        return [
            SimpleNamespace(
                id="s-1",
                topic=topic,
                is_active=True,
                priority=0,
                push_enabled=True,
                push_breaking_only=False,
                subscribed_at=datetime(2026, 1, 1, 0, 0, 0),
            )
        ]

    async def get_by_user_and_topic(self, user_id: str, topic_id: str, include_deleted: bool = False):
        if topic_id == "already":
            return SimpleNamespace(id="s-existing", is_active=True, is_deleted=False)
        if topic_id == "inactive":
            return SimpleNamespace(id="s-inactive", is_active=False, is_deleted=False)
        if topic_id == "missing":
            return None
        if topic_id == "t-keyword":
            return SimpleNamespace(id="s-keyword", is_active=True, is_deleted=False)
        return None

    async def is_subscribed(self, user_id: str, topic_id: str):
        return topic_id in {"t-1", "t-100", "t-keyword"}

    async def update(self, subscription_id: str, data: dict):
        return True

    async def create(self, data: dict):
        return SimpleNamespace(id="s-new")

    async def delete(self, subscription_id: str):
        return True


def _build_test_app():
    app = FastAPI()
    app.include_router(api_router)

    async def override_user_service():
        return FakeUserService()

    async def override_db():
        yield object()

    app.dependency_overrides[users_module.get_user_service] = override_user_service
    app.dependency_overrides[users_module.get_db] = override_db
    app.dependency_overrides[subscriptions_module.get_db] = override_db
    return app


def test_user_api_endpoints():
    app = _build_test_app()
    client = TestClient(app)
    headers = {"x-user-id": "current_user_id"}

    resp_me = client.get("/api/v1/users/me", headers=headers)
    assert resp_me.status_code == 200
    assert resp_me.json()["id"] == "u-1"

    resp_settings = client.put("/api/v1/users/me/settings", json={"theme": "dark"}, headers=headers)
    assert resp_settings.status_code == 200
    assert resp_settings.json()["success"] is True

    resp_export = client.get("/api/v1/users/me/export", headers=headers)
    assert resp_export.status_code == 200
    assert resp_export.json()["user"]["id"] == "u-1"

    resp_delete = client.delete("/api/v1/users/me", headers=headers)
    assert resp_delete.status_code == 200
    assert resp_delete.json()["success"] is True


def test_subscription_api_endpoints(monkeypatch):
    app = _build_test_app()
    client = TestClient(app)

    monkeypatch.setattr(subscriptions_module, "TopicRepository", FakeTopicRepo)
    monkeypatch.setattr(subscriptions_module, "SubscriptionRepository", FakeSubscriptionRepo)
    headers = {"x-user-id": "current_user_id"}

    resp_categories = client.get("/api/v1/subscriptions/topics/categories", headers=headers)
    assert resp_categories.status_code == 200
    assert resp_categories.json()[0]["name"] == "tech"

    resp_topics_q = client.get("/api/v1/subscriptions/topics", params={"q": "ai"}, headers=headers)
    assert resp_topics_q.status_code == 200
    assert resp_topics_q.json()[0]["slug"] == "ai"

    resp_topics_category = client.get("/api/v1/subscriptions/topics", params={"category": "tech"}, headers=headers)
    assert resp_topics_category.status_code == 200

    resp_topics_popular = client.get("/api/v1/subscriptions/topics", headers=headers)
    assert resp_topics_popular.status_code == 200

    resp_topic_detail = client.get("/api/v1/subscriptions/topics/t-100", headers=headers)
    assert resp_topic_detail.status_code == 200
    assert resp_topic_detail.json()["id"] == "t-100"
    assert resp_topic_detail.json()["is_subscribed"] is True

    resp_my = client.get("/api/v1/subscriptions/me", headers=headers)
    assert resp_my.status_code == 200
    assert len(resp_my.json()) == 1
    assert "push_breaking_only" in resp_my.json()[0]

    resp_subscribe_create = client.post(
        "/api/v1/subscriptions/subscribe",
        json={"topic_id": "new-topic", "push_enabled": True},
        headers=headers,
    )
    assert resp_subscribe_create.status_code == 200
    assert resp_subscribe_create.json()["success"] is True

    resp_subscribe_update = client.post(
        "/api/v1/subscriptions/subscribe",
        json={"topic_id": "already", "push_enabled": False},
        headers=headers,
    )
    assert resp_subscribe_update.status_code == 200

    resp_keyword = client.post(
        "/api/v1/subscriptions/subscribe/keyword",
        json={"keyword": "AI"},
        headers=headers,
    )
    assert resp_keyword.status_code == 200
    assert resp_keyword.json()["topic"]["slug"] == "keyword-ai"

    resp_update = client.patch(
        "/api/v1/subscriptions/me/already",
        json={"priority": 9, "push_breaking_only": True},
        headers=headers,
    )
    assert resp_update.status_code == 200

    resp_reorder = client.put(
        "/api/v1/subscriptions/me/reorder",
        json={"items": [{"topic_id": "already", "priority": 3}]},
        headers=headers,
    )
    assert resp_reorder.status_code == 200
    assert resp_reorder.json()["updated"] == 1

    resp_unsub_404 = client.delete("/api/v1/subscriptions/unsubscribe/missing", headers=headers)
    assert resp_unsub_404.status_code == 404

    # Patch get_by_user_and_topic to always return subscription for successful unsubscribe.
    class SuccessfulUnsubRepo(FakeSubscriptionRepo):
        async def get_by_user_and_topic(self, user_id: str, topic_id: str, include_deleted: bool = False):
            return SimpleNamespace(id="s-x", is_active=True, is_deleted=False)

    monkeypatch.setattr(subscriptions_module, "SubscriptionRepository", SuccessfulUnsubRepo)
    resp_unsub = client.delete("/api/v1/subscriptions/unsubscribe/topic-ok", headers=headers)
    assert resp_unsub.status_code == 200
    assert resp_unsub.json()["success"] is True


def test_keyword_subscribe_is_idempotent(monkeypatch):
    app = _build_test_app()
    client = TestClient(app)
    headers = {"x-user-id": "current_user_id"}

    class StatefulTopicRepo(FakeTopicRepo):
        topic_id = "t-keyword-idempotent"
        create_calls = 0
        increment_calls = []

        async def get_by_slug(self, slug: str):
            if slug == "keyword-ai":
                return SimpleNamespace(
                    id=self.topic_id,
                    name="AI",
                    slug=slug,
                    description="d",
                    category="custom",
                    subscriber_count=0,
                )
            return None

        async def create(self, data: dict):
            type(self).create_calls += 1
            return SimpleNamespace(
                id=self.topic_id,
                name=data["name"],
                slug=data["slug"],
                description=data.get("description"),
                category=data.get("category"),
                subscriber_count=0,
            )

        async def increment_subscriber(self, topic_id: str, delta: int):
            type(self).increment_calls.append((topic_id, delta))
            return True

    class StatefulSubscriptionRepo(FakeSubscriptionRepo):
        created = False
        create_calls = 0
        update_calls = 0
        include_deleted_flags = []

        async def get_by_user_and_topic(self, user_id: str, topic_id: str, include_deleted: bool = False):
            type(self).include_deleted_flags.append(include_deleted)
            if topic_id == StatefulTopicRepo.topic_id and type(self).created:
                return SimpleNamespace(id="s-keyword-idempotent", is_active=True, is_deleted=False)
            return None

        async def create(self, data: dict):
            type(self).created = True
            type(self).create_calls += 1
            return SimpleNamespace(id="s-keyword-idempotent")

        async def update(self, subscription_id: str, data: dict):
            type(self).update_calls += 1
            return True

    monkeypatch.setattr(subscriptions_module, "TopicRepository", StatefulTopicRepo)
    monkeypatch.setattr(subscriptions_module, "SubscriptionRepository", StatefulSubscriptionRepo)

    resp_first = client.post(
        "/api/v1/subscriptions/subscribe/keyword",
        json={"keyword": "AI"},
        headers=headers,
    )
    resp_second = client.post(
        "/api/v1/subscriptions/subscribe/keyword",
        json={"keyword": "AI"},
        headers=headers,
    )

    assert resp_first.status_code == 200
    assert resp_second.status_code == 200
    assert resp_first.json()["topic"]["id"] == resp_second.json()["topic"]["id"]
    assert StatefulSubscriptionRepo.create_calls == 1
    assert StatefulSubscriptionRepo.update_calls == 1
    assert all(StatefulSubscriptionRepo.include_deleted_flags)
    assert StatefulTopicRepo.increment_calls == [(StatefulTopicRepo.topic_id, 1)]


def test_resubscribe_reactivates_cancelled_subscription(monkeypatch):
    app = _build_test_app()
    client = TestClient(app)
    headers = {"x-user-id": "current_user_id"}
    target_topic_id = "topic-reactivate"

    class StatefulTopicRepo(FakeTopicRepo):
        increment_calls = []

        async def get_by_id(self, topic_id: str):
            return SimpleNamespace(
                id=topic_id,
                name="AI",
                slug="ai",
                description="d",
                category="tech",
                subscriber_count=3,
            )

        async def increment_subscriber(self, topic_id: str, delta: int):
            type(self).increment_calls.append((topic_id, delta))
            return True

    class StatefulSubscriptionRepo(FakeSubscriptionRepo):
        is_active = True
        create_calls = 0
        include_deleted_flags = []
        update_payloads = []

        async def get_by_user_and_topic(self, user_id: str, topic_id: str, include_deleted: bool = False):
            if topic_id != target_topic_id:
                return None
            type(self).include_deleted_flags.append(include_deleted)
            return SimpleNamespace(
                id="s-reactivate",
                is_active=type(self).is_active,
                is_deleted=False,
            )

        async def update(self, subscription_id: str, data: dict):
            type(self).update_payloads.append(data)
            if data.get("is_active") is False:
                type(self).is_active = False
            if data.get("is_active") is True:
                type(self).is_active = True
            return True

        async def create(self, data: dict):
            type(self).create_calls += 1
            return SimpleNamespace(id="s-new-should-not-happen")

    monkeypatch.setattr(subscriptions_module, "TopicRepository", StatefulTopicRepo)
    monkeypatch.setattr(subscriptions_module, "SubscriptionRepository", StatefulSubscriptionRepo)

    resp_unsubscribe = client.delete(f"/api/v1/subscriptions/unsubscribe/{target_topic_id}", headers=headers)
    resp_resubscribe = client.post(
        "/api/v1/subscriptions/subscribe",
        json={"topic_id": target_topic_id},
        headers=headers,
    )

    assert resp_unsubscribe.status_code == 200
    assert resp_resubscribe.status_code == 200
    assert StatefulSubscriptionRepo.create_calls == 0
    assert any(payload.get("is_active") is False for payload in StatefulSubscriptionRepo.update_payloads)
    assert any(payload.get("is_active") is True for payload in StatefulSubscriptionRepo.update_payloads)
    assert StatefulSubscriptionRepo.include_deleted_flags[-1] is True
    assert StatefulTopicRepo.increment_calls == [
        (target_topic_id, -1),
        (target_topic_id, 1),
    ]
