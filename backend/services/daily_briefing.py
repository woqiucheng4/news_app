"""
Daily briefing generation and delivery.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from core.ai import AIModel, ai_manager, resolve_chat_model
from core.config import get_settings
from core.database import db_manager
from core.firebase import send_fcm_token_message
from models.article import Article
from models.subscription import Subscription
from models.user import UserSettings
from repositories.sqlalchemy.article import ArticleRepository
from repositories.sqlalchemy.notification import NotificationRepository, PushTokenRepository
from repositories.sqlalchemy.user import SubscriptionRepository, UserRepository

logger = logging.getLogger(__name__)

DAILY_BRIEFING_SYSTEM_PROMPT = """你是一位新闻编辑，负责撰写用户的每日信息简报。

任务：根据提供的多条新闻摘要，生成一份简洁的「今日概览」。

要求：
1. 长度：3-5 句话，总计 120-200 字
2. 按重要性排序，覆盖不同话题
3. 语言：与输入摘要的主要语言一致
4. 纯文本，无标题、无列表符号

禁止：添加个人观点、预测或未提供的信息。"""

MAX_BRIEFING_ARTICLES = 8
BRIEFING_LOOKBACK_HOURS = 24


class DailyBriefingService:
    """Generate and deliver per-user daily briefings."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.article_repo = ArticleRepository(session)
        self.notification_repo = NotificationRepository(session)
        self.push_token_repo = PushTokenRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
        self.user_repo = UserRepository(session)

    async def run_scheduled_batch(self) -> Dict[str, int]:
        """Deliver daily briefings to all eligible users."""
        now = datetime.utcnow()
        day_start = datetime(now.year, now.month, now.day)
        candidates = await self.user_repo.list_daily_briefing_candidates()

        sent = 0
        skipped = 0
        failed = 0

        for settings in candidates:
            user_id = str(settings.user_id)
            try:
                delivered = await self.deliver_for_user(
                    user_id,
                    settings=settings,
                    day_start=day_start,
                    now=now,
                )
                if delivered:
                    sent += 1
                else:
                    skipped += 1
            except Exception:
                failed += 1
                logger.exception("Daily briefing failed for user %s", user_id)

        return {"sent": sent, "skipped": skipped, "failed": failed}

    async def deliver_for_user(
        self,
        user_id: str,
        *,
        settings: UserSettings | None = None,
        day_start: datetime | None = None,
        now: datetime | None = None,
    ) -> bool:
        """Generate and push a daily briefing for one user."""
        now = now or datetime.utcnow()
        day_start = day_start or datetime(now.year, now.month, now.day)
        settings = settings or await self.user_repo.get_settings(user_id)
        if settings is None or not settings.push_enabled or not settings.push_daily_briefing:
            return False

        if self._is_quiet_hours(settings, now.hour):
            return False

        if await self.notification_repo.has_daily_briefing_on_date(user_id, day_start):
            return False

        pushes_today = await self.notification_repo.count_pushed_since(
            user_id,
            day_start,
        )
        user = await self.user_repo.get_by_id(user_id)
        is_premium = bool(user and user.is_premium_active)
        daily_push_limit = max(settings.push_max_per_day, 1)
        if is_premium:
            daily_push_limit *= 2

        if pushes_today >= daily_push_limit:
            return False

        briefing_text = await self.generate_daily_briefing(user_id)
        if not briefing_text:
            return False

        tokens = await self.push_token_repo.list_active_tokens_for_user(user_id)
        if not tokens:
            return False

        title = "NewsFlow Daily Briefing"
        data = {
            "notification_type": "daily_briefing",
        }
        if is_premium:
            data["priority_tier"] = "premium"

        message_ids: List[str] = []
        for push_token in tokens:
            message_id = await send_fcm_token_message(
                token=push_token.token,
                title=title,
                body=briefing_text[:1000],
                data=data,
                priority="high" if is_premium else "normal",
            )
            if message_id:
                message_ids.append(message_id)

        await self.notification_repo.create_notification(
            user_id=user_id,
            title=title,
            body=briefing_text,
            notification_type="daily_briefing",
            fcm_message_id=message_ids[0] if message_ids else None,
            metadata={"token_count": len(tokens), "delivered_count": len(message_ids)},
        )
        return bool(message_ids)

    async def generate_daily_briefing(self, user_id: str) -> Optional[str]:
        """Build an AI digest from recent subscribed-topic articles."""
        articles = await self._collect_user_articles(user_id)
        if not articles:
            return None

        if len(articles) == 1:
            article = articles[0]
            return (article.summary or article.title or "").strip() or None

        lines = []
        for index, article in enumerate(articles, start=1):
            summary = (article.summary or article.title or "").strip()
            if summary:
                lines.append(f"{index}. {summary}")

        if not lines:
            return None

        prompt = "以下是与用户订阅话题相关的最新新闻摘要：\n\n" + "\n".join(lines)
        response = await ai_manager.generate(
            prompt=prompt,
            system_prompt=DAILY_BRIEFING_SYSTEM_PROMPT,
            model=resolve_chat_model(),
            max_tokens=220,
            temperature=0.3,
        )
        text = (response.content or "").strip()
        return text or None

    async def _collect_user_articles(self, user_id: str) -> List[Article]:
        since = datetime.utcnow() - timedelta(hours=BRIEFING_LOOKBACK_HOURS)
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.topic))
            .where(
                Subscription.user_id == user_id,
                Subscription.is_deleted == False,
                Subscription.is_active == True,
            )
        )
        result = await self.session.execute(stmt)
        subscriptions = list(result.scalars().all())

        seen_ids: Set[str] = set()
        collected: List[Article] = []

        for subscription in subscriptions:
            topic = subscription.topic
            if topic is None:
                continue
            rows = await self.article_repo.list_for_topic(
                topic.name,
                limit=MAX_BRIEFING_ARTICLES,
                since=since,
            )
            for article in rows:
                article_id = str(article.id)
                if article_id in seen_ids:
                    continue
                if not article.is_summary_generated:
                    continue
                seen_ids.add(article_id)
                collected.append(article)

        collected.sort(
            key=lambda item: (
                item.relevance_score or 0,
                item.published_at or item.created_at,
            ),
            reverse=True,
        )
        return collected[:MAX_BRIEFING_ARTICLES]

    @staticmethod
    def _is_quiet_hours(settings: UserSettings, hour_utc: int) -> bool:
        start = settings.quiet_hours_start
        end = settings.quiet_hours_end
        if start is None or end is None:
            return False
        if start <= end:
            return start <= hour_utc < end
        return hour_utc >= start or hour_utc < end


async def run_daily_briefing_batch() -> Dict[str, int]:
    """Scheduler entrypoint."""
    async with db_manager.get_write_session() as session:
        service = DailyBriefingService(session)
        try:
            result = await service.run_scheduled_batch()
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise
