"""
文章模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    Text,
    Index,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from .base import BaseModel


class Source(BaseModel):
    """信息源模型"""
    __tablename__ = "sources"

    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)  # rss, web, api
    feed_url = Column(String(500), nullable=True)  # RSS feed URL

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    last_fetched_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)

    # 元数据
    category = Column(String(100), nullable=True)
    language = Column(String(10), default="en", nullable=False)
    fetch_interval_minutes = Column(Integer, default=30, nullable=False)
    heat_score = Column(Numeric(10, 2), default=0, nullable=False)
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)

    # 关系
    articles = relationship("Article", back_populates="source", lazy="selectin")

    def __repr__(self):
        return f"<Source {self.name}>"


class Article(BaseModel):
    """文章模型"""
    __tablename__ = "articles"

    # 基本信息
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    content = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)  # 摘录

    # 来源
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True)
    author = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)

    # 分类
    category = Column(String(100), nullable=True, index=True)
    tags = Column(ARRAY(String), default=[], nullable=False)

    # 去重字段
    url_hash = Column(String(64), unique=True, nullable=False, index=True)
    title_hash = Column(String(64), nullable=True, index=True)
    content_hash = Column(String(64), nullable=True, index=True)
    simhash = Column(String(64), nullable=True, index=True)

    # AI 摘要
    summary = Column(Text, nullable=True)
    summary_model = Column(String(50), nullable=True)
    summary_generated_at = Column(DateTime, nullable=True)
    relevance_score = Column(Numeric(3, 1), nullable=True)

    # 事件聚类
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True, index=True)

    # 状态
    is_processed = Column(Boolean, default=False, nullable=False)
    is_summary_generated = Column(Boolean, default=False, nullable=False)

    # 统计
    view_count = Column(Integer, default=0, nullable=False)
    bookmark_count = Column(Integer, default=0, nullable=False)

    # 元数据
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)

    # 关系
    source = relationship("Source", back_populates="articles", lazy="selectin")
    event = relationship("Event", back_populates="articles", lazy="selectin")
    bookmarks = relationship("Bookmark", back_populates="article", lazy="selectin")

    # 索引
    __table_args__ = (
        Index("idx_articles_source_published", "source_id", "published_at"),
        Index("idx_articles_category_published", "category", "published_at"),
    )

    def __repr__(self):
        return f"<Article {self.title[:50]}>"


class Event(BaseModel):
    """事件模型（用于事件聚类）"""
    __tablename__ = "events"

    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # 代表性信息
    representative_article_id = Column(UUID(as_uuid=True), nullable=True)
    representative_hash = Column(String(64), nullable=True)

    # 统计
    article_count = Column(Integer, default=1, nullable=False)
    source_count = Column(Integer, default=1, nullable=False)

    # 时间
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    articles = relationship("Article", back_populates="event", lazy="selectin")

    def __repr__(self):
        return f"<Event {self.title[:50]}>"


class Bookmark(BaseModel):
    """书签模型"""
    __tablename__ = "bookmarks"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False, index=True)
    note = Column(Text, nullable=True)

    # 关系
    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")

    # 唯一约束
    __table_args__ = (
        {"comment": "用户书签"},
    )
