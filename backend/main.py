"""
NewsFlow 应用入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from core.config import get_settings
from core.dependencies import services
from api.v1.router import api_router
from api.web import router as web_router
from middleware.rate_limit import RateLimitMiddleware
from tasks.scheduler import scheduler_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting NewsFlow application...")

    # 初始化所有服务
    await services.initialize()
    await scheduler_manager.start()
    logger.info("All services initialized")

    # 添加限流中间件（需要 Redis）
    # app.add_middleware(
    #     RateLimitMiddleware,
    #     redis_client=services.cache._redis_client,
    # )

    yield

    # 关闭所有服务
    await scheduler_manager.stop()
    await services.close()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered information aggregation app",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router)
    app.include_router(web_router, prefix="/web")

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        health = await services.health_check()
        all_healthy = all(
            v if isinstance(v, bool) else all(v.values())
            for v in health.values()
        )
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health,
        }

    # 根端点
    @app.get("/")
    async def root():
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/web/feed")

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
    )
