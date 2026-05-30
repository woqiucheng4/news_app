"""
通知模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import BaseModel


class Notification(BaseModel):
    """通知模型"""
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 通知内容
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # daily_briefing, breaking, update

    # 关联
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True)

    # 状态
    is_read = Column(Boolean, default=False, nullable=False)
    is_pushed = Column(Boolean, default=False, nullable=False)
    pushed_at = Column(DateTime, nullable=True)

    # FCM
    fcm_message_id = Column(String(255), nullable=True)

    # 元数据
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)

    def __repr__(self):
        return f"<Notification {self.title[:50]}>"


class PushToken(BaseModel):
    """推送令牌模型"""
    __tablename__ = "push_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # ios, android, web
    device_id = Column(String(255), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<PushToken {self.platform}>"
