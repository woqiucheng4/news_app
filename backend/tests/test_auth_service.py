from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.auth import AuthService


def _make_user(user_id: str, email: str, hashed_password: str = "hashed"):
    return SimpleNamespace(
        id=user_id,
        email=email,
        display_name="User",
        is_premium=False,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
    )


class FakeUserRepo:
    def __init__(self):
        self.users = {}

    async def get_by_email(self, email: str):
        return next((item for item in self.users.values() if item.email == email), None)

    async def get_by_id(self, user_id: str):
        return self.users.get(str(user_id))

    async def create(self, data: dict):
        user_id = str(uuid4())
        user = _make_user(user_id, data["email"], data.get("hashed_password"))
        user.display_name = data.get("display_name")
        self.users[user_id] = user
        return user

    async def create_settings(self, user_id: str, settings: dict = None):
        return SimpleNamespace(user_id=user_id)

    async def get_by_google_id(self, provider_id: str):
        return None

    async def get_by_apple_id(self, provider_id: str):
        return None

    async def update(self, user_id: str, data: dict):
        user = self.users[str(user_id)]
        for k, v in data.items():
            setattr(user, k, v)
        return user


@pytest.mark.asyncio
async def test_auth_service_register_login_refresh(monkeypatch):
    repo = FakeUserRepo()
    service = AuthService(repo)

    monkeypatch.setattr("services.auth.hash_password", lambda pwd: f"hashed:{pwd}")
    monkeypatch.setattr("services.auth.verify_password", lambda plain, hashed: hashed == f"hashed:{plain}")
    monkeypatch.setattr("services.auth.create_access_token", lambda **kwargs: "access-token")
    refresh_tokens = iter(["refresh-token", "refresh-token-2"])
    monkeypatch.setattr(
        "services.auth.create_refresh_token",
        lambda **kwargs: next(refresh_tokens, "refresh-token-2"),
    )
    monkeypatch.setattr("services.auth.decode_token", lambda token: {"sub": next(iter(repo.users.keys())), "type": "refresh"})

    async def fake_get_or_create_by_oauth(_self, **kwargs):
        return {"id": next(iter(repo.users.keys())), "email": kwargs["email"]}

    monkeypatch.setattr("services.auth.UserService.get_or_create_by_oauth", fake_get_or_create_by_oauth)

    registered = await service.register("user@example.com", "secret123", "Name")
    assert registered["access_token"] == "access-token"
    assert registered["refresh_token"] == "refresh-token"

    logged = await service.login("user@example.com", "secret123")
    assert logged["token_type"] == "bearer"

    oauth = await service.oauth_login("google", "gid", "user@example.com", "Name")
    assert oauth["user"]["email"] == "user@example.com"

    refreshed = await service.refresh_access_token("refresh-token")
    assert refreshed["access_token"] == "access-token"
    assert refreshed["refresh_token"] == "refresh-token-2"

    with pytest.raises(ValueError):
        await service.login("user@example.com", "wrong-pass")
