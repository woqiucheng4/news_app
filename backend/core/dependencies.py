"""
依赖注入模块 - FastAPI 依赖注入配置
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_write_session, get_read_session, db_manager
from .cache import cache_manager
from .tasks import task_manager
from .storage import storage_manager
from .ai import ai_manager
from .config import Settings, get_settings
from .security import decode_token


bearer_scheme = HTTPBearer(auto_error=False)


async def get_settings_dep() -> Settings:
    """获取配置"""
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（写）"""
    async with db_manager.get_write_session() as session:
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（读）"""
    async with db_manager.get_read_session() as session:
        yield session


async def get_cache():
    """获取缓存管理器"""
    return cache_manager


async def get_task_manager():
    """获取任务管理器"""
    return task_manager


async def get_storage():
    """获取存储管理器"""
    return storage_manager


async def get_ai_service():
    """获取 AI 服务"""
    return ai_manager


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """从 Bearer token 解析当前用户 ID。"""
    # Test and local-debug fallback.
    x_user_id = request.headers.get("x-user-id")
    if x_user_id:
        return x_user_id

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
        )

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload",
        )

    return str(user_id)


async def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[str]:
    """Resolve user ID from header or Bearer token without requiring auth."""
    x_user_id = request.headers.get("x-user-id")
    if x_user_id:
        return x_user_id.strip()

    if not credentials or credentials.scheme.lower() != "bearer":
        return None

    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    return str(user_id) if user_id else None


class ServiceContainer:
    """服务容器 - 集中管理所有服务实例"""

    def __init__(self):
        self.settings: Settings = get_settings()
        self.db = db_manager
        self.cache = cache_manager
        self.tasks = task_manager
        self.storage = storage_manager
        self.ai = ai_manager

    async def initialize(self):
        """初始化所有服务"""
        from .database import init_db
        from .cache import init_cache
        from .tasks import init_tasks
        from .storage import init_storage
        from .ai import init_ai
        from services import article as _article_tasks
        _ = _article_tasks  # ensure task decorators are registered before init_tasks

        await init_db()
        await init_cache()
        await init_tasks()
        await init_storage()
        await init_ai()

    async def close(self):
        """关闭所有服务"""
        from .database import close_db
        from .cache import close_cache
        from .storage import close_storage

        await close_db()
        await close_cache()
        await close_storage()

    async def health_check(self) -> dict:
        """健康检查"""
        return {
            "database": await self.db.health_check(),
            "cache": await self.cache.health_check(),
            "tasks": await self.tasks.health_check(),
            "storage": await self.storage.health_check(),
            "ai": await self.ai.health_check(),
        }


# 全局服务容器
services = ServiceContainer()
