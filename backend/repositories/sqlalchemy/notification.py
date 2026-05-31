"""
Notification and push token repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification, PushToken
from ..interfaces import INotificationRepository
from .base import SQLAlchemyRepository


class NotificationRepository(SQLAlchemyRepository, INotificationRepository):
    """Notification repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    async def get_user_notifications(
        self,
        user_id: str,
        is_read: bool | None = None,
        limit: int = 50,
    ) -> List[Notification]:
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_deleted == False,
        )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(self, id: str) -> bool:
        stmt = (
            update(Notification)
            .where(Notification.id == id, Notification.is_deleted == False)
            .values(is_read=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: str) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_deleted == False,
                Notification.is_read == False,
            )
            .values(is_read=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def get_unpushed(self, limit: int = 100) -> List[Notification]:
        stmt = (
            select(Notification)
            .where(
                Notification.is_deleted == False,
                Notification.is_pushed == False,
            )
            .order_by(Notification.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(self, user_id: str) -> int:
        stmt = select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.is_deleted == False,
            Notification.is_read == False,
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())


class PushTokenRepository(SQLAlchemyRepository):
    """Push token repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PushToken)

    async def upsert_token(
        self,
        *,
        user_id: str,
        token: str,
        platform: str,
        device_id: str | None = None,
    ) -> PushToken:
        stmt = select(PushToken).where(PushToken.token == token)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.utcnow()
        if existing:
            existing.user_id = user_id
            existing.platform = platform
            existing.device_id = device_id
            existing.is_active = True
            existing.last_used_at = now
            await self.session.flush()
            return existing

        instance = PushToken(
            user_id=user_id,
            token=token,
            platform=platform,
            device_id=device_id,
            is_active=True,
            last_used_at=now,
        )
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def deactivate_token(self, token: str) -> bool:
        stmt = (
            update(PushToken)
            .where(PushToken.token == token)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
