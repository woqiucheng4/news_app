"""
API v1 路由注册
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .articles import router as articles_router
from .users import router as users_router
from .subscriptions import router as subscriptions_router
from .notifications import router as notifications_router
from .dashboard import router as dashboard_router
from .analytics import router as analytics_router
from .billing import router as billing_router

api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(articles_router, prefix="/articles", tags=["articles"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(billing_router, prefix="/billing", tags=["billing"])
