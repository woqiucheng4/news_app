from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.notification import NotificationService
from services.push_topics import build_fcm_topic_name


@pytest.mark.asyncio
async def test_push_article_sends_premium_priority_tokens(monkeypatch):
    topic_id = str(uuid4())
    article_id = str(uuid4())
    premium_user_id = str(uuid4())

    class FakeTopicRepo:
        async def list_with_subscribers(self):
            return [SimpleNamespace(id=topic_id, name="AI", subscriber_count=2)]

        async def get_by_id(self, topic_id_value):
            return SimpleNamespace(id=topic_id_value, subscriber_count=2)

    class FakeArticleRepo:
        async def get_by_id(self, article_id_value):
            return SimpleNamespace(
                id=article_id_value,
                title="AI breakthrough announced",
                content="Major AI news today.",
                summary="AI models improve again.",
                is_summary_generated=True,
            )

    class FakeSubscriptionRepo:
        async def get_topic_subscribers(self, topic_id_value):
            assert topic_id_value == topic_id
            return [premium_user_id]

    class FakeUserRepo:
        async def get_by_id(self, user_id):
            return SimpleNamespace(is_premium_active=True)

    class FakePushTokenRepo:
        async def list_active_tokens_for_user(self, user_id):
            return [SimpleNamespace(token="premium-device-token")]

    topic_calls: list[str] = []
    token_calls: list[dict] = []

    async def fake_topic_send(*, topic, title, body, data=None, priority="normal"):
        topic_calls.append(topic)
        return "topic-msg-1"

    async def fake_token_send(*, token, title, body, data=None, priority="normal"):
        token_calls.append({"token": token, "priority": priority, "data": data})
        return "token-msg-1"

    monkeypatch.setattr(
        "services.notification.send_fcm_topic_message",
        fake_topic_send,
    )
    monkeypatch.setattr(
        "services.notification.send_fcm_token_message",
        fake_token_send,
    )

    service = NotificationService(session=SimpleNamespace())
    service.topic_repo = FakeTopicRepo()
    service.article_repo = FakeArticleRepo()
    service.subscription_repo = FakeSubscriptionRepo()
    service.user_repo = FakeUserRepo()
    service.push_token_repo = FakePushTokenRepo()

    count = await service.push_article_to_matching_topics(article_id)

    assert count == 1
    assert topic_calls == [build_fcm_topic_name(topic_id)]
    assert len(token_calls) == 1
    assert token_calls[0]["token"] == "premium-device-token"
    assert token_calls[0]["priority"] == "high"
    assert token_calls[0]["data"]["priority_tier"] == "premium"
