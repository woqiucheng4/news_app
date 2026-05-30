"""
最简 Web 页面路由（Jinja2）。
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from core.analytics_auth import verify_analytics_dashboard_access
from core.dependencies import get_db
from repositories.sqlalchemy.analytics import AnalyticsRepository
from repositories.sqlalchemy.article import ArticleRepository
from services.analytics import AnalyticsService

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")


def _group_events_by_category(events_by_name: List[Dict[str, Any]]) -> Dict[str, int]:
    categories = {
        "discover": 0,
        "feed": 0,
        "subscription": 0,
        "other": 0,
    }
    for item in events_by_name:
        event_name = item.get("event", "")
        count = int(item.get("count", 0))
        if event_name.startswith("discover_"):
            categories["discover"] += count
        elif event_name.startswith("feed_"):
            categories["feed"] += count
        elif event_name.startswith("subscription_"):
            categories["subscription"] += count
        else:
            categories["other"] += count
    return categories


def _to_article_card(article: Any) -> Dict[str, Any]:
    source_name = article.source.name if getattr(article, "source", None) else "Unknown"
    metadata = getattr(article, "metadata_", {}) or {}
    return {
        "id": str(article.id),
        "title": article.title,
        "url": article.url,
        "excerpt": article.excerpt,
        "summary": article.summary,
        "source_name": source_name,
        "category": article.category,
        "platform": metadata.get("platform"),
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat(),
    }


@router.get("/", response_class=HTMLResponse)
async def web_root() -> RedirectResponse:
    return RedirectResponse(url="/web/feed")


@router.get("/feed", response_class=HTMLResponse)
async def web_feed(
    request: Request,
    category: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    repo = ArticleRepository(db)
    offset = (page - 1) * page_size
    filters: Dict[str, Any] = {}
    if category:
        filters["category"] = category
    articles = await repo.list(filters=filters, order_by="-published_at", limit=page_size, offset=offset)
    categories = await _get_categories(repo)
    cards = [_to_article_card(article) for article in articles]
    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "title": "NewsFlow Feed",
            "active_page": "feed",
            "articles": cards,
            "categories": categories,
            "selected_category": category or "",
            "page": page,
            "has_more": len(cards) == page_size,
        },
    )


@router.get("/hot", response_class=HTMLResponse)
async def web_hot_topics(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    repo = ArticleRepository(db)
    hot_articles = await repo.get_recent(category="hot", limit=200)
    grouped: dict[str, list[Dict[str, Any]]] = defaultdict(list)
    for article in hot_articles:
        card = _to_article_card(article)
        platform = card.get("platform") or "other"
        grouped[platform].append(card)

    return templates.TemplateResponse(
        request=request,
        name="hot.html",
        context={
            "title": "NewsFlow Hot Topics",
            "active_page": "hot",
            "grouped_topics": dict(grouped),
        },
    )


@router.get("/articles/{article_id}", response_class=HTMLResponse)
async def web_article_detail(
    request: Request,
    article_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = ArticleRepository(db)
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    related: List[Dict[str, Any]] = []
    if article.event_id:
        event_articles = await repo.get_by_event_id(str(article.event_id))
        related = [
            _to_article_card(item)
            for item in event_articles
            if str(item.id) != str(article.id)
        ][:10]

    return templates.TemplateResponse(
        request=request,
        name="article_detail.html",
        context={
            "title": article.title,
            "active_page": "feed",
            "article": _to_article_card(article),
            "full_summary": article.summary,
            "related_articles": related,
        },
    )


@router.get("/analytics", response_class=HTMLResponse)
async def web_analytics_dashboard(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
    event: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    verify_analytics_dashboard_access(request, token)
    service = AnalyticsService(AnalyticsRepository(db))
    summary = await service.get_summary(
        days=days,
        user_id=user_id,
        session_id=session_id,
        event_name=event,
    )
    funnel = await service.get_funnel(days=days, user_id=user_id, session_id=session_id)
    related_funnel = await service.get_related_funnel(
        days=days,
        user_id=user_id,
        session_id=session_id,
    )
    recent = await service.list_recent_events(
        limit=30,
        event_name=event,
        user_id=user_id,
        session_id=session_id,
    )
    max_daily = max((item["count"] for item in summary["daily_counts"]), default=1)
    max_event_count = max((item["count"] for item in summary["events_by_name"]), default=1)
    event_categories = _group_events_by_category(summary["events_by_name"])

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "title": "NewsFlow Analytics",
            "active_page": "analytics",
            "summary": summary,
            "funnel": funnel,
            "related_funnel": related_funnel,
            "recent_events": recent,
            "max_daily": max_daily,
            "max_event_count": max_event_count,
            "event_categories": event_categories,
            "selected_days": days,
            "selected_event": event or "",
            "selected_user_id": user_id or "",
            "selected_session_id": session_id or "",
            "dashboard_token": token or "",
        },
    )


@router.get("/analytics/export.csv")
async def web_analytics_export_csv(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
    event: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    verify_analytics_dashboard_access(request, token)
    service = AnalyticsService(AnalyticsRepository(db))
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


async def _get_categories(repo: ArticleRepository) -> List[str]:
    recent = await repo.list(order_by="-published_at", limit=200)
    categories = sorted({item.category for item in recent if item.category})
    return categories
