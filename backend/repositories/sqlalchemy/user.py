"""
用户 Repository 实现
"""

from typing import Optional, List, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserSettings
from models.subscription import Subscription, Topic
from ..interfaces import IUserRepository, ISubscriptionRepository, ITopicRepository
from .base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository, IUserRepository):
    """用户 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(
            User.email == email,
            User.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_supabase_uid(self, uid: str) -> Optional[User]:
        stmt = select(User).where(
            User.supabase_uid == uid,
            User.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        stmt = select(User).where(
            User.google_id == google_id,
            User.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_apple_id(self, apple_id: str) -> Optional[User]:
        stmt = select(User).where(
            User.apple_id == apple_id,
            User.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_settings(self, user_id: str) -> Optional[UserSettings]:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_settings(self, user_id: str, settings: dict = None) -> UserSettings:
        settings_data = {"user_id": user_id, **(settings or {})}
        instance = UserSettings(**settings_data)
        self.session.add(instance)
        await self.session.flush()
        return instance


class TopicRepository(SQLAlchemyRepository, ITopicRepository):
    """话题 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Topic)

    async def get_by_slug(self, slug: str) -> Optional[Topic]:
        stmt = select(Topic).where(
            Topic.slug == slug,
            Topic.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, query: str, limit: int = 20) -> List[Topic]:
        stmt = select(Topic).where(
            Topic.is_deleted == False,
            Topic.name.ilike(f"%{query}%"),
        ).order_by(Topic.subscriber_count.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_popular(self, limit: int = 20) -> List[Topic]:
        stmt = select(Topic).where(
            Topic.is_deleted == False,
        ).order_by(Topic.subscriber_count.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_categories(self) -> List[Dict[str, int]]:
        stmt = (
            select(
                Topic.category,
                func.count(Topic.id).label("topic_count"),
            )
            .where(
                Topic.is_deleted == False,
                Topic.category.isnot(None),
            )
            .group_by(Topic.category)
            .order_by(func.count(Topic.id).desc(), Topic.category.asc())
        )
        result = await self.session.execute(stmt)
        return [
            {"name": row.category, "topic_count": row.topic_count}
            for row in result.all()
        ]

    async def get_by_category(self, category: str) -> List[Topic]:
        stmt = select(Topic).where(
            Topic.is_deleted == False,
            Topic.category == category,
        ).order_by(Topic.subscriber_count.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_with_subscribers(self) -> List[Topic]:
        stmt = select(Topic).where(
            Topic.is_deleted == False,
            Topic.subscriber_count > 0,
        ).order_by(Topic.subscriber_count.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def increment_subscriber(self, id: str, increment: int = 1) -> bool:
        from sqlalchemy import update
        stmt = (
            update(Topic)
            .where(Topic.id == id)
            .values(subscriber_count=Topic.subscriber_count + increment)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class SubscriptionRepository(SQLAlchemyRepository, ISubscriptionRepository):
    """订阅 Repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Subscription)

    async def get_user_subscriptions(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Subscription]:
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_deleted == False,
            Subscription.is_active == True,
        ).order_by(
            Subscription.priority.desc(),
            Subscription.subscribed_at.desc(),
        ).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def is_subscribed(self, user_id: str, topic_id: str) -> bool:
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.topic_id == topic_id,
            Subscription.is_deleted == False,
            Subscription.is_active == True,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_topic_subscribers(self, topic_id: str) -> List[str]:
        stmt = select(Subscription.user_id).where(
            Subscription.topic_id == topic_id,
            Subscription.is_deleted == False,
            Subscription.is_active == True,
            Subscription.push_enabled == True,
        )
        result = await self.session.execute(stmt)
        return [str(row) for row in result.scalars().all()]

    async def get_by_user_and_topic(
        self,
        user_id: str,
        topic_id: str,
        include_deleted: bool = False,
    ) -> Optional[Subscription]:
        conditions = [
            Subscription.user_id == user_id,
            Subscription.topic_id == topic_id,
        ]
        if not include_deleted:
            conditions.append(Subscription.is_deleted == False)

        stmt = select(Subscription).where(*conditions)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
