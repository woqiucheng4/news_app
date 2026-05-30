"""
用户模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    # 基本信息
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True)
    display_name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # 认证
    hashed_password = Column(String(255), nullable=True)  # 邮箱登录
    supabase_uid = Column(String(255), unique=True, nullable=True, index=True)  # Supabase Auth

    # OAuth
    google_id = Column(String(255), unique=True, nullable=True)
    apple_id = Column(String(255), unique=True, nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    premium_expires_at = Column(DateTime, nullable=True)

    # 设置
    settings = Column(JSONB, default={}, nullable=False)

    # 关系
    subscriptions = relationship("Subscription", back_populates="user", lazy="selectin")
    bookmarks = relationship("Bookmark", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def is_premium_active(self) -> bool:
        """检查高级会员是否有效"""
        if not self.is_premium:
            return False
        if self.premium_expires_at and self.premium_expires_at < datetime.utcnow():
            return False
        return True


class UserSettings(BaseModel):
    """用户设置模型"""
    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # 通知设置
    push_enabled = Column(Boolean, default=True, nullable=False)
    push_daily_briefing = Column(Boolean, default=True, nullable=False)
    push_breaking_news = Column(Boolean, default=True, nullable=False)
    push_max_per_day = Column(Integer, default=5, nullable=False)
    quiet_hours_start = Column(Integer, nullable=True)  # 0-23
    quiet_hours_end = Column(Integer, nullable=True)  # 0-23

    # 显示设置
    language = Column(String(10), default="en", nullable=False)
    theme = Column(String(20), default="system", nullable=False)  # light, dark, system
    font_size = Column(String(20), default="medium", nullable=False)  # small, medium, large

    # 摘要设置
    summary_length = Column(String(20), default="balanced", nullable=False)  # short, balanced, detailed
    summary_language = Column(String(10), default="auto", nullable=False)  # auto, en, zh, ...

    # 其他设置
    extra = Column(JSONB, default={}, nullable=False)
