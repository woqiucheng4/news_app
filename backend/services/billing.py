"""
Billing and premium activation (MVP verify stub).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from repositories.sqlalchemy.user import UserRepository


class BillingService:
    """Verify store purchases and grant premium access."""

    PREMIUM_DURATION_DAYS = 30

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.settings = get_settings()

    async def verify_purchase(
        self,
        *,
        user_id: str,
        platform: str,
        product_id: str,
        purchase_token: str,
    ) -> dict:
        expected_product = self.settings.freemium.premium_product_id
        if product_id != expected_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PRODUCT",
                    "message": "Unknown product id",
                },
            )

        if not purchase_token.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_TOKEN", "message": "Missing purchase token"},
            )

        if not self._can_verify_in_current_environment():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={
                    "code": "STORE_VERIFY_UNAVAILABLE",
                    "message": "Store receipt verification is not configured",
                },
            )

        expires_at = datetime.utcnow() + timedelta(days=self.PREMIUM_DURATION_DAYS)
        user = await self.user_repo.update(
            user_id,
            {
                "is_premium": True,
                "premium_expires_at": expires_at,
            },
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await self._invalidate_user_cache(user_id)

        return {
            "success": True,
            "is_premium": True,
            "premium_expires_at": expires_at.isoformat(),
            "platform": platform,
            "product_id": product_id,
            "verification": "dev_stub" if self.settings.debug else "accepted",
        }

    def _can_verify_in_current_environment(self) -> bool:
        if self.settings.freemium.allow_dev_purchase_verify:
            return True
        return self.settings.debug

    async def _invalidate_user_cache(self, user_id: str) -> None:
        from core.cache import cache_manager

        await cache_manager.delete(f"user:{user_id}")
