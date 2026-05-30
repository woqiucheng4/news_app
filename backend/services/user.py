"""
用户服务实现
"""

from typing import Optional, Dict
from datetime import datetime
import logging

from .interfaces import IUserService
from repositories.sqlalchemy.user import UserRepository
from core.cache import cache_manager

logger = logging.getLogger(__name__)


class UserService(IUserService):
    """用户服务"""

    def __init__(self, user_repo: UserRepository):
        self.repo = user_repo

    async def get_user(self, id: str) -> Optional[Dict]:
        """获取用户信息"""
        cache_key = f"user:{id}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        user = await self.repo.get_by_id(id)
        if not user:
            return None

        result = self._to_dict(user)
        await cache_manager.set(cache_key, result, ttl=300)
        return result

    async def get_or_create_by_oauth(
        self,
        email: str,
        provider: str,
        provider_id: str,
        **kwargs,
    ) -> Dict:
        """通过 OAuth 获取或创建用户"""
        # 尝试通过 provider_id 获取
        user = None
        if provider == "google":
            user = await self.repo.get_by_google_id(provider_id)
        elif provider == "apple":
            user = await self.repo.get_by_apple_id(provider_id)

        if user:
            return self._to_dict(user)

        # 尝试通过邮箱获取
        user = await self.repo.get_by_email(email)
        if user:
            # 更新 OAuth ID
            update_data = {}
            if provider == "google":
                update_data["google_id"] = provider_id
            elif provider == "apple":
                update_data["apple_id"] = provider_id

            if update_data:
                user = await self.repo.update(str(user.id), update_data)
            return self._to_dict(user)

        # 创建新用户
        user_data = {
            "email": email,
            "display_name": kwargs.get("display_name", email.split("@")[0]),
            "avatar_url": kwargs.get("avatar_url"),
            "is_verified": True,  # OAuth 用户默认已验证
        }

        if provider == "google":
            user_data["google_id"] = provider_id
        elif provider == "apple":
            user_data["apple_id"] = provider_id

        user = await self.repo.create(user_data)

        # 创建用户设置
        await self.repo.create_settings(str(user.id))

        return self._to_dict(user)

    async def update_settings(self, user_id: str, settings: Dict) -> bool:
        """更新用户设置"""
        settings_obj = await self.repo.get_settings(user_id)

        if settings_obj:
            # 更新现有设置
            for key, value in settings.items():
                if hasattr(settings_obj, key):
                    setattr(settings_obj, key, value)
        else:
            # 创建新设置
            await self.repo.create_settings(user_id, settings)

        # 清除缓存
        await cache_manager.delete(f"user:{user_id}")

        return True

    async def export_user_data(self, user_id: str) -> Dict:
        """导出用户数据（GDPR）"""
        user = await self.repo.get_by_id(user_id)
        if not user:
            return {}

        # 获取用户设置
        settings = await self.repo.get_settings(user_id)

        return {
            "user": self._to_dict(user),
            "settings": settings.to_dict() if settings else {},
            "exported_at": datetime.utcnow().isoformat(),
        }

    async def delete_user(self, user_id: str) -> bool:
        """删除用户（GDPR）"""
        # 软删除用户
        success = await self.repo.delete(user_id)

        if success:
            # 清除缓存
            await cache_manager.delete(f"user:{user_id}")

        return success

    def _to_dict(self, user) -> Dict:
        """转换为字典"""
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_premium": user.is_premium,
            "is_admin": bool(getattr(user, "is_admin", False)),
            "created_at": user.created_at.isoformat(),
        }
