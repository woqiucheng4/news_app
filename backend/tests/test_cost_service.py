from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.cost import CostService


@dataclass
class FakeSummary:
    total_cost_usd: float
    total_requests: int = 0
    total_tokens: int = 0


class FakeCostRepository:
    def __init__(self):
        self.daily_summary: FakeSummary | None = None
        self.monthly_total: float = 0.0
        self.logged_payloads: list[dict] = []

    async def log_usage(self, data: dict):
        self.logged_payloads.append(data)
        return data

    async def get_daily_summary(self, _date: date):
        return self.daily_summary

    async def get_cost_trend(self, _days: int = 7):
        return []

    async def get_cost_by_model(self, _date: date):
        return []

    async def get_total_cost(self, _start_date: date, _end_date: date):
        return self.monthly_total


@pytest.mark.asyncio
async def test_record_usage_auto_fills_total_tokens():
    repo = FakeCostRepository()
    service = CostService(repo=repo, daily_budget_usd=5.0, monthly_budget_usd=100.0)

    await service.record_usage(
        {
            "model": "gpt-4o-mini",
            "input_tokens": 80,
            "output_tokens": 20,
            "cost_usd": 0.002,
        }
    )

    assert repo.logged_payloads
    assert repo.logged_payloads[0]["total_tokens"] == 100


@pytest.mark.asyncio
async def test_check_budget_blocks_when_daily_budget_exceeded():
    repo = FakeCostRepository()
    repo.daily_summary = FakeSummary(total_cost_usd=4.9)
    repo.monthly_total = 20.0
    service = CostService(repo=repo, daily_budget_usd=5.0, monthly_budget_usd=100.0)

    allowed = await service.check_budget(estimated_cost=0.2)

    assert allowed is False


@pytest.mark.asyncio
async def test_get_degradation_level_thresholds():
    repo = FakeCostRepository()
    service = CostService(repo=repo, daily_budget_usd=5.0, monthly_budget_usd=100.0)

    repo.daily_summary = FakeSummary(total_cost_usd=2.0)  # 40%
    repo.monthly_total = 30.0
    assert await service.get_degradation_level() == "normal"

    repo.daily_summary = FakeSummary(total_cost_usd=4.1)  # 82%
    repo.monthly_total = 40.0
    assert await service.get_degradation_level() == "degraded"

    repo.daily_summary = FakeSummary(total_cost_usd=4.8)  # 96%
    repo.monthly_total = 45.0
    assert await service.get_degradation_level() == "cache_only"

    repo.daily_summary = FakeSummary(total_cost_usd=5.3)  # 106%
    repo.monthly_total = 50.0
    assert await service.get_degradation_level() == "paused"
