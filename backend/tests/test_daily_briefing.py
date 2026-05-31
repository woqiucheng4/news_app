from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.daily_briefing import DailyBriefingService


class FakeArticleRepo:
    def __init__(self, articles):
        self.articles = articles

    async def list_for_topic(self, topic_name, limit=20, offset=0, since=None):
        return [item for item in self.articles if topic_name.lower() in item.title.lower()]


class FakeNotificationRepo:
    def __init__(self):
        self.created = []
        self.briefing_sent = False
        self.pushes_today = 0

    async def has_daily_briefing_on_date(self, user_id, day_start):
        return self.briefing_sent

    async def count_pushed_since(self, user_id, since, notification_types=None):
        return self.pushes_today

    async def create_notification(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(id=str(uuid4()))


class FakePushTokenRepo:
    async def list_active_tokens_for_user(self, user_id):
        return [SimpleNamespace(token="device-token-1")]


class FakeSubscriptionRepo:
    pass


class FakeUserRepo:
    def __init__(self, settings):
        self.settings = settings

    async def get_settings(self, user_id):
        return self.settings


@pytest.mark.asyncio
async def test_generate_daily_briefing_returns_single_article_summary():
    article = SimpleNamespace(
        id=str(uuid4()),
        title="NVIDIA beats earnings",
        summary="NVIDIA reported strong quarterly results.",
        is_summary_generated=True,
        relevance_score=90,
        published_at=datetime(2026, 5, 31, 8, 0, 0),
        created_at=datetime(2026, 5, 31, 8, 0, 0),
    )
    service = DailyBriefingService(session=SimpleNamespace())
    service.article_repo = FakeArticleRepo([article])
    service.subscription_repo = FakeSubscriptionRepo()
    service.user_repo = FakeUserRepo(None)
    service.notification_repo = FakeNotificationRepo()
    service.push_token_repo = FakePushTokenRepo()

    async def fake_collect(_user_id):
        return [article]

    service._collect_user_articles = fake_collect  # type: ignore

    text = await service.generate_daily_briefing("user-1")
    assert text == "NVIDIA reported strong quarterly results."


@pytest.mark.asyncio
async def test_deliver_for_user_skips_when_already_sent(monkeypatch):
    settings = SimpleNamespace(
        push_enabled=True,
        push_daily_briefing=True,
        push_max_per_day=5,
        quiet_hours_start=None,
        quiet_hours_end=None,
    )
    service = DailyBriefingService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo(settings)
    service.notification_repo = FakeNotificationRepo()
    service.notification_repo.briefing_sent = True
    service.push_token_repo = FakePushTokenRepo()

    delivered = await service.deliver_for_user("user-1", settings=settings)
    assert delivered is False


@pytest.mark.asyncio
async def test_deliver_for_user_pushes_and_records_notification(monkeypatch):
    settings = SimpleNamespace(
        user_id=uuid4(),
        push_enabled=True,
        push_daily_briefing=True,
        push_max_per_day=5,
        quiet_hours_start=None,
        quiet_hours_end=None,
    )
    service = DailyBriefingService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo(settings)
    service.notification_repo = FakeNotificationRepo()
    service.push_token_repo = FakePushTokenRepo()

    async def fake_generate(user_id):
        return "Your daily digest is ready."

    async def fake_send(*, token, title, body, data=None):
        assert token == "device-token-1"
        assert data["notification_type"] == "daily_briefing"
        return "msg-123"

    monkeypatch.setattr(service, "generate_daily_briefing", fake_generate)
    monkeypatch.setattr(
        "services.daily_briefing.send_fcm_token_message",
        fake_send,
    )

    delivered = await service.deliver_for_user("user-1", settings=settings)
    assert delivered is True
    assert len(service.notification_repo.created) == 1
    assert service.notification_repo.created[0]["notification_type"] == "daily_briefing"
