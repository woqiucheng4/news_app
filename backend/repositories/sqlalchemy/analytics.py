"""Analytics events repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import cast, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Date

from models.analytics import ClientAnalyticsEvent
from .base import SQLAlchemyRepository


class AnalyticsRepository(SQLAlchemyRepository):
    """Repository for client analytics events."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ClientAnalyticsEvent)

    async def create_event(self, data: Dict[str, Any]) -> ClientAnalyticsEvent:
        return await self.create(data)

    def _base_filters(
        self,
        *,
        since: datetime,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: Optional[str] = None,
    ):
        filters = [
            ClientAnalyticsEvent.is_deleted == False,
            ClientAnalyticsEvent.event_at >= since.replace(tzinfo=None),
        ]
        if user_id:
            filters.append(ClientAnalyticsEvent.user_id == user_id)
        if session_id:
            filters.append(ClientAnalyticsEvent.session_id == session_id)
        if event_name:
            filters.append(ClientAnalyticsEvent.event_name == event_name)
        return filters

    async def get_summary(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        base_filter = self._base_filters(
            since=since,
            user_id=user_id,
            session_id=session_id,
            event_name=event_name,
        )

        total_stmt = select(func.count()).select_from(ClientAnalyticsEvent).where(*base_filter)
        total_result = await self.session.execute(total_stmt)
        total_events = int(total_result.scalar_one() or 0)

        by_event_stmt = (
            select(ClientAnalyticsEvent.event_name, func.count())
            .where(*base_filter)
            .group_by(ClientAnalyticsEvent.event_name)
            .order_by(func.count().desc())
        )
        by_event_result = await self.session.execute(by_event_stmt)
        events_by_name = [
            {"event": event_name_value, "count": int(count)}
            for event_name_value, count in by_event_result.all()
        ]

        daily_stmt = (
            select(cast(ClientAnalyticsEvent.event_at, Date).label("day"), func.count())
            .where(*base_filter)
            .group_by("day")
            .order_by("day")
        )
        daily_result = await self.session.execute(daily_stmt)
        daily_counts = [
            {"date": day.isoformat(), "count": int(count)}
            for day, count in daily_result.all()
        ]

        return {
            "days": days,
            "total_events": total_events,
            "events_by_name": events_by_name,
            "daily_counts": daily_counts,
            "user_id": user_id,
            "session_id": session_id,
            "event_filter": event_name,
        }

    async def list_recent_events(
        self,
        *,
        limit: int = 50,
        event_name: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[ClientAnalyticsEvent]:
        stmt = (
            select(ClientAnalyticsEvent)
            .where(ClientAnalyticsEvent.is_deleted == False)
            .order_by(ClientAnalyticsEvent.event_at.desc())
            .limit(limit)
        )
        if event_name:
            stmt = stmt.where(ClientAnalyticsEvent.event_name == event_name)
        if user_id:
            stmt = stmt.where(ClientAnalyticsEvent.user_id == user_id)
        if session_id:
            stmt = stmt.where(ClientAnalyticsEvent.session_id == session_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def purge_events_older_than(self, *, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stmt = delete(ClientAnalyticsEvent).where(
            ClientAnalyticsEvent.event_at < cutoff.replace(tzinfo=None)
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    async def _count_events(
        self,
        *,
        since: datetime,
        event_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> int:
        filters = [
            ClientAnalyticsEvent.is_deleted == False,
            ClientAnalyticsEvent.event_at >= since.replace(tzinfo=None),
            ClientAnalyticsEvent.event_name == event_name,
        ]
        if user_id:
            filters.append(ClientAnalyticsEvent.user_id == user_id)
        if session_id:
            filters.append(ClientAnalyticsEvent.session_id == session_id)
        if success is not None:
            filters.append(ClientAnalyticsEvent.params["success"].as_boolean() == success)

        stmt = select(func.count()).select_from(ClientAnalyticsEvent).where(*filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def _count_events_with_string_param(
        self,
        *,
        since: datetime,
        event_name: str,
        param_key: str,
        param_value: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        filters = [
            ClientAnalyticsEvent.is_deleted == False,
            ClientAnalyticsEvent.event_at >= since.replace(tzinfo=None),
            ClientAnalyticsEvent.event_name == event_name,
            ClientAnalyticsEvent.params[param_key].as_string() == param_value,
        ]
        if user_id:
            filters.append(ClientAnalyticsEvent.user_id == user_id)
        if session_id:
            filters.append(ClientAnalyticsEvent.session_id == session_id)

        stmt = select(func.count()).select_from(ClientAnalyticsEvent).where(*filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_funnel(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        search_count = await self._count_events(
            since=since,
            event_name="discover_search",
            user_id=user_id,
            session_id=session_id,
        )
        category_count = await self._count_events(
            since=since,
            event_name="discover_category_select",
            user_id=user_id,
            session_id=session_id,
        )
        topic_attempts = await self._count_events(
            since=since,
            event_name="discover_topic_subscribe",
            user_id=user_id,
            session_id=session_id,
        )
        topic_success = await self._count_events(
            since=since,
            event_name="discover_topic_subscribe",
            user_id=user_id,
            session_id=session_id,
            success=True,
        )
        keyword_attempts = await self._count_events(
            since=since,
            event_name="discover_keyword_subscribe",
            user_id=user_id,
            session_id=session_id,
        )
        keyword_success = await self._count_events(
            since=since,
            event_name="discover_keyword_subscribe",
            user_id=user_id,
            session_id=session_id,
            success=True,
        )

        subscribe_attempts = topic_attempts + keyword_attempts
        subscribe_success = topic_success + keyword_success

        def _rate(numerator: int, denominator: int) -> Optional[float]:
            if denominator <= 0:
                return None
            return round(numerator / denominator, 4)

        return {
            "days": days,
            "user_id": user_id,
            "session_id": session_id,
            "steps": {
                "search": search_count,
                "category_select": category_count,
                "topic_subscribe_attempts": topic_attempts,
                "topic_subscribe_success": topic_success,
                "keyword_subscribe_attempts": keyword_attempts,
                "keyword_subscribe_success": keyword_success,
                "subscribe_attempts": subscribe_attempts,
                "subscribe_success": subscribe_success,
            },
            "conversion_rates": {
                "search_to_category": _rate(category_count, search_count),
                "search_to_subscribe_attempt": _rate(subscribe_attempts, search_count),
                "subscribe_attempt_to_success": _rate(subscribe_success, subscribe_attempts),
            },
        }

    async def get_related_funnel(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        impression = await self._count_events(
            since=since,
            event_name="feed_related_impression",
            user_id=user_id,
            session_id=session_id,
        )
        swipe = await self._count_events(
            since=since,
            event_name="feed_related_swipe",
            user_id=user_id,
            session_id=session_id,
        )
        click = await self._count_events(
            since=since,
            event_name="feed_related_click",
            user_id=user_id,
            session_id=session_id,
        )
        view_all = await self._count_events(
            since=since,
            event_name="feed_related_view_all",
            user_id=user_id,
            session_id=session_id,
        )
        article_open = await self._count_events_with_string_param(
            since=since,
            event_name="feed_article_open",
            param_key="source",
            param_value="related_article",
            user_id=user_id,
            session_id=session_id,
        )

        def _rate(numerator: int, denominator: int) -> Optional[float]:
            if denominator <= 0:
                return None
            return round(numerator / denominator, 4)

        return {
            "days": days,
            "user_id": user_id,
            "session_id": session_id,
            "steps": {
                "impression": impression,
                "swipe": swipe,
                "click": click,
                "view_all": view_all,
                "article_open": article_open,
            },
            "conversion_rates": {
                "impression_to_click": _rate(click, impression),
                "impression_to_view_all": _rate(view_all, impression),
                "swipe_to_click": _rate(click, swipe),
                "click_to_open": _rate(article_open, click),
            },
        }
