"""Analytics dashboard access control."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, Query, Request, status

from core.config import get_settings
from core.security import decode_token


def _decode_bearer_payload(request: Request) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        payload = decode_token(token)
    except ValueError:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def verify_analytics_dashboard_access(
    request: Request,
    token: Optional[str] = Query(default=None),
) -> None:
    """Require dashboard token or admin JWT when analytics access is restricted."""
    settings = get_settings()
    expected_token = settings.analytics.dashboard_token
    admin_emails = settings.analytics.admin_emails_list

    if not expected_token and not admin_emails:
        return

    provided_token = request.headers.get("X-Analytics-Token") or token
    if expected_token and provided_token == expected_token:
        return

    payload = _decode_bearer_payload(request)
    if payload:
        if payload.get("is_admin") is True:
            return

        email = payload.get("email")
        if email and admin_emails and str(email).strip().lower() in admin_emails:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid analytics dashboard token",
    )
