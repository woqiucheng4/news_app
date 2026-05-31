"""Shared helpers for FCM topic naming."""

from __future__ import annotations


def build_fcm_topic_name(topic_id: str) -> str:
    """Build a stable FCM topic name from a topic UUID."""
    normalized = topic_id.strip()
    return f"topic_{normalized}"
