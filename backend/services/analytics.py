"""Client analytics ingestion service."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from repositories.sqlalchemy.analytics import AnalyticsRepository

logger = logging.getLogger(__name__)

EVENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")

ALLOWED_PARAMS_BY_EVENT: Dict[str, Set[str]] = {
    "discover_search": {"query", "source", "category"},
    "discover_category_select": {"category", "source"},
    "discover_topic_subscribe": {"topic_id", "success"},
    "discover_keyword_subscribe": {"keyword", "success"},
    "discover_recent_search_delete": {"query"},
    "discover_recent_searches_clear": {"previous_count"},
    "feed_refresh": {"source"},
    "feed_article_open": {"article_id", "source"},
    "feed_related_impression": {
        "article_id",
        "visible_count",
        "total_count",
        "source",
        "display_state",
    },
    "feed_related_view_all": {"article_id", "total_count"},
    "feed_related_swipe": {
        "article_id",
        "source",
        "scroll_offset",
        "max_scroll_extent",
    },
    "feed_related_click": {
        "article_id",
        "related_article_id",
        "source",
    },
    "subscription_push_toggle": {"topic_id", "enabled", "success"},
    "subscription_unsubscribe": {"topic_id", "success"},
    "subscription_list_refresh": {"source"},
}


class AnalyticsService:
    """Validate and persist client analytics events."""

    def __init__(self, repo: AnalyticsRepository):
        self._repo = repo

    async def ingest_event(
        self,
        *,
        event: str,
        params: Dict[str, Any],
        ts: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> None:
        normalized_event = event.strip()
        if not EVENT_NAME_PATTERN.match(normalized_event):
            raise ValueError("Invalid event name")

        allowed = ALLOWED_PARAMS_BY_EVENT.get(normalized_event)
        if allowed is None:
            raise ValueError("Unsupported event")

        sanitized_params = _sanitize_params(params, allowed)
        event_ts = _parse_ts(ts)

        await self._repo.create_event(
            {
                "event_name": normalized_event,
                "params": sanitized_params,
                "event_at": event_ts.replace(tzinfo=None),
                "user_id": user_id,
                "session_id": session_id,
                "client_ip": client_ip,
            }
        )

        logger.info(
            "analytics_event",
            extra={
                "analytics": {
                    "event": normalized_event,
                    "params": sanitized_params,
                    "ts": event_ts.isoformat(),
                    "user_id": user_id,
                    "session_id": session_id,
                    "client_ip": client_ip,
                }
            },
        )

    async def get_summary(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._repo.get_summary(
            days=days,
            user_id=user_id,
            session_id=session_id,
            event_name=event_name,
        )

    async def list_recent_events(
        self,
        *,
        limit: int = 50,
        event_name: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = await self._repo.list_recent_events(
            limit=limit,
            event_name=event_name,
            user_id=user_id,
            session_id=session_id,
        )
        return [
            {
                "id": str(row.id),
                "event": row.event_name,
                "params": row.params or {},
                "event_at": row.event_at.isoformat() if row.event_at else None,
                "user_id": row.user_id,
                "session_id": getattr(row, "session_id", None),
                "client_ip": row.client_ip,
            }
            for row in rows
        ]

    async def purge_old_events(self, *, retention_days: int) -> int:
        return await self._repo.purge_events_older_than(retention_days=retention_days)

    async def get_funnel(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._repo.get_funnel(
            days=days,
            user_id=user_id,
            session_id=session_id,
        )

    async def build_export_csv(
        self,
        *,
        days: int = 7,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> str:
        import csv
        import io

        summary = await self.get_summary(
            days=days,
            user_id=user_id,
            session_id=session_id,
            event_name=event_name,
        )
        funnel = await self.get_funnel(days=days, user_id=user_id, session_id=session_id)
        recent = await self.list_recent_events(
            limit=500,
            event_name=event_name,
            user_id=user_id,
            session_id=session_id,
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "metric", "value"])
        writer.writerow(["summary", "days", summary["days"]])
        writer.writerow(["summary", "total_events", summary["total_events"]])
        for item in summary["events_by_name"]:
            writer.writerow(["event_count", item["event"], item["count"]])
        for item in summary["daily_counts"]:
            writer.writerow(["daily_count", item["date"], item["count"]])

        writer.writerow([])
        writer.writerow(["funnel_step", "count"])
        for step, count in funnel["steps"].items():
            writer.writerow([step, count])

        writer.writerow([])
        writer.writerow(["event_at", "event", "user_id", "session_id", "params"])
        for row in recent:
            writer.writerow([
                row.get("event_at") or "",
                row.get("event") or "",
                row.get("user_id") or "",
                row.get("session_id") or "",
                row.get("params") or {},
            ])

        return buffer.getvalue()


def _sanitize_params(params: Dict[str, Any], allowed: Set[str]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key in allowed:
        if key not in params:
            continue
        value = params[key]
        if isinstance(value, bool):
            sanitized[key] = value
        elif isinstance(value, (int, float)):
            sanitized[key] = value
        elif isinstance(value, str):
            sanitized[key] = value.strip()[:100]
        else:
            sanitized[key] = str(value)[:100]
    return sanitized


def _parse_ts(ts: Optional[str]) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)
