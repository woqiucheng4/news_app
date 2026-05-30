"""
订阅模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class Topic(BaseModel):
    """话题模型"""
    __tablename__ = "topics"

    name = Column(String(200), nullable=False, unique=True)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # 统计
    subscriber_count = Column(Integer, default=0, nullable=False)
    article_count = Column(Integer, default=0, nullable=False)

    # 图标
    icon_url = Column(String(500), nullable=True)

    # 元数据
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)

    # 关系
    subscriptions = relationship("Subscription", back_populates="topic", lazy="selectin")

    def __repr__(self):
        return f"<Topic {self.name}>"


class Subscription(BaseModel):
    """订阅模型"""
    __tablename__ = "subscriptions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)

    # 设置
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 优先级，用于排序

    # 通知设置
    push_enabled = Column(Boolean, default=True, nullable=False)
    push_breaking_only = Column(Boolean, default=False, nullable=False)

    # 时间
    subscribed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_read_at = Column(DateTime, nullable=True)

    # 关系
    user = relationship("User", back_populates="subscriptions")
    topic = relationship("Topic", back_populates="subscriptions")

    # 唯一约束
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),
    )

    def __repr__(self):
        return f"<Subscription user={self.user_id} topic={self.topic_id}>"


class UserFeed(BaseModel):
    """用户自定义信息源"""
    __tablename__ = "user_feeds"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)

    # 自定义源信息
    custom_url = Column(String(500), nullable=True)
    custom_name = Column(String(200), nullable=True)
    feed_type = Column(String(50), nullable=False)  # rss, url, keyword

    # 设置
    is_active = Column(Boolean, default=True, nullable=False)
    fetch_interval = Column(Integer, default=60, nullable=False)  # 分钟

    # 关系
    user = relationship("User")
    source = relationship("Source")

    def __repr__(self):
        return f"<UserFeed user={self.user_id}>"
