"""
Optional Firebase Admin initialization for FCM push.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_firebase_initialized = False


def is_firebase_configured() -> bool:
    from .config import get_settings

    settings = get_settings()
    firebase = settings.firebase
    return bool(firebase.credentials_path or firebase.credentials_json)


def is_firebase_initialized() -> bool:
    return _firebase_initialized


def initialize_firebase() -> bool:
    """Initialize Firebase Admin once. Returns True when FCM is available."""
    global _firebase_initialized

    if _firebase_initialized:
        return True

    from .config import get_settings

    settings = get_settings()
    firebase = settings.firebase

    if not firebase.credentials_path and not firebase.credentials_json:
        logger.info("Firebase credentials not configured; FCM push disabled")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        logger.warning("firebase-admin not installed; FCM push disabled")
        return False

    if firebase_admin._apps:
        _firebase_initialized = True
        return True

    try:
        if firebase.credentials_json:
            payload = json.loads(firebase.credentials_json)
            cred = credentials.Certificate(payload)
        else:
            cred = credentials.Certificate(firebase.credentials_path)

        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin initialized for FCM")
        return True
    except Exception as exc:
        logger.warning("Failed to initialize Firebase Admin: %s", exc)
        return False


async def send_fcm_topic_message(
    *,
    topic: str,
    title: str,
    body: str,
    data: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """
    Send a notification to an FCM topic.

    Returns the FCM message ID when sent, or None when Firebase is unavailable.
    """
    import asyncio

    if not initialize_firebase():
        logger.info(
            "FCM topic push skipped (Firebase unavailable): topic=%s title=%s",
            topic,
            title,
        )
        return None

    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        topic=topic,
    )

    def _send() -> str:
        return messaging.send(message)

    return await asyncio.to_thread(_send)


async def send_fcm_token_message(
    *,
    token: str,
    title: str,
    body: str,
    data: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """Send a notification to a single device token."""
    import asyncio

    if not initialize_firebase():
        logger.info(
            "FCM token push skipped (Firebase unavailable): token=%s title=%s",
            token[:12],
            title,
        )
        return None

    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )

    def _send() -> str:
        return messaging.send(message)

    return await asyncio.to_thread(_send)
