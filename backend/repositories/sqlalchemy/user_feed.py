"""
User custom feed repository.
"""

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.subscription import UserFeed
from .base import SQLAlchemyRepository


class UserFeedRepository(SQLAlchemyRepository):
    """Repository for user-defined RSS / URL feeds."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserFeed)

    async def get_by_user_and_url(self, user_id: str, url: str) -> Optional[UserFeed]:
        stmt = select(UserFeed).where(
            UserFeed.user_id == user_id,
            UserFeed.custom_url == url,
            UserFeed.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str, limit: int = 100) -> List[UserFeed]:
        stmt = (
            select(UserFeed)
            .where(
                UserFeed.user_id == user_id,
                UserFeed.is_deleted == False,
            )
            .order_by(UserFeed.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
