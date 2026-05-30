from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.user import UserService


def _make_user(user_id: str = None, email: str = "user@example.com"):
    return SimpleNamespace(
        id=user_id or str(uuid4()),
        email=email,
        username="tester",
        display_name="Tester",
        avatar_url=None,
        is_active=True,
        is_verified=True,
        is_premium=False,
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        google_id=None,
        apple_id=None,
    )


class FakeUserRepo:
    def __init__(self):
        self.user = _make_user("u-1")
        self.settings = SimpleNamespace(
            push_enabled=True,
            theme="light",
            to_dict=lambda: {"push_enabled": True, "theme": "light"},
        )
        self.deleted_ids: list[str] = []

    async def get_by_id(self, user_id: str):
        return self.user if user_id in {"u-1", "current_user_id"} else None

    async def get_by_google_id(self, provider_id: str):
        return self.user if provider_id == "g-id-exists" else None

    async def get_by_apple_id(self, provider_id: str):
        return self.user if provider_id == "a-id-exists" else None

    async def get_by_email(self, email: str):
        return self.user if email == "user@example.com" else None

    async def update(self, user_id: str, data: dict):
        for key, value in data.items():
            setattr(self.user, key, value)
        return self.user

    async def create(self, data: dict):
        self.user = _make_user("new-u", email=data["email"])
        self.user.display_name = data.get("display_name")
        self.user.avatar_url = data.get("avatar_url")
        self.user.google_id = data.get("google_id")
        self.user.apple_id = data.get("apple_id")
        return self.user

    async def create_settings(self, user_id: str, settings: dict = None):
        payload = settings or {}
        self.settings = SimpleNamespace(
            **payload,
            to_dict=lambda: payload,
        )
        return self.settings

    async def get_settings(self, user_id: str):
        return self.settings

    async def delete(self, user_id: str):
        self.deleted_ids.append(user_id)
        return True


@pytest.mark.asyncio
async def test_user_service_full_flow(monkeypatch):
    repo = FakeUserRepo()
    service = UserService(repo)
    cache_store = {}

    async def fake_cache_get(key: str):
        return cache_store.get(key)

    async def fake_cache_set(key: str, value: dict, ttl: int):
        cache_store[key] = value
        return True

    async def fake_cache_delete(key: str):
        cache_store.pop(key, None)
        return True

    monkeypatch.setattr("services.user.cache_manager.get", fake_cache_get)
    monkeypatch.setattr("services.user.cache_manager.set", fake_cache_set)
    monkeypatch.setattr("services.user.cache_manager.delete", fake_cache_delete)

    user = await service.get_user("u-1")
    assert user["email"] == "user@example.com"
    assert "user:u-1" in cache_store

    # Hit cache branch.
    cached_user = await service.get_user("u-1")
    assert cached_user["id"] == user["id"]

    existing_by_provider = await service.get_or_create_by_oauth(
        email="user@example.com",
        provider="google",
        provider_id="g-id-exists",
    )
    assert existing_by_provider["id"] == "u-1"

    existing_by_email = await service.get_or_create_by_oauth(
        email="user@example.com",
        provider="apple",
        provider_id="a-id-new",
    )
    assert existing_by_email["id"] == "u-1"
    assert repo.user.apple_id == "a-id-new"

    created = await service.get_or_create_by_oauth(
        email="new@example.com",
        provider="google",
        provider_id="g-id-new",
        display_name="New User",
    )
    assert created["email"] == "new@example.com"
    assert repo.user.google_id == "g-id-new"

    updated = await service.update_settings("u-1", {"theme": "dark"})
    assert updated is True

    exported = await service.export_user_data("u-1")
    assert exported["user"]["id"] == "new-u" or exported["user"]["id"] == "u-1"
    assert "exported_at" in exported

    deleted = await service.delete_user("u-1")
    assert deleted is True
    assert "u-1" in repo.deleted_ids
