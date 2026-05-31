"""
用户 API
"""

from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user_id, get_db
from repositories.sqlalchemy.user import UserRepository
from services.user import UserService
from services.freemium import FreemiumService

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_premium: bool
    is_admin: bool = False
    created_at: str


class UserSettingsUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    push_daily_briefing: Optional[bool] = None
    push_breaking_news: Optional[bool] = None
    push_max_per_day: Optional[int] = None
    language: Optional[str] = None
    theme: Optional[str] = None


class EntitlementsResponse(BaseModel):
    is_premium: bool
    max_topic_subscriptions: Optional[int] = None
    topic_subscriptions_used: int
    daily_article_views_limit: Optional[int] = None
    daily_article_views_used: int
    can_subscribe_more: bool
    can_view_articles: bool
    features: dict
    premium_product_id: str


async def get_user_service(db=Depends(get_db)) -> UserService:
    """依赖注入：获取用户服务"""
    repo = UserRepository(db)
    return UserService(repo)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """获取当前用户信息"""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/entitlements", response_model=EntitlementsResponse)
async def get_entitlements(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get freemium limits and current usage for the signed-in user."""
    service = FreemiumService(db)
    return await service.get_entitlements(user_id)


@router.put("/me/settings")
async def update_settings(
    settings: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """更新用户设置"""
    success = await service.update_settings(user_id, settings.model_dump(exclude_unset=True))
    return {"success": success}


@router.get("/me/export")
async def export_user_data(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """导出用户数据（GDPR）"""
    return await service.export_user_data(user_id)


@router.delete("/me")
async def delete_user(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """删除用户（GDPR）"""
    success = await service.delete_user(user_id)
    return {"success": success}
