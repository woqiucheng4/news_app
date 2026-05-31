"""
Custom RSS / web URL source API.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from core.dependencies import get_current_user_id, get_db
from repositories.sqlalchemy.article import ArticleRepository, EventRepository, SourceRepository
from repositories.sqlalchemy.user_feed import UserFeedRepository
from services.content_ingestion import ContentIngestionService

router = APIRouter()


class RegisterRssRequest(BaseModel):
    feed_url: HttpUrl
    name: Optional[str] = Field(default=None, max_length=200)


class IngestUrlRequest(BaseModel):
    url: HttpUrl
    name: Optional[str] = Field(default=None, max_length=200)


class UserFeedResponse(BaseModel):
    id: str
    feed_type: str
    custom_url: Optional[str] = None
    custom_name: Optional[str] = None
    source_id: Optional[str] = None
    is_active: bool


def _build_ingestion_service(db) -> ContentIngestionService:
    source_repo = SourceRepository(db)
    article_repo = ArticleRepository(db)
    event_repo = EventRepository(db)
    return ContentIngestionService(
        source_repo=source_repo,
        article_repo=article_repo,
        event_repo=event_repo,
    )


@router.get("/me", response_model=list[UserFeedResponse])
async def list_my_sources(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List custom RSS / URL sources registered by the current user."""
    repo = UserFeedRepository(db)
    feeds = await repo.list_for_user(user_id)
    return [
        UserFeedResponse(
            id=str(feed.id),
            feed_type=feed.feed_type,
            custom_url=feed.custom_url,
            custom_name=feed.custom_name,
            source_id=str(feed.source_id) if feed.source_id else None,
            is_active=feed.is_active,
        )
        for feed in feeds
    ]


@router.post("/rss")
async def register_rss_source(
    body: RegisterRssRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Register a custom RSS feed and fetch it immediately."""
    service = _build_ingestion_service(db)
    try:
        result = await service.register_user_rss_feed(
            user_id=user_id,
            feed_url=str(body.feed_url),
            custom_name=body.name,
        )
        await db.commit()
        return {"success": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/url")
async def ingest_web_url(
    body: IngestUrlRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Fetch and ingest a single web page URL for the current user."""
    service = _build_ingestion_service(db)
    try:
        result = await service.ingest_user_web_url(
            user_id=user_id,
            page_url=str(body.url),
            custom_name=body.name,
        )
        await db.commit()
        return {"success": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
