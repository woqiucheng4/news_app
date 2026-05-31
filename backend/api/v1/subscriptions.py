"""订阅 API。"""

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.dependencies import get_current_user_id, get_db
from repositories.sqlalchemy.user import SubscriptionRepository, TopicRepository
from services.freemium import FreemiumService

router = APIRouter()


class TopicResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    category: Optional[str] = None
    subscriber_count: int = 0
    is_subscribed: bool = False


class TopicCategoryResponse(BaseModel):
    name: str
    topic_count: int


class SubscriptionResponse(BaseModel):
    topic: TopicResponse
    is_active: bool
    priority: int
    push_enabled: bool
    push_breaking_only: bool
    subscribed_at: str


class SubscribeRequest(BaseModel):
    topic_id: str
    push_enabled: bool = True
    push_breaking_only: bool = False


class KeywordSubscribeRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=100)
    category: str = Field(default="custom", max_length=100)
    push_enabled: bool = True
    push_breaking_only: bool = False


class UpdateSubscriptionRequest(BaseModel):
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    push_enabled: Optional[bool] = None
    push_breaking_only: Optional[bool] = None


class ReorderSubscriptionItem(BaseModel):
    topic_id: str
    priority: int


class ReorderSubscriptionsRequest(BaseModel):
    items: List[ReorderSubscriptionItem]


def _slugify_keyword(keyword: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", keyword.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid keyword")
    return f"keyword-{normalized}"


def _to_topic_response(topic, is_subscribed: bool = False) -> TopicResponse:
    return TopicResponse(
        id=str(topic.id),
        name=topic.name,
        slug=topic.slug,
        description=topic.description,
        category=topic.category,
        subscriber_count=topic.subscriber_count,
        is_subscribed=is_subscribed,
    )


def _to_subscription_response(subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        topic=_to_topic_response(subscription.topic, is_subscribed=True),
        is_active=subscription.is_active,
        priority=subscription.priority,
        push_enabled=subscription.push_enabled,
        push_breaking_only=subscription.push_breaking_only,
        subscribed_at=subscription.subscribed_at.isoformat(),
    )


@router.get("/topics/categories", response_model=List[TopicCategoryResponse])
async def get_topic_categories(db=Depends(get_db)):
    """获取话题分类目录。"""
    repo = TopicRepository(db)
    categories = await repo.list_categories()
    return [TopicCategoryResponse(**item) for item in categories]


@router.get("/topics", response_model=List[TopicResponse])
async def get_topics(
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """获取话题列表（支持分类和关键词搜索）。"""
    topic_repo = TopicRepository(db)
    subscription_repo = SubscriptionRepository(db)

    if q:
        topics = await topic_repo.search(q, limit=limit)
    elif category:
        topics = await topic_repo.get_by_category(category)
    else:
        topics = await topic_repo.get_popular(limit=limit)

    if offset:
        topics = topics[offset:]
    topics = topics[:limit]

    enriched = []
    for topic in topics:
        is_subscribed = await subscription_repo.is_subscribed(user_id, str(topic.id))
        enriched.append(_to_topic_response(topic, is_subscribed=is_subscribed))

    return enriched


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """获取话题详情。"""
    topic_repo = TopicRepository(db)
    subscription_repo = SubscriptionRepository(db)
    topic = await topic_repo.get_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    is_subscribed = await subscription_repo.is_subscribed(user_id, topic_id)
    return _to_topic_response(topic, is_subscribed=is_subscribed)


@router.get("/me", response_model=List[SubscriptionResponse])
async def get_my_subscriptions(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """获取我的订阅。"""
    repo = SubscriptionRepository(db)
    subscriptions = await repo.get_user_subscriptions(user_id, limit=limit, offset=offset)
    return [_to_subscription_response(item) for item in subscriptions]


@router.post("/subscribe")
async def subscribe(
    request: SubscribeRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """订阅话题。"""
    topic_repo = TopicRepository(db)
    topic = await topic_repo.get_by_id(request.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    subscription_repo = SubscriptionRepository(db)
    freemium = FreemiumService(db)
    existing = await subscription_repo.get_by_user_and_topic(
        user_id,
        request.topic_id,
        include_deleted=True,
    )
    will_increase_active = not existing or not existing.is_active or existing.is_deleted
    if will_increase_active:
        await freemium.assert_can_add_subscription(user_id)

    should_increment = False
    if existing:
        if not existing.is_active or existing.is_deleted:
            should_increment = True
        await subscription_repo.update(
            str(existing.id),
            {
                "is_active": True,
                "is_deleted": False,
                "push_enabled": request.push_enabled,
                "push_breaking_only": request.push_breaking_only,
            },
        )
    else:
        await subscription_repo.create(
            {
                "user_id": user_id,
                "topic_id": request.topic_id,
                "push_enabled": request.push_enabled,
                "push_breaking_only": request.push_breaking_only,
            }
        )
        should_increment = True

    if should_increment:
        await topic_repo.increment_subscriber(request.topic_id, 1)

    return {"success": True}


@router.post("/subscribe/keyword")
async def subscribe_by_keyword(
    request: KeywordSubscribeRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """通过关键词创建并订阅话题。"""
    topic_repo = TopicRepository(db)
    slug = _slugify_keyword(request.keyword)
    topic = await topic_repo.get_by_slug(slug)
    if not topic:
        topic = await topic_repo.create(
            {
                "name": request.keyword.strip(),
                "slug": slug,
                "description": f"Keyword subscription: {request.keyword.strip()}",
                "category": request.category,
            }
        )

    subscription_repo = SubscriptionRepository(db)
    freemium = FreemiumService(db)
    existing = await subscription_repo.get_by_user_and_topic(
        user_id,
        str(topic.id),
        include_deleted=True,
    )
    will_increase_active = not existing or not existing.is_active or existing.is_deleted
    if will_increase_active:
        await freemium.assert_can_add_subscription(user_id)

    should_increment = False
    if existing:
        if not existing.is_active or existing.is_deleted:
            should_increment = True
        await subscription_repo.update(
            str(existing.id),
            {
                "is_active": True,
                "is_deleted": False,
                "push_enabled": request.push_enabled,
                "push_breaking_only": request.push_breaking_only,
            },
        )
    else:
        await subscription_repo.create(
            {
                "user_id": user_id,
                "topic_id": str(topic.id),
                "push_enabled": request.push_enabled,
                "push_breaking_only": request.push_breaking_only,
            }
        )
        should_increment = True

    if should_increment:
        await topic_repo.increment_subscriber(str(topic.id), 1)

    return {
        "success": True,
        "topic": _to_topic_response(topic, is_subscribed=True),
    }


@router.patch("/me/{topic_id}")
async def update_subscription(
    topic_id: str,
    request: UpdateSubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """更新订阅设置（优先级、推送开关等）。"""
    repo = SubscriptionRepository(db)
    subscription = await repo.get_by_user_and_topic(user_id, topic_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        return {"success": True}

    await repo.update(str(subscription.id), update_data)
    return {"success": True}


@router.put("/me/reorder")
async def reorder_subscriptions(
    request: ReorderSubscriptionsRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """批量调整订阅优先级。"""
    repo = SubscriptionRepository(db)
    for item in request.items:
        subscription = await repo.get_by_user_and_topic(user_id, item.topic_id)
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail=f"Subscription not found for topic {item.topic_id}",
            )
        await repo.update(str(subscription.id), {"priority": item.priority})
    return {"success": True, "updated": len(request.items)}


@router.delete("/unsubscribe/{topic_id}")
async def unsubscribe(
    topic_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """取消订阅。"""
    repo = SubscriptionRepository(db)
    subscription = await repo.get_by_user_and_topic(user_id, topic_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await repo.update(
        str(subscription.id),
        {
            "is_active": False,
            "push_enabled": False,
        },
    )

    topic_repo = TopicRepository(db)
    await topic_repo.increment_subscriber(topic_id, -1)

    return {"success": True}
