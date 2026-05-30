from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import auth as auth_module
from api.v1 import users as users_module
from api.v1.router import api_router
from services.auth import AuthService
from services.user import UserService


class InMemoryUserRepo:
    def __init__(self):
        self.users: dict[str, SimpleNamespace] = {}
        self.settings: dict[str, SimpleNamespace] = {}

    async def get_by_email(self, email: str):
        for user in self.users.values():
            if user.email == email and not user.is_deleted:
                return user
        return None

    async def get_by_id(self, user_id: str):
        user = self.users.get(str(user_id))
        if not user or user.is_deleted:
            return None
        return user

    async def get_by_google_id(self, provider_id: str):
        for user in self.users.values():
            if user.google_id == provider_id and not user.is_deleted:
                return user
        return None

    async def get_by_apple_id(self, provider_id: str):
        for user in self.users.values():
            if user.apple_id == provider_id and not user.is_deleted:
                return user
        return None

    async def create(self, data: dict):
        user_id = str(uuid4())
        user = SimpleNamespace(
            id=user_id,
            email=data["email"],
            username=None,
            display_name=data.get("display_name"),
            avatar_url=data.get("avatar_url"),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", True),
            is_premium=data.get("is_premium", False),
            hashed_password=data.get("hashed_password"),
            google_id=data.get("google_id"),
            apple_id=data.get("apple_id"),
            is_deleted=False,
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        self.users[user_id] = user
        return user

    async def update(self, user_id: str, data: dict):
        user = self.users[str(user_id)]
        for key, value in data.items():
            setattr(user, key, value)
        return user

    async def create_settings(self, user_id: str, settings: dict = None):
        payload = settings or {}
        settings_obj = SimpleNamespace(
            push_enabled=payload.get("push_enabled", True),
            push_daily_briefing=payload.get("push_daily_briefing", True),
            push_breaking_news=payload.get("push_breaking_news", True),
            push_max_per_day=payload.get("push_max_per_day", 10),
            language=payload.get("language", "en"),
            theme=payload.get("theme", "light"),
            to_dict=lambda: {
                "push_enabled": settings_obj.push_enabled,
                "push_daily_briefing": settings_obj.push_daily_briefing,
                "push_breaking_news": settings_obj.push_breaking_news,
                "push_max_per_day": settings_obj.push_max_per_day,
                "language": settings_obj.language,
                "theme": settings_obj.theme,
            },
        )
        self.settings[str(user_id)] = settings_obj
        return settings_obj

    async def get_settings(self, user_id: str):
        return self.settings.get(str(user_id))

    async def delete(self, user_id: str):
        user = self.users.get(str(user_id))
        if not user or user.is_deleted:
            return False
        user.is_deleted = True
        user.is_active = False
        return True


def _build_test_app(repo: InMemoryUserRepo) -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)

    async def override_auth_service():
        return AuthService(repo)

    async def override_user_service():
        return UserService(repo)

    app.dependency_overrides[auth_module.get_auth_service] = override_auth_service
    app.dependency_overrides[users_module.get_user_service] = override_user_service
    return app


def test_auth_oauth_user_and_gdpr_uat_flow(monkeypatch):
    monkeypatch.setattr("services.auth.hash_password", lambda pwd: f"hashed:{pwd}")
    monkeypatch.setattr("services.auth.verify_password", lambda plain, hashed: hashed == f"hashed:{plain}")
    cache_store = {}

    async def fake_cache_get(key: str):
        return cache_store.get(key)

    async def fake_cache_set(key: str, value, ttl: int):
        cache_store[key] = value
        return True

    async def fake_cache_delete(key: str):
        cache_store.pop(key, None)
        return True

    monkeypatch.setattr("services.user.cache_manager.get", fake_cache_get)
    monkeypatch.setattr("services.user.cache_manager.set", fake_cache_set)
    monkeypatch.setattr("services.user.cache_manager.delete", fake_cache_delete)

    repo = InMemoryUserRepo()
    client = TestClient(_build_test_app(repo))

    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@test.com", "password": "abcdef", "display_name": "Alice"},
    )
    assert register_resp.status_code == 200
    register_body = register_resp.json()
    base_user_id = register_body["user"]["id"]
    access_token = register_body["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Google OAuth should merge into existing account by email.
    oauth_google = client.post(
        "/api/v1/auth/oauth/google",
        json={"provider_id": "google-provider-1", "email": "alice@test.com"},
    )
    assert oauth_google.status_code == 200
    assert oauth_google.json()["user"]["id"] == base_user_id

    # Apple OAuth should also merge into same account.
    oauth_apple = client.post(
        "/api/v1/auth/oauth/apple",
        json={"provider_id": "apple-provider-1", "email": "alice@test.com"},
    )
    assert oauth_apple.status_code == 200
    assert oauth_apple.json()["user"]["id"] == base_user_id

    # /users/me with bearer token.
    me_resp = client.get("/api/v1/users/me", headers=auth_headers)
    assert me_resp.status_code == 200
    me_body = me_resp.json()
    assert me_body["id"] == base_user_id
    assert {"email", "display_name", "is_active", "is_verified", "is_premium", "is_admin"}.issubset(me_body.keys())
    assert me_body["is_admin"] is False

    # /users/me without auth should be rejected.
    me_no_auth = client.get("/api/v1/users/me")
    assert me_no_auth.status_code == 401

    # Update settings.
    settings_resp = client.put(
        "/api/v1/users/me/settings",
        headers=auth_headers,
        json={"push_enabled": True, "language": "zh-CN", "theme": "dark"},
    )
    assert settings_resp.status_code == 200
    assert settings_resp.json()["success"] is True

    # Export GDPR payload.
    export_resp = client.get("/api/v1/users/me/export", headers=auth_headers)
    assert export_resp.status_code == 200
    export_body = export_resp.json()
    assert "user" in export_body and "settings" in export_body and "exported_at" in export_body
    assert export_body["user"]["id"] == base_user_id
    assert export_body["settings"]["theme"] == "dark"

    # Delete account and verify old token no longer fetches user profile.
    delete_resp = client.delete("/api/v1/users/me", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    me_after_delete = client.get("/api/v1/users/me", headers=auth_headers)
    assert me_after_delete.status_code in {401, 404}

    # Edge case: re-register same email after deletion.
    register_after_delete = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@test.com", "password": "abcdef", "display_name": "Alice2"},
    )
    assert register_after_delete.status_code in {200, 400}
    if register_after_delete.status_code == 200:
        assert register_after_delete.json()["user"]["id"] != base_user_id
