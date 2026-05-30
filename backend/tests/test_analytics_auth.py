"""Tests for analytics dashboard access control."""

from pathlib import Path
import sys

import pytest
from fastapi import HTTPException
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.analytics_auth import verify_analytics_dashboard_access
from core.config import get_settings
from core.security import create_access_token


def _make_request(headers=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope)


def test_dashboard_open_when_unrestricted(monkeypatch):
    monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)
    monkeypatch.delenv("ANALYTICS_ADMIN_EMAILS", raising=False)
    get_settings.cache_clear()

    verify_analytics_dashboard_access(_make_request())


def test_dashboard_allows_admin_jwt(monkeypatch):
    monkeypatch.setenv("ANALYTICS_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)
    get_settings.cache_clear()

    token = create_access_token(subject="user-admin", email="admin@example.com")
    verify_analytics_dashboard_access(
        _make_request(headers={"Authorization": f"Bearer {token}"})
    )


def test_dashboard_allows_is_admin_jwt_claim(monkeypatch):
    monkeypatch.setenv("ANALYTICS_DASHBOARD_TOKEN", "secret-token")
    monkeypatch.delenv("ANALYTICS_ADMIN_EMAILS", raising=False)
    get_settings.cache_clear()

    token = create_access_token(
        subject="admin-user",
        email="regular@example.com",
        is_admin=True,
    )
    verify_analytics_dashboard_access(
        _make_request(headers={"Authorization": f"Bearer {token}"})
    )

    get_settings.cache_clear()


def test_dashboard_rejects_non_admin_jwt(monkeypatch):
    monkeypatch.setenv("ANALYTICS_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.delenv("ANALYTICS_DASHBOARD_TOKEN", raising=False)
    get_settings.cache_clear()

    token = create_access_token(subject="user-1", email="user@example.com")
    with pytest.raises(HTTPException) as exc:
        verify_analytics_dashboard_access(
            _make_request(headers={"Authorization": f"Bearer {token}"})
        )

    assert exc.value.status_code == 403

    get_settings.cache_clear()
