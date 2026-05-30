"""
Dashboard API - 成本监控和系统状态
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core.analytics_auth import verify_analytics_dashboard_access
from core.config import get_settings
from core.dependencies import get_db, services
from repositories.sqlalchemy.analytics import AnalyticsRepository
from repositories.sqlalchemy.cost import CostRepository
from services.analytics import AnalyticsService
from services.cost import CostService
from tasks.scheduler import scheduler_manager

router = APIRouter()


class CostSummaryResponse(BaseModel):
    date: str
    total_cost_usd: float
    total_requests: int
    total_tokens: int
    budget_usd: float
    budget_used_percent: float
    remaining_usd: float
    degradation_level: str


class CostTrendResponse(BaseModel):
    date: str
    cost_usd: float
    requests: int


class SystemHealthResponse(BaseModel):
    database: dict
    cache: dict
    tasks: bool
    storage: bool
    ai: dict
    scheduler: Optional[dict] = None


class AnalyticsEventCountResponse(BaseModel):
    event: str
    count: int


class AnalyticsDailyCountResponse(BaseModel):
    date: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    days: int
    total_events: int
    events_by_name: List[AnalyticsEventCountResponse]
    daily_counts: List[AnalyticsDailyCountResponse]
    user_id: Optional[str] = None
    event_filter: Optional[str] = None


@router.get("/cost/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取成本摘要"""
    settings = get_settings()
    cost_service = CostService(
        repo=CostRepository(db),
        daily_budget_usd=settings.ai.ai_daily_budget_usd,
        monthly_budget_usd=settings.ai.ai_monthly_budget_usd,
    )
    summary = await cost_service.get_daily_summary(target_date)
    return CostSummaryResponse(**summary)


@router.get("/cost/trend", response_model=List[CostTrendResponse])
async def get_cost_trend(
    days: int = Query(7, le=30),
    db: AsyncSession = Depends(get_db),
):
    """获取成本趋势"""
    settings = get_settings()
    cost_service = CostService(
        repo=CostRepository(db),
        daily_budget_usd=settings.ai.ai_daily_budget_usd,
        monthly_budget_usd=settings.ai.ai_monthly_budget_usd,
    )
    trend = await cost_service.get_cost_trend(days=days)
    return [CostTrendResponse(**item) for item in trend]


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
    event: Optional[str] = Query(default=None, max_length=40),
    user_id: Optional[str] = Query(default=None, max_length=255),
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """获取客户端 analytics 聚合摘要"""
    verify_analytics_dashboard_access(request, token)
    service = AnalyticsService(AnalyticsRepository(db))
    summary = await service.get_summary(days=days, user_id=user_id, event_name=event)
    return AnalyticsSummaryResponse(**summary)


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """系统健康检查"""
    health = await services.health_check()
    health["scheduler"] = {
        "running": await scheduler_manager.health_check(),
    }
    return SystemHealthResponse(**health)


@router.get("/stats")
async def get_system_stats():
    """系统统计"""
    return {
        "articles": {
            "total": 0,  # TODO: 从数据库获取
            "today": 0,
        },
        "users": {
            "total": 0,
            "active_today": 0,
        },
        "sources": {
            "total": 0,
            "active": 0,
        },
    }
