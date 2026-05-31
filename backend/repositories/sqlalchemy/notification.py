"""
Notification and push token repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select, update
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

    async def create_notification(
        self,
        *,
        user_id: str,
        title: str,
        body: str,
        notification_type: str,
        article_id: str | None = None,
        fcm_message_id: str | None = None,
        metadata: dict | None = None,
    ) -> Notification:
        instance = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            article_id=article_id,
            is_read=False,
            is_pushed=fcm_message_id is not None,
            pushed_at=datetime.utcnow() if fcm_message_id else None,
            fcm_message_id=fcm_message_id,
            metadata_=metadata or {},
        )
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def count_pushed_since(
        self,
        user_id: str,
        since: datetime,
        notification_types: list[str] | None = None,
    ) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_deleted == False,
            Notification.is_pushed == True,
            Notification.pushed_at >= since,
        )
        if notification_types:
            stmt = stmt.where(Notification.notification_type.in_(notification_types))
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def has_daily_briefing_on_date(self, user_id: str, day_start: datetime) -> bool:
        stmt = select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.is_deleted == False,
            Notification.notification_type == "daily_briefing",
            Notification.created_at >= day_start,
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


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

    async def list_active_tokens_for_user(self, user_id: str) -> List[PushToken]:
        stmt = select(PushToken).where(
            PushToken.user_id == user_id,
            PushToken.is_active == True,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
