from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.freemium import FreemiumService


class FakeUserRepo:
    def __init__(self, premium: bool = False):
        self.premium = premium

    async def get_by_id(self, user_id: str):
        return SimpleNamespace(
            is_premium=self.premium,
            premium_expires_at=None,
            is_premium_active=self.premium,
        )


class FakeSubscriptionRepo:
    def __init__(self, active_count: int = 0):
        self.active_count = active_count

    async def count_active_subscriptions(self, user_id: str):
        return self.active_count


@pytest.mark.asyncio
async def test_assert_can_add_subscription_blocks_free_limit(monkeypatch):
    service = FreemiumService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo(premium=False)
    service.subscription_repo = FakeSubscriptionRepo(active_count=5)

    with pytest.raises(HTTPException) as exc:
        await service.assert_can_add_subscription("user-1")

    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "SUBSCRIPTION_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_record_article_view_enforces_daily_limit(monkeypatch):
    viewed = {f"article-{index}" for index in range(20)}

    async def fake_get(key):
        if key.startswith("freemium:views:"):
            return list(viewed)
        return None

    async def fake_set(key, value, ttl=3600):
        return True

    monkeypatch.setattr("services.freemium.cache_manager.get", fake_get)
    monkeypatch.setattr("services.freemium.cache_manager.set", fake_set)

    service = FreemiumService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo(premium=False)
    service.subscription_repo = FakeSubscriptionRepo()

    with pytest.raises(HTTPException) as exc:
        await service.record_article_view("user-1", "new-article")

    assert exc.value.detail["code"] == "DAILY_VIEW_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_get_entitlements_premium_user():
    service = FreemiumService(session=SimpleNamespace())
    service.user_repo = FakeUserRepo(premium=True)
    service.subscription_repo = FakeSubscriptionRepo(active_count=12)

    async def fake_views(_user_id):
        return 0

    service._daily_article_views = fake_views  # type: ignore

    entitlements = await service.get_entitlements("user-1")
    assert entitlements["is_premium"] is True
    assert entitlements["max_topic_subscriptions"] is None
    assert entitlements["features"]["deep_analysis"] is True
