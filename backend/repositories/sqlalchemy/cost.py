"""
成本 Repository 实现
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cost import APIUsageLog, DailyCostSummary
from ..interfaces import ICostRepository
from .base import SQLAlchemyRepository


class CostRepository(SQLAlchemyRepository, ICostRepository):
    """成本 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DailyCostSummary)

    async def log_usage(self, data: Dict[str, Any]) -> APIUsageLog:
        payload = dict(data)
        payload.setdefault("input_tokens", 0)
        payload.setdefault("output_tokens", 0)
        payload.setdefault("total_tokens", payload["input_tokens"] + payload["output_tokens"])
        payload.setdefault("cost_usd", 0.0)
        payload.setdefault("cache_hit", False)
        payload.setdefault("prompt_cached", False)
        payload.setdefault("retry_count", 0)

        usage = APIUsageLog(**payload)
        self.session.add(usage)
        await self.session.flush()

        usage_date = usage.created_at.date() if usage.created_at else datetime.utcnow().date()
        await self._upsert_daily_summary(usage_date, usage)
        return usage

    async def _upsert_daily_summary(self, usage_date: date, usage: APIUsageLog) -> DailyCostSummary:
        summary = await self.get_daily_summary(usage_date)
        if summary is None:
            summary = DailyCostSummary(
                date=usage_date,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                cached_requests=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                total_cost_usd=0.0,
                cost_by_model={},
                cost_by_type={},
            )
            self.session.add(summary)

        summary.total_requests += 1
        if usage.error_code:
            summary.failed_requests += 1
        else:
            summary.successful_requests += 1
        if usage.cache_hit:
            summary.cached_requests += 1

        summary.total_input_tokens += usage.input_tokens
        summary.total_output_tokens += usage.output_tokens
        summary.total_tokens += usage.total_tokens
        summary.total_cost_usd += usage.cost_usd

        by_model = dict(summary.cost_by_model or {})
        by_model[usage.model] = float(by_model.get(usage.model, 0.0)) + float(usage.cost_usd)
        summary.cost_by_model = by_model

        usage_type = usage.request_type or "unknown"
        by_type = dict(summary.cost_by_type or {})
        by_type[usage_type] = float(by_type.get(usage_type, 0.0)) + float(usage.cost_usd)
        summary.cost_by_type = by_type

        await self.session.flush()
        return summary

    async def get_daily_summary(self, date_value: date) -> Optional[DailyCostSummary]:
        stmt = select(DailyCostSummary).where(
            DailyCostSummary.date == date_value,
            DailyCostSummary.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_cost_trend(self, days: int = 7) -> List[DailyCostSummary]:
        days = max(days, 1)
        since_date = datetime.utcnow().date() - timedelta(days=days - 1)
        stmt = (
            select(DailyCostSummary)
            .where(
                DailyCostSummary.date >= since_date,
                DailyCostSummary.is_deleted == False,
            )
            .order_by(DailyCostSummary.date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_cost_by_model(self, date_value: date) -> List[Dict]:
        summary = await self.get_daily_summary(date_value)
        if summary is None:
            return []
        return [
            {"model": model, "cost_usd": float(cost)}
            for model, cost in (summary.cost_by_model or {}).items()
        ]

    async def get_total_cost(self, start_date: date, end_date: date) -> float:
        stmt = select(func.coalesce(func.sum(DailyCostSummary.total_cost_usd), 0.0)).where(
            DailyCostSummary.date >= start_date,
            DailyCostSummary.date <= end_date,
            DailyCostSummary.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return float(result.scalar() or 0.0)
