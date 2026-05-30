"""Client analytics ingestion and query API."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.analytics_auth import verify_analytics_dashboard_access
from core.dependencies import get_current_user_id, get_db, get_optional_user_id
from repositories.sqlalchemy.analytics import AnalyticsRepository
from services.analytics import AnalyticsService

router = APIRouter()


class AnalyticsEventRequest(BaseModel):
    event: str = Field(min_length=1, max_length=40)
    params: Dict[str, Any] = Field(default_factory=dict)
    ts: Optional[str] = None


class AnalyticsEventResponse(BaseModel):
    success: bool = True


class AnalyticsEventItemResponse(BaseModel):
    id: str
    event: str
    params: Dict[str, Any]
    event_at: Optional[str]
    user_id: Optional[str] = None
    client_ip: Optional[str] = None


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
    session_id: Optional[str] = None
    event_filter: Optional[str] = None


class AnalyticsFunnelStepsResponse(BaseModel):
    search: int
    category_select: int
    topic_subscribe_attempts: int
    topic_subscribe_success: int
    keyword_subscribe_attempts: int
    keyword_subscribe_success: int
    subscribe_attempts: int
    subscribe_success: int


class AnalyticsFunnelRatesResponse(BaseModel):
    search_to_category: Optional[float] = None
    search_to_subscribe_attempt: Optional[float] = None
    subscribe_attempt_to_success: Optional[float] = None


class AnalyticsFunnelResponse(BaseModel):
    days: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    steps: AnalyticsFunnelStepsResponse
    conversion_rates: AnalyticsFunnelRatesResponse


class AnalyticsRelatedFunnelStepsResponse(BaseModel):
    impression: int
    swipe: int
    click: int
    view_all: int
    article_open: int


class AnalyticsRelatedFunnelRatesResponse(BaseModel):
    impression_to_click: Optional[float] = None
    impression_to_view_all: Optional[float] = None
    swipe_to_click: Optional[float] = None
    click_to_open: Optional[float] = None


class AnalyticsRelatedFunnelResponse(BaseModel):
    days: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    steps: AnalyticsRelatedFunnelStepsResponse
    conversion_rates: AnalyticsRelatedFunnelRatesResponse


async def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(db))


def _analytics_dashboard_guard(
    request: Request,
    token: Optional[str] = Query(default=None),
) -> None:
    verify_analytics_dashboard_access(request, token)


def _get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _get_session_id(request: Request) -> Optional[str]:
    session_id = request.headers.get("X-Session-Id")
    if session_id:
        normalized = session_id.strip()
        if normalized:
            return normalized[:64]
    return None


@router.post("/events", response_model=AnalyticsEventResponse, status_code=202)
async def ingest_analytics_event(
    request: Request,
    payload: AnalyticsEventRequest,
    service: AnalyticsService = Depends(get_analytics_service),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Ingest a sanitized client analytics event."""
    try:
        await service.ingest_event(
            event=payload.event,
            params=payload.params,
            ts=payload.ts,
            user_id=user_id,
            session_id=_get_session_id(request),
            client_ip=_get_client_ip(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AnalyticsEventResponse()


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    dependencies=[Depends(_analytics_dashboard_guard)],
)
async def get_analytics_summary(
    days: int = Query(default=7, ge=1, le=90),
    event: Optional[str] = Query(default=None, max_length=40),
    user_id: Optional[str] = Query(default=None, max_length=255),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get aggregated analytics summary for dashboard."""
    summary = await service.get_summary(days=days, user_id=user_id, event_name=event)
    return AnalyticsSummaryResponse(**summary)


@router.get(
    "/events/recent",
    response_model=List[AnalyticsEventItemResponse],
    dependencies=[Depends(_analytics_dashboard_guard)],
)
async def get_recent_analytics_events(
    limit: int = Query(default=50, ge=1, le=200),
    event: Optional[str] = Query(default=None, max_length=40),
    user_id: Optional[str] = Query(default=None, max_length=255),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """List recent analytics events for debugging/dashboard."""
    rows = await service.list_recent_events(limit=limit, event_name=event, user_id=user_id)
    return [AnalyticsEventItemResponse(**row) for row in rows]


@router.get(
    "/funnel",
    response_model=AnalyticsFunnelResponse,
    dependencies=[Depends(_analytics_dashboard_guard)],
)
async def get_analytics_funnel(
    days: int = Query(default=7, ge=1, le=90),
    user_id: Optional[str] = Query(default=None, max_length=255),
    session_id: Optional[str] = Query(default=None, max_length=64),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get discovery funnel step counts and conversion rates."""
    funnel = await service.get_funnel(days=days, user_id=user_id, session_id=session_id)
    return AnalyticsFunnelResponse(**funnel)


@router.get(
    "/related-funnel",
    response_model=AnalyticsRelatedFunnelResponse,
    dependencies=[Depends(_analytics_dashboard_guard)],
)
async def get_related_analytics_funnel(
    days: int = Query(default=7, ge=1, le=90),
    user_id: Optional[str] = Query(default=None, max_length=255),
    session_id: Optional[str] = Query(default=None, max_length=64),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get related-coverage funnel step counts and conversion rates."""
    funnel = await service.get_related_funnel(
        days=days,
        user_id=user_id,
        session_id=session_id,
    )
    return AnalyticsRelatedFunnelResponse(**funnel)


@router.get(
    "/export.csv",
    dependencies=[Depends(_analytics_dashboard_guard)],
)
async def export_analytics_csv(
    days: int = Query(default=7, ge=1, le=90),
    event: Optional[str] = Query(default=None, max_length=40),
    user_id: Optional[str] = Query(default=None, max_length=255),
    session_id: Optional[str] = Query(default=None, max_length=64),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Export analytics summary and recent events as CSV."""
    csv_content = await service.build_export_csv(
        days=days,
        user_id=user_id,
        session_id=session_id,
        event_name=event,
    )
    filename = f"analytics-{days}d.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/me/summary", response_model=AnalyticsSummaryResponse)
async def get_my_analytics_summary(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
    scope: str = Query(default="user", pattern="^(user|session)$"),
    session_id: Optional[str] = Query(default=None, max_length=64),
    current_user_id: str = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get analytics summary for the authenticated user or current session."""
    if scope == "session":
        resolved_session = session_id or _get_session_id(request)
        if not resolved_session:
            raise HTTPException(status_code=400, detail="session_id required for session scope")
        summary = await service.get_summary(
            days=days,
            user_id=current_user_id,
            session_id=resolved_session,
        )
    else:
        summary = await service.get_summary(days=days, user_id=current_user_id)
    return AnalyticsSummaryResponse(**summary)


@router.get("/me/funnel", response_model=AnalyticsFunnelResponse)
async def get_my_analytics_funnel(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
    scope: str = Query(default="user", pattern="^(user|session)$"),
    session_id: Optional[str] = Query(default=None, max_length=64),
    current_user_id: str = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get discovery funnel for the authenticated user or current session."""
    if scope == "session":
        resolved_session = session_id or _get_session_id(request)
        if not resolved_session:
            raise HTTPException(status_code=400, detail="session_id required for session scope")
        funnel = await service.get_funnel(
            days=days,
            user_id=current_user_id,
            session_id=resolved_session,
        )
    else:
        funnel = await service.get_funnel(days=days, user_id=current_user_id)
    return AnalyticsFunnelResponse(**funnel)
