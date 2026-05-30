"""
文章 Repository 实现
"""

from typing import Optional, List
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.article import Article, Source, Event
from ..interfaces import IArticleRepository
from .base import SQLAlchemyRepository


class ArticleRepository(SQLAlchemyRepository, IArticleRepository):
    """文章 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Article)

    async def get_by_url_hash(self, url_hash: str) -> Optional[Article]:
        stmt = select(Article).where(
            Article.url_hash == url_hash,
            Article.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_event_id(self, event_id: str) -> List[Article]:
        stmt = select(Article).where(
            Article.event_id == event_id,
            Article.is_deleted == False,
        ).order_by(Article.published_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search(self, query: str, limit: int = 20) -> List[Article]:
        """全文搜索"""
        stmt = select(Article).where(
            Article.is_deleted == False,
            or_(
                Article.title.ilike(f"%{query}%"),
                Article.content.ilike(f"%{query}%"),
                Article.summary.ilike(f"%{query}%"),
            )
        ).order_by(Article.published_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_for_topic(
        self,
        topic_name: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        """List articles matching a subscribed topic by keyword semantics."""
        normalized = topic_name.strip()
        if not normalized:
            return []

        pattern = f"%{normalized}%"
        stmt = (
            select(Article)
            .where(
                Article.is_deleted == False,
                or_(
                    Article.title.ilike(pattern),
                    Article.content.ilike(pattern),
                    Article.summary.ilike(pattern),
                ),
            )
            .order_by(Article.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, category: str = None, limit: int = 20) -> List[Article]:
        stmt = select(Article).where(Article.is_deleted == False)

        if category:
            stmt = stmt.where(Article.category == category)

        stmt = stmt.order_by(Article.published_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unsummarized(self, limit: int = 100) -> List[Article]:
        stmt = select(Article).where(
            Article.is_deleted == False,
            Article.is_summary_generated == False,
            Article.content.isnot(None),
        ).order_by(Article.created_at.asc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_summary(
        self,
        id: str,
        summary: str,
        model: str,
        relevance_score: Optional[float] = None,
    ) -> bool:
        from datetime import datetime
        stmt = (
            update(Article)
            .where(Article.id == id)
            .values(
                summary=summary,
                summary_model=model,
                summary_generated_at=datetime.utcnow(),
                relevance_score=relevance_score,
                is_summary_generated=True,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_by_source(
        self,
        source_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Article]:
        stmt = select(Article).where(
            Article.source_id == source_id,
            Article.is_deleted == False,
        ).order_by(Article.published_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_trending(self, hours: int = 24, limit: int = 20) -> List[Article]:
        """获取热门文章"""
        from datetime import datetime, timedelta

        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = select(Article).where(
            Article.is_deleted == False,
            Article.created_at >= since,
        ).order_by(Article.view_count.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()


class SourceRepository(SQLAlchemyRepository):
    """信息源 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Source)

    async def get_active_sources(self) -> List[Source]:
        stmt = select(Source).where(
            Source.is_deleted == False,
            Source.is_active == True,
        ).order_by(Source.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_feed_url(self, feed_url: str) -> Optional[Source]:
        stmt = select(Source).where(
            Source.feed_url == feed_url,
            Source.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_fetch_status(
        self,
        id: str,
        success: bool,
        error: str = None,
    ) -> bool:
        from datetime import datetime

        if success:
            stmt = (
                update(Source)
                .where(Source.id == id)
                .values(
                    last_fetched_at=datetime.utcnow(),
                    last_error=None,
                    error_count=0,
                )
            )
        else:
            stmt = (
                update(Source)
                .where(Source.id == id)
                .values(
                    last_error=error,
                    error_count=Source.error_count + 1,
                    is_active=(Source.error_count + 1) < 5,
                )
            )

        result = await self.session.execute(stmt)
        return result.rowcount > 0


class EventRepository(SQLAlchemyRepository):
    """事件 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Event)

    async def get_recent(self, category: str = None, limit: int = 20) -> List[Event]:
        stmt = select(Event).where(Event.is_deleted == False)

        if category:
            stmt = stmt.where(Event.category == category)

        stmt = stmt.order_by(Event.last_updated_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_trending(self, limit: int = 20) -> List[Event]:
        stmt = (
            select(Event)
            .where(Event.is_deleted == False)
            .order_by(Event.article_count.desc(), Event.last_updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_article_hash(self, content_hash: str) -> Optional[Event]:
        stmt = select(Event).where(
            Event.representative_hash == content_hash,
            Event.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_article_count(self, id: str, increment: int = 1) -> bool:
        from datetime import datetime
        stmt = (
            update(Event)
            .where(Event.id == id)
            .values(
                article_count=Event.article_count + increment,
                last_updated_at=datetime.utcnow(),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def sync_source_count(self, event_id: str) -> bool:
        from datetime import datetime

        source_count_stmt = (
            select(func.count(func.distinct(Article.source_id)))
            .where(
                Article.event_id == event_id,
                Article.is_deleted == False,
            )
        )
        source_count_result = await self.session.execute(source_count_stmt)
        source_count = int(source_count_result.scalar() or 0)

        update_stmt = (
            update(Event)
            .where(Event.id == event_id)
            .values(
                source_count=source_count,
                last_updated_at=datetime.utcnow(),
            )
        )
        result = await self.session.execute(update_stmt)
        return result.rowcount > 0
