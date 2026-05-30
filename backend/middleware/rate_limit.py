"""
限流中间件
"""

from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(
        self,
        app,
        redis_client: redis.Redis,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        super().__init__(app)
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window

        # 不同端点的限流配置
        self.endpoint_limits = {
            "/api/v1/articles/search": {"limit": 30, "window": 60},
            "/api/v1/articles/trending": {"limit": 50, "window": 60},
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端标识
        client_id = self._get_client_id(request)

        # 获取端点限流配置
        path = request.url.path
        config = self.endpoint_limits.get(path, {
            "limit": self.default_limit,
            "window": self.default_window,
        })

        # 检查限流
        key = f"rate_limit:{path}:{client_id}"
        allowed = await self._check_rate_limit(
            key,
            config["limit"],
            config["window"],
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
            )

        # 执行请求
        response = await call_next(request)

        # 添加限流头
        remaining = await self._get_remaining(key, config["limit"])
        response.headers["X-RateLimit-Limit"] = str(config["limit"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用认证用户 ID
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # 否则使用 IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host

        return f"ip:{ip}"

    async def _check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> bool:
        """检查是否超过限流"""
        now = time.time()
        window_start = now - window

        # 使用滑动窗口
        pipe = self.redis.pipeline()

        # 移除窗口外的记录
        pipe.zremrangebyscore(key, 0, window_start)

        # 统计窗口内的请求数
        pipe.zcard(key)

        # 添加当前请求
        pipe.zadd(key, {str(now): now})

        # 设置过期时间
        pipe.expire(key, window)

        results = await pipe.execute()

        current_count = results[1]

        if current_count >= limit:
            # 移除刚添加的记录
            await self.redis.zrem(key, str(now))
            return False

        return True

    async def _get_remaining(self, key: str, limit: int) -> int:
        """获取剩余请求数"""
        count = await self.redis.zcard(key)
        return max(0, limit - count)
