"""
Notification service — FCM topic push and device token registration.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from core.firebase import send_fcm_topic_message, send_fcm_token_message
from models.subscription import Topic
from repositories.sqlalchemy.article import ArticleRepository
from repositories.sqlalchemy.notification import NotificationRepository, PushTokenRepository
from repositories.sqlalchemy.user import SubscriptionRepository, TopicRepository, UserRepository
from services.push_topics import build_fcm_topic_name

logger = logging.getLogger(__name__)


class NotificationService:
    """Push notification orchestration."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(session)
        self.push_token_repo = PushTokenRepository(session)
        self.topic_repo = TopicRepository(session)
        self.article_repo = ArticleRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
        self.user_repo = UserRepository(session)

    async def register_push_token(
        self,
        *,
        user_id: str,
        token: str,
        platform: str,
        device_id: str | None = None,
    ) -> None:
        await self.push_token_repo.upsert_token(
            user_id=user_id,
            token=token,
            platform=platform,
            device_id=device_id,
        )

    async def send_to_topic(
        self,
        *,
        topic_id: str,
        title: str,
        body: str,
        data: Dict[str, str] | None = None,
        notification_type: str = "update",
        article_id: str | None = None,
    ) -> Optional[str]:
        topic = await self.topic_repo.get_by_id(topic_id)
        if not topic or topic.subscriber_count <= 0:
            return None

        fcm_topic = build_fcm_topic_name(topic_id)
        message_id = await send_fcm_topic_message(
            topic=fcm_topic,
            title=title,
            body=body,
            data=data,
        )

        logger.info(
            "FCM topic push topic_id=%s fcm_topic=%s message_id=%s",
            topic_id,
            fcm_topic,
            message_id,
        )
        return message_id

    async def push_article_to_matching_topics(self, article_id: str) -> int:
        """Push an article update to all matching subscribed topics."""
        article = await self.article_repo.get_by_id(article_id)
        if not article or not article.is_summary_generated:
            return 0

        topics = await self._find_matching_topics(
            title=article.title or "",
            content=article.content or "",
            summary=article.summary or "",
        )
        if not topics:
            return 0

        body = (article.summary or article.title or "").strip()
        if not body:
            return 0

        title = (article.title or "NewsFlow update").strip()
        data = {
            "article_id": str(article.id),
            "notification_type": "update",
        }

        sent = 0
        for topic in topics:
            message_id = await self.send_to_topic(
                topic_id=str(topic.id),
                title=title[:500],
                body=body[:1000],
                data=data,
                notification_type="update",
                article_id=str(article.id),
            )
            if message_id is not None:
                sent += 1

            await self._push_priority_to_premium_subscribers(
                topic_id=str(topic.id),
                title=title[:500],
                body=body[:1000],
                data=data,
            )

        return sent

    async def _push_priority_to_premium_subscribers(
        self,
        *,
        topic_id: str,
        title: str,
        body: str,
        data: Dict[str, str],
    ) -> int:
        """Send high-priority direct pushes to premium subscribers of a topic."""
        user_ids = await self.subscription_repo.get_topic_subscribers(topic_id)
        delivered = 0

        for user_id in user_ids:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_premium_active:
                continue

            tokens = await self.push_token_repo.list_active_tokens_for_user(user_id)
            premium_data = {**data, "priority_tier": "premium"}
            for push_token in tokens:
                message_id = await send_fcm_token_message(
                    token=push_token.token,
                    title=title,
                    body=body,
                    data=premium_data,
                    priority="high",
                )
                if message_id:
                    delivered += 1

        if delivered:
            logger.info(
                "Premium priority push topic_id=%s delivered=%s",
                topic_id,
                delivered,
            )
        return delivered

    async def _find_matching_topics(
        self,
        *,
        title: str,
        content: str,
        summary: str,
    ) -> List[Topic]:
        topics = await self.topic_repo.list_with_subscribers()
        haystack = f"{title}\n{content}\n{summary}".lower()
        matches: List[Topic] = []

        for topic in topics:
            needle = topic.name.strip().lower()
            if len(needle) < 2:
                continue
            if needle in haystack:
                matches.append(topic)

        return matches

    async def get_user_notifications(
        self,
        user_id: str,
        *,
        is_read: bool | None = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        rows = await self.notification_repo.get_user_notifications(
            user_id,
            is_read=is_read,
            limit=limit,
        )
        return [self._notification_to_dict(row) for row in rows]

    async def mark_as_read(self, notification_id: str) -> bool:
        return await self.notification_repo.mark_as_read(notification_id)

    async def mark_all_as_read(self, user_id: str) -> int:
        return await self.notification_repo.mark_all_as_read(user_id)

    async def get_unread_count(self, user_id: str) -> int:
        return await self.notification_repo.count_unread(user_id)

    @staticmethod
    def _notification_to_dict(row) -> Dict[str, Any]:
        return {
            "id": str(row.id),
            "title": row.title,
            "body": row.body,
            "notification_type": row.notification_type,
            "is_read": row.is_read,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


async def push_article_update(article_id: str) -> int:
    """Fire-and-forget helper used after summary generation."""
    async with db_manager.get_write_session() as session:
        service = NotificationService(session)
        try:
            sent = await service.push_article_to_matching_topics(article_id)
            await session.commit()
            return sent
        except Exception as exc:
            await session.rollback()
            logger.warning("Failed to push article update for %s: %s", article_id, exc)
            return 0
