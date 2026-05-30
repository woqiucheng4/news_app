"""
认证服务：邮箱注册/登录、OAuth 登录、刷新 token。
"""

from typing import Dict

from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from repositories.sqlalchemy.user import UserRepository
from services.user import UserService


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.user_service = UserService(user_repo)

    async def register(self, email: str, password: str, display_name: str = None) -> Dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        user = await self.user_repo.create(
            {
                "email": email,
                "display_name": display_name or email.split("@")[0],
                "hashed_password": hash_password(password),
                "is_active": True,
                "is_verified": True,
            }
        )
        await self.user_repo.create_settings(str(user.id))
        return self._build_auth_response(user)

    async def login(self, email: str, password: str) -> Dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            raise ValueError("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        return self._build_auth_response(user)

    async def oauth_login(
        self,
        provider: str,
        provider_id: str,
        email: str,
        display_name: str = None,
        avatar_url: str = None,
    ) -> Dict:
        if provider not in {"google", "apple"}:
            raise ValueError("Unsupported provider")

        user_dict = await self.user_service.get_or_create_by_oauth(
            email=email,
            provider=provider,
            provider_id=provider_id,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        user = await self.user_repo.get_by_id(user_dict["id"])
        return self._build_auth_response(user)

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        return {
            "access_token": create_access_token(
                subject=str(user.id),
                email=user.email,
                is_premium=user.is_premium,
                is_admin=bool(getattr(user, "is_admin", False)),
            ),
            "refresh_token": create_refresh_token(subject=str(user.id)),
            "token_type": "bearer",
        }

    def _build_auth_response(self, user) -> Dict:
        return {
            "access_token": create_access_token(
                subject=str(user.id),
                email=user.email,
                is_premium=user.is_premium,
                is_admin=bool(getattr(user, "is_admin", False)),
            ),
            "refresh_token": create_refresh_token(subject=str(user.id)),
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "is_premium": user.is_premium,
            },
        }
