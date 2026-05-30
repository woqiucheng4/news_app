"""Client analytics event model."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class ClientAnalyticsEvent(BaseModel):
    """Persisted client-side analytics event."""

    __tablename__ = "client_analytics_events"

    event_name = Column(String(40), nullable=False, index=True)
    params = Column(JSONB, default=dict, nullable=False)
    event_at = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    client_ip = Column(String(64), nullable=True)
