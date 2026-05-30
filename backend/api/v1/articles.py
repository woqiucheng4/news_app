"""
文章 API
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user_id, get_db, get_cache
from repositories.sqlalchemy.article import ArticleRepository
from repositories.sqlalchemy.user import SubscriptionRepository, TopicRepository
from services.article import ArticleService

router = APIRouter()


class ArticleResponse(BaseModel):
    id: str
    title: str
    url: str
    excerpt: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    source: Optional[dict] = None
    category: Optional[str] = None
    tags: List[str] = []
    published_at: Optional[str] = None
    created_at: str
    view_count: int = 0
    bookmark_count: int = 0


class ArticleDetailResponse(ArticleResponse):
    related_articles: List[ArticleResponse] = []
    related_articles_total: int = 0


class RelatedArticlesResponse(BaseModel):
    page: int
    page_size: int
    articles: List[ArticleResponse]
    has_more: bool
    total: int


class FeedResponse(BaseModel):
    page: int
    page_size: int
    articles: List[ArticleResponse]
    has_more: bool
    topic_id: Optional[str] = None


class TrendingEventResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    category: Optional[str] = None
    article_count: int
    source_count: int
    last_updated_at: Optional[str] = None


async def get_article_service(db=Depends(get_db)) -> ArticleService:
    """依赖注入：获取文章服务"""
    repo = ArticleRepository(db)
    return ArticleService(repo)


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    topic_id: Optional[str] = Query(None, min_length=1),
    user_id: str = Depends(get_current_user_id),
    service: ArticleService = Depends(get_article_service),
    db=Depends(get_db),
):
    """获取信息流；可选 topic_id 返回单话题过滤视图（需已订阅）"""
    topic_name: Optional[str] = None
    if topic_id:
        subscription_repo = SubscriptionRepository(db)
        if not await subscription_repo.is_subscribed(user_id, topic_id):
            raise HTTPException(
                status_code=403,
                detail="Subscription required for topic feed",
            )

        topic_repo = TopicRepository(db)
        topic = await topic_repo.get_by_id(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        topic_name = topic.name

    return await service.get_feed(
        user_id,
        page,
        page_size,
        topic_id=topic_id,
        topic_name=topic_name,
    )


@router.get("/search", response_model=List[ArticleResponse])
async def search_articles(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    service: ArticleService = Depends(get_article_service),
):
    """搜索文章"""
    return await service.search_articles(q, limit)


@router.get("/trending", response_model=List[TrendingEventResponse])
async def get_trending(
    limit: int = Query(20, ge=1, le=100),
    service: ArticleService = Depends(get_article_service),
):
    """获取热门事件"""
    return await service.get_trending(limit)


@router.get("/{article_id}/related", response_model=RelatedArticlesResponse)
async def get_related_articles(
    article_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ArticleService = Depends(get_article_service),
):
    """获取同一事件下的相关文章列表"""
    result = await service.get_related_articles(article_id, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return result


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article(
    article_id: str,
    service: ArticleService = Depends(get_article_service),
):
    """获取文章详情"""
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/{article_id}/summary")
async def generate_summary(
    article_id: str,
    service: ArticleService = Depends(get_article_service),
):
    """生成摘要"""
    summary = await service.generate_summary(article_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Article not found or no content")
    return {"summary": summary}
