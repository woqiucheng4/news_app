"""
SQLAlchemy Repository 基类
"""

from typing import Optional, List, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase

from ..interfaces import IRepository


class SQLAlchemyRepository(IRepository):
    """SQLAlchemy Repository 基类"""

    def __init__(self, session: AsyncSession, model: Type[DeclarativeBase]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[Any]:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: Dict[str, Any]) -> Any:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Any]:
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.is_deleted == False)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: str) -> bool:
        """软删除"""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        stmt = select(self.model).where(self.model.is_deleted == False)

        # 应用过滤器
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        stmt = stmt.where(getattr(self.model, key).in_(value))
                    elif isinstance(value, dict):
                        # 支持操作符，如 {"gt": 10}
                        for op, v in value.items():
                            if op == "gt":
                                stmt = stmt.where(getattr(self.model, key) > v)
                            elif op == "gte":
                                stmt = stmt.where(getattr(self.model, key) >= v)
                            elif op == "lt":
                                stmt = stmt.where(getattr(self.model, key) < v)
                            elif op == "lte":
                                stmt = stmt.where(getattr(self.model, key) <= v)
                            elif op == "ne":
                                stmt = stmt.where(getattr(self.model, key) != v)
                    else:
                        stmt = stmt.where(getattr(self.model, key) == value)

        # 排序
        if order_by:
            if order_by.startswith("-"):
                stmt = stmt.order_by(getattr(self.model, order_by[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(self.model, order_by).asc())
        else:
            stmt = stmt.order_by(self.model.created_at.desc())

        # 分页
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: Dict[str, Any] = None) -> int:
        stmt = select(func.count()).select_from(self.model).where(
            self.model.is_deleted == False
        )

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar()
