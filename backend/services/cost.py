"""
成本服务实现
"""

from datetime import datetime
from typing import Any, Dict, List

from repositories.interfaces import ICostRepository
from .interfaces import ICostService


class CostService(ICostService):
    """成本服务"""

    WARNING_THRESHOLD = 0.80
    CRITICAL_THRESHOLD = 0.95

    def __init__(
        self,
        repo: ICostRepository,
        daily_budget_usd: float = 5.0,
        monthly_budget_usd: float = 100.0,
    ):
        self.repo = repo
        self.daily_budget_usd = daily_budget_usd
        self.monthly_budget_usd = monthly_budget_usd

    async def record_usage(self, data: Dict) -> bool:
        payload = dict(data)
        payload.setdefault("input_tokens", 0)
        payload.setdefault("output_tokens", 0)
        payload.setdefault("total_tokens", payload["input_tokens"] + payload["output_tokens"])
        payload.setdefault("cost_usd", 0.0)
        await self.repo.log_usage(payload)
        return True

    async def get_daily_summary(self, date_value: datetime = None) -> Dict[str, Any]:
        target_date = date_value.date() if isinstance(date_value, datetime) else (date_value or datetime.utcnow().date())
        summary = await self.repo.get_daily_summary(target_date)

        total_cost = float(summary.total_cost_usd) if summary else 0.0
        total_requests = summary.total_requests if summary else 0
        total_tokens = summary.total_tokens if summary else 0

        used_percent = (total_cost / self.daily_budget_usd * 100) if self.daily_budget_usd > 0 else 0.0
        return {
            "date": target_date.isoformat(),
            "total_cost_usd": total_cost,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "budget_usd": self.daily_budget_usd,
            "budget_used_percent": used_percent,
            "remaining_usd": max(0.0, self.daily_budget_usd - total_cost),
            "degradation_level": await self.get_degradation_level(),
        }

    async def get_cost_trend(self, days: int = 7) -> List[Dict]:
        trend_items = await self.repo.get_cost_trend(days)
        return [
            {
                "date": item.date.isoformat(),
                "cost_usd": float(item.total_cost_usd),
                "requests": int(item.total_requests),
            }
            for item in trend_items
        ]

    async def check_budget(self, estimated_cost: float) -> bool:
        today = datetime.utcnow().date()
        daily_summary = await self.repo.get_daily_summary(today)
        daily_spent = float(daily_summary.total_cost_usd) if daily_summary else 0.0
        if daily_spent + estimated_cost > self.daily_budget_usd:
            return False

        month_start = today.replace(day=1)
        monthly_spent = await self.repo.get_total_cost(month_start, today)
        if monthly_spent + estimated_cost > self.monthly_budget_usd:
            return False
        return True

    async def get_degradation_level(self) -> str:
        daily_ratio, monthly_ratio = await self._current_budget_ratios()
        current_ratio = max(daily_ratio, monthly_ratio)

        if current_ratio > 1.0:
            return "paused"
        if current_ratio >= self.WARNING_THRESHOLD:
            return "degraded"
        return "normal"

    async def _current_budget_ratios(self) -> tuple[float, float]:
        today = datetime.utcnow().date()
        daily_summary = await self.repo.get_daily_summary(today)
        daily_spent = float(daily_summary.total_cost_usd) if daily_summary else 0.0
        month_start = today.replace(day=1)
        monthly_spent = await self.repo.get_total_cost(month_start, today)

        daily_ratio = (daily_spent / self.daily_budget_usd) if self.daily_budget_usd > 0 else 0.0
        monthly_ratio = (monthly_spent / self.monthly_budget_usd) if self.monthly_budget_usd > 0 else 0.0
        return daily_ratio, monthly_ratio
