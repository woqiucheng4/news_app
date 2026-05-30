"""
数据库模块 - 支持连接池、读写分离、自动迁移
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


class DatabaseManager:
    """
    数据库管理器

    支持功能：
    - 连接池管理
    - 读写分离
    - 健康检查
    - 自动重连
    """

    def __init__(self):
        self.settings = get_settings()
        self._write_engine: Optional[AsyncEngine] = None
        self._read_engines: list[AsyncEngine] = []
        self._read_index: int = 0
        self._write_session_factory: Optional[async_sessionmaker] = None
        self._read_session_factories: list[async_sessionmaker] = []

    async def initialize(self):
        """初始化数据库连接"""
        # 创建写引擎（主库）
        self._write_engine = create_async_engine(
            self.settings.database.database_url,
            pool_size=self.settings.database.db_pool_size,
            max_overflow=self.settings.database.db_max_overflow,
            pool_timeout=self.settings.database.db_pool_timeout,
            pool_recycle=self.settings.database.db_pool_recycle,
            pool_pre_ping=True,
            echo=self.settings.debug,
        )

        self._write_session_factory = async_sessionmaker(
            self._write_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # 创建读引擎（从库，可选）
        for url in self.settings.database_read_urls_list:
            engine = create_async_engine(
                url,
                pool_size=self.settings.database.db_pool_size,
                max_overflow=self.settings.database.db_max_overflow,
                pool_pre_ping=True,
                echo=False,
            )
            self._read_engines.append(engine)
            self._read_session_factories.append(
                async_sessionmaker(
                    engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                )
            )

        # 如果没有配置从库，使用主库作为读库
        if not self._read_engines:
            self._read_engines.append(self._write_engine)
            self._read_session_factories.append(self._write_session_factory)

        logger.info(
            f"Database initialized: 1 write engine, "
            f"{len(self._read_engines)} read engines"
        )

    async def close(self):
        """关闭所有数据库连接"""
        if self._write_engine:
            await self._write_engine.dispose()

        for engine in self._read_engines:
            if engine != self._write_engine:
                await engine.dispose()

        logger.info("Database connections closed")

    @asynccontextmanager
    async def get_write_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取写会话（主库）"""
        async with self._write_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def get_read_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取读会话（从库，轮询负载均衡）"""
        factory = self._read_session_factories[self._read_index % len(self._read_session_factories)]
        self._read_index += 1

        async with factory() as session:
            try:
                yield session
            finally:
                await session.close()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取会话（自动选择读写）"""
        # 默认使用写会话，确保一致性
        async with self.get_write_session() as session:
            yield session

    async def health_check(self) -> dict:
        """健康检查"""
        result = {
            "write": False,
            "read_engines": [],
        }

        # 检查写引擎
        try:
            async with self._write_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            result["write"] = True
        except Exception as e:
            logger.error(f"Write engine health check failed: {e}")

        # 检查读引擎
        for i, engine in enumerate(self._read_engines):
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                result["read_engines"].append({"index": i, "status": True})
            except Exception as e:
                logger.error(f"Read engine {i} health check failed: {e}")
                result["read_engines"].append({"index": i, "status": False})

        return result

    async def execute_migration(self, migration_sql: str):
        """执行迁移 SQL"""
        async with self._write_engine.begin() as conn:
            await conn.execute(text(migration_sql))
        logger.info("Migration executed successfully")


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def init_db():
    """初始化数据库"""
    await db_manager.initialize()


async def close_db():
    """关闭数据库"""
    await db_manager.close()


async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取写会话"""
    async with db_manager.get_write_session() as session:
        yield session


async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取读会话"""
    async with db_manager.get_read_session() as session:
        yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取会话"""
    async with db_manager.get_session() as session:
        yield session
