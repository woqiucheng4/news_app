"""
缓存模块 - 多级缓存支持，可扩展为 Redis Cluster
"""

from typing import Optional, Any
from abc import ABC, abstractmethod
from functools import wraps
import json
import hashlib
import asyncio
from datetime import datetime
import logging

import redis.asyncio as redis
from redis.sentinel import Sentinel

from .config import get_settings

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """缓存后端抽象接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        pass

    @abstractmethod
    async def clear(self, pattern: str = "*") -> int:
        """清除匹配的缓存"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class LocalCache(CacheBackend):
    """
    本地内存缓存（L1 缓存）

    特点：
    - 速度极快（微秒级）
    - 容量有限
    - 进程内共享
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_order: list[str] = []

    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expire_at = self._cache[key]
            if expire_at > asyncio.get_event_loop().time():
                # 更新访问顺序
                self._access_order.remove(key)
                self._access_order.append(key)
                return value
            else:
                # 过期删除
                del self._cache[key]
                self._access_order.remove(key)
        return None

    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        # 清理过期和 LRU
        await self._cleanup()

        expire_at = asyncio.get_event_loop().time() + ttl
        self._cache[key] = (value, expire_at)

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return True

    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self, pattern: str = "*") -> int:
        if pattern == "*":
            count = len(self._cache)
            self._cache.clear()
            self._access_order.clear()
            return count
        return 0

    async def health_check(self) -> bool:
        return True

    async def _cleanup(self):
        """清理过期和超出容量的缓存"""
        now = asyncio.get_event_loop().time()

        # 清理过期
        expired_keys = [
            k for k, (_, exp) in self._cache.items()
            if exp <= now
        ]
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

        # LRU 淘汰
        while len(self._cache) >= self.max_size:
            oldest_key = self._access_order[0]
            del self._cache[oldest_key]
            self._access_order.remove(oldest_key)


class RedisCache(CacheBackend):
    """
    Redis 缓存（L2 缓存）

    特点：
    - 分布式共享
    - 容量大
    - 支持持久化
    - 支持 Sentinel/Cluster
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def clear(self, pattern: str = "*") -> int:
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    async def health_check(self) -> bool:
        try:
            return await self.redis.ping()
        except Exception:
            return False


class MultiLevelCache(CacheBackend):
    """
    多级缓存

    L1: 本地内存缓存（微秒级）
    L2: Redis 缓存（毫秒级）

    读取顺序：L1 -> L2 -> 数据源
    写入顺序：L1 + L2（同时）
    """

    def __init__(
        self,
        l1_cache: LocalCache,
        l2_cache: RedisCache,
        l1_ttl: int = 60,
        l2_ttl: int = 3600,
    ):
        self.l1 = l1_cache
        self.l2 = l2_cache
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl

    async def get(self, key: str) -> Optional[Any]:
        # L1
        value = await self.l1.get(key)
        if value is not None:
            return value

        # L2
        value = await self.l2.get(key)
        if value is not None:
            # 回填 L1
            await self.l1.set(key, value, self.l1_ttl)
            return value

        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        # 同时写入 L1 和 L2
        l1_result = await self.l1.set(key, value, min(ttl, self.l1_ttl))
        l2_result = await self.l2.set(key, value, min(ttl, self.l2_ttl))
        return l1_result or l2_result

    async def delete(self, key: str) -> bool:
        l1_result = await self.l1.delete(key)
        l2_result = await self.l2.delete(key)
        return l1_result or l2_result

    async def exists(self, key: str) -> bool:
        return await self.l1.exists(key) or await self.l2.exists(key)

    async def clear(self, pattern: str = "*") -> int:
        l1_count = await self.l1.clear(pattern)
        l2_count = await self.l2.clear(pattern)
        return l1_count + l2_count

    async def health_check(self) -> dict:
        return {
            "l1": await self.l1.health_check(),
            "l2": await self.l2.health_check(),
        }


class CacheManager:
    """缓存管理器 - 统一管理多级缓存"""

    def __init__(self):
        self.settings = get_settings()
        self._cache: Optional[MultiLevelCache] = None
        self._redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """初始化缓存"""
        # 创建 Redis 客户端
        if self.settings.redis.redis_sentinel_urls:
            # 使用 Sentinel
            sentinel = Sentinel(
                self.settings.redis.redis_sentinel_urls_list,
                socket_timeout=self.settings.redis.redis_socket_timeout,
            )
            self._redis_client = sentinel.master_for(
                self.settings.redis.redis_sentinel_master,
                socket_timeout=self.settings.redis.redis_socket_timeout,
            )
        else:
            # 直连
            self._redis_client = redis.from_url(
                self.settings.redis.redis_url,
                max_connections=self.settings.redis.redis_max_connections,
                socket_timeout=self.settings.redis.redis_socket_timeout,
                decode_responses=self.settings.redis.redis_decode_responses,
            )

        # 创建多级缓存
        l1_cache = LocalCache(max_size=1000)
        l2_cache = RedisCache(self._redis_client)

        self._cache = MultiLevelCache(
            l1_cache=l1_cache,
            l2_cache=l2_cache,
            l1_ttl=60,
            l2_ttl=3600,
        )

        logger.info("Cache initialized")

    async def close(self):
        """关闭缓存连接"""
        if self._redis_client:
            await self._redis_client.close()
        logger.info("Cache connections closed")

    @property
    def cache(self) -> MultiLevelCache:
        """获取缓存实例"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")
        return self._cache

    async def get(self, key: str) -> Optional[Any]:
        return await self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        return await self.cache.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        return await self.cache.delete(key)

    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: int = 3600,
    ) -> Any:
        """获取缓存，不存在则通过工厂函数创建"""
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory()
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        """使匹配模式的缓存失效"""
        return await self.cache.clear(pattern)

    async def health_check(self) -> dict:
        """健康检查"""
        return await self.cache.health_check()


# 全局缓存管理器实例
cache_manager = CacheManager()


async def init_cache():
    """初始化缓存"""
    await cache_manager.initialize()


async def close_cache():
    """关闭缓存"""
    await cache_manager.close()


def cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    # 如果键太长，使用哈希
    if len(key_string) > 200:
        return hashlib.md5(key_string.encode()).hexdigest()

    return key_string


def cached(
    prefix: str,
    ttl: int = 3600,
    key_builder=None,
):
    """
    缓存装饰器

    用法：
    @cached("article", ttl=3600)
    async def get_article(article_id: str):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = cache_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_value = await cache_manager.get(key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 写入缓存
            if result is not None:
                await cache_manager.set(key, result, ttl)

            return result
        return wrapper
    return decorator
