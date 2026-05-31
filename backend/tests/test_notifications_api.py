from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import notifications as notifications_module
from api.v1.router import api_router
from core.dependencies import get_db
from services.push_topics import build_fcm_topic_name


class FakeNotificationService:
    def __init__(self, session):
        self.session = session
        self.tokens: list[dict] = []

    async def register_push_token(self, **kwargs):
        self.tokens.append(kwargs)

    async def get_user_notifications(self, user_id, *, is_read=None, limit=50):
        return [
            {
                "id": "n-1",
                "title": "Hello",
                "body": "World",
                "notification_type": "update",
                "is_read": False,
                "created_at": "2026-01-01T00:00:00",
            }
        ]

    async def get_unread_count(self, user_id):
        return 1

    async def mark_as_read(self, notification_id):
        return notification_id == "n-1"

    async def mark_all_as_read(self, user_id):
        return 2


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        notifications_module,
        "NotificationService",
        FakeNotificationService,
    )

    async def fake_get_db():
        session = SimpleNamespace()

        async def commit():
            return None

        session.commit = commit
        yield session

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[get_db] = fake_get_db
    return TestClient(app)


def test_build_fcm_topic_name_uses_topic_id():
    topic_id = "550e8400-e29b-41d4-a716-446655440000"
    assert build_fcm_topic_name(topic_id) == f"topic_{topic_id}"


def test_register_push_token(client):
    response = client.post(
        "/api/v1/notifications/register",
        headers={"x-user-id": "user-1"},
        json={
            "token": "fcm-token-abc",
            "platform": "android",
            "device_id": "pixel-8",
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_notifications(client):
    response = client.get(
        "/api/v1/notifications/",
        headers={"x-user-id": "user-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["title"] == "Hello"


def test_get_unread_count(client):
    response = client.get(
        "/api/v1/notifications/unread-count",
        headers={"x-user-id": "user-1"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.asyncio
async def test_push_article_to_matching_topics_skips_without_firebase(monkeypatch):
    from services.notification import NotificationService

    topic_id = str(uuid4())
    article_id = str(uuid4())

    class FakeTopicRepo:
        async def list_with_subscribers(self):
            return [
                SimpleNamespace(
                    id=topic_id,
                    name="NVIDIA",
                    subscriber_count=3,
                )
            ]

        async def get_by_id(self, topic_id_value):
            return SimpleNamespace(
                id=topic_id_value,
                subscriber_count=3,
            )

    class FakeArticleRepo:
        async def get_by_id(self, article_id_value):
            return SimpleNamespace(
                id=article_id_value,
                title="NVIDIA earnings beat expectations",
                content="Chip demand remains strong.",
                summary="NVIDIA reported strong earnings.",
                is_summary_generated=True,
            )

    sent_topics: list[str] = []

    async def fake_send(*, topic, title, body, data=None, priority="normal"):
        sent_topics.append(topic)
        return None

    class FakeSubscriptionRepo:
        async def get_topic_subscribers(self, topic_id_value):
            return []

    monkeypatch.setattr(
        "services.notification.send_fcm_topic_message",
        fake_send,
    )

    service = NotificationService(session=SimpleNamespace())
    service.topic_repo = FakeTopicRepo()
    service.article_repo = FakeArticleRepo()
    service.subscription_repo = FakeSubscriptionRepo()

    count = await service.push_article_to_matching_topics(article_id)
    assert count == 0
    assert sent_topics == [build_fcm_topic_name(topic_id)]
