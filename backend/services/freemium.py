"""
Freemium entitlements and usage limits.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import cache_manager
from core.config import get_settings
from repositories.sqlalchemy.user import SubscriptionRepository, UserRepository


class FreemiumService:
    """Enforce free-tier limits and expose entitlement snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
        self.settings = get_settings().freemium

    async def get_entitlements(self, user_id: str) -> Dict[str, Any]:
        premium = await self._is_premium_active(user_id)
        topic_used = await self.subscription_repo.count_active_subscriptions(user_id)
        views_used = await self._daily_article_views(user_id)

        max_topics = None if premium else self.settings.free_max_topic_subscriptions
        max_views = None if premium else self.settings.free_daily_article_views

        return {
            "is_premium": premium,
            "max_topic_subscriptions": max_topics,
            "topic_subscriptions_used": topic_used,
            "daily_article_views_limit": max_views,
            "daily_article_views_used": views_used,
            "can_subscribe_more": premium
            or topic_used < self.settings.free_max_topic_subscriptions,
            "can_view_articles": premium
            or views_used < self.settings.free_daily_article_views,
            "features": {
                "deep_analysis": premium,
                "priority_push": premium,
                "unlimited_subscriptions": premium,
            },
            "premium_product_id": self.settings.premium_product_id,
        }

    async def assert_can_add_subscription(self, user_id: str) -> None:
        if await self._is_premium_active(user_id):
            return

        active_count = await self.subscription_repo.count_active_subscriptions(user_id)
        if active_count >= self.settings.free_max_topic_subscriptions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "SUBSCRIPTION_LIMIT_REACHED",
                    "message": "Free plan topic subscription limit reached",
                    "limit": self.settings.free_max_topic_subscriptions,
                    "used": active_count,
                },
            )

    async def record_article_view(self, user_id: str, article_id: str) -> None:
        """Record a billable article detail view; raises when free limit exceeded."""
        if await self._is_premium_active(user_id):
            return

        day_key = datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = f"freemium:views:{user_id}:{day_key}"
        viewed = set(await cache_manager.get(cache_key) or [])

        if article_id in viewed:
            return

        if len(viewed) >= self.settings.free_daily_article_views:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "DAILY_VIEW_LIMIT_REACHED",
                    "message": "Free plan daily article view limit reached",
                    "limit": self.settings.free_daily_article_views,
                    "used": len(viewed),
                },
            )

        viewed.add(article_id)
        await cache_manager.set(cache_key, list(viewed), ttl=86_400)

    async def assert_premium_feature(self, user_id: str, feature: str) -> None:
        if await self._is_premium_active(user_id):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PREMIUM_REQUIRED",
                "message": f"Premium subscription required for {feature}",
                "feature": feature,
            },
        )

    async def _is_premium_active(self, user_id: str) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        return bool(user.is_premium_active)

    async def _daily_article_views(self, user_id: str) -> int:
        day_key = datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = f"freemium:views:{user_id}:{day_key}"
        viewed = await cache_manager.get(cache_key) or []
        return len(viewed)
