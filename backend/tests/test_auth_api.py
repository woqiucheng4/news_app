from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import auth as auth_module
from api.v1.router import api_router


class FakeAuthService:
    async def register(self, email: str, password: str, display_name: str = None):
        if email == "exists@example.com":
            raise ValueError("Email already registered")
        return {"access_token": "a", "refresh_token": "r", "token_type": "bearer", "user": {"email": email}}

    async def login(self, email: str, password: str):
        if password == "badpass":
            raise ValueError("Invalid email or password")
        return {"access_token": "a", "refresh_token": "r", "token_type": "bearer"}

    async def oauth_login(self, provider: str, provider_id: str, email: str, display_name: str = None, avatar_url: str = None):
        if provider not in {"google", "apple"}:
            raise ValueError("Unsupported provider")
        return {"access_token": "a", "refresh_token": "r", "token_type": "bearer", "user": {"email": email}}

    async def refresh_access_token(self, refresh_token: str):
        if refresh_token == "bad":
            raise ValueError("Invalid refresh token")
        return {
            "access_token": "new-a",
            "refresh_token": "new-r",
            "token_type": "bearer",
        }


def _build_app():
    app = FastAPI()
    app.include_router(api_router)

    async def override_auth_service():
        return FakeAuthService()

    app.dependency_overrides[auth_module.get_auth_service] = override_auth_service
    return app


def test_auth_api_endpoints():
    client = TestClient(_build_app())

    ok_register = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "secret123", "display_name": "New"},
    )
    assert ok_register.status_code == 200

    bad_register = client.post(
        "/api/v1/auth/register",
        json={"email": "exists@example.com", "password": "secret123"},
    )
    assert bad_register.status_code == 400

    ok_login = client.post("/api/v1/auth/login", json={"email": "new@example.com", "password": "secret123"})
    assert ok_login.status_code == 200

    bad_login = client.post("/api/v1/auth/login", json={"email": "new@example.com", "password": "badpass"})
    assert bad_login.status_code == 401

    ok_oauth = client.post(
        "/api/v1/auth/oauth/google",
        json={"provider_id": "gid", "email": "oauth@example.com"},
    )
    assert ok_oauth.status_code == 200

    bad_oauth = client.post(
        "/api/v1/auth/oauth/github",
        json={"provider_id": "gid", "email": "oauth@example.com"},
    )
    assert bad_oauth.status_code == 400

    ok_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": "good"})
    assert ok_refresh.status_code == 200
    assert ok_refresh.json()["access_token"] == "new-a"
    assert ok_refresh.json()["refresh_token"] == "new-r"

    bad_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": "bad"})
    assert bad_refresh.status_code == 401


def test_login_rate_limit_returns_429(monkeypatch):
    client = TestClient(_build_app())

    async def always_limited(_key: str):
        return auth_module.LOGIN_RATE_LIMIT, 60

    monkeypatch.setattr(auth_module, "_get_login_failure_state", always_limited)

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "new@example.com", "password": "secret123"},
    )
    assert resp.status_code == 429
    assert resp.headers["X-RateLimit-Limit"] == str(auth_module.LOGIN_RATE_LIMIT)


def test_register_rate_limit_returns_429(monkeypatch):
    client = TestClient(_build_app())

    async def consume_denied(_key: str, _limit: int, _window: int):
        return False, 0, 120

    monkeypatch.setattr(auth_module, "_consume_rate_limit_slot", consume_denied)

    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "secret123", "display_name": "New"},
    )
    assert resp.status_code == 429
    assert resp.headers["X-RateLimit-Limit"] == str(auth_module.REGISTER_RATE_LIMIT)


def test_refresh_rate_limit_returns_429(monkeypatch):
    client = TestClient(_build_app())

    async def consume_denied(_key: str, _limit: int, _window: int):
        return False, 0, 120

    monkeypatch.setattr(auth_module, "_consume_rate_limit_slot", consume_denied)

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "good"})
    assert resp.status_code == 429
    assert resp.headers["X-RateLimit-Limit"] == str(auth_module.REFRESH_RATE_LIMIT)
