"""
配置管理模块 - 所有配置外部化，支持环境变量和 .env 文件
"""

from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    # 连接配置
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    db_pool_size: int = Field(default=20, validation_alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, validation_alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, validation_alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, validation_alias="DB_POOL_RECYCLE")

    # 读写分离（可选）
    database_read_urls: Optional[str] = Field(default=None, validation_alias="DATABASE_READ_URLS")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class RedisSettings(BaseSettings):
    """Redis 配置"""

    # 连接配置
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_max_connections: int = Field(default=100, validation_alias="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, validation_alias="REDIS_SOCKET_TIMEOUT")
    redis_decode_responses: bool = Field(default=True, validation_alias="REDIS_DECODE_RESPONSES")

    # Sentinel 配置（可选）
    redis_sentinel_urls: Optional[str] = Field(default=None, validation_alias="REDIS_SENTINEL_URLS")
    redis_sentinel_master: str = Field(default="mymaster", validation_alias="REDIS_SENTINEL_MASTER")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class AISettings(BaseSettings):
    """AI 服务配置"""

    # OpenAI
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=150, validation_alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.3, validation_alias="OPENAI_TEMPERATURE")

    # Claude (可选)
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-haiku-4-5-20251001", validation_alias="ANTHROPIC_MODEL")

    # 并发控制
    ai_max_concurrent: int = Field(default=50, validation_alias="AI_MAX_CONCURRENT")
    ai_requests_per_minute: int = Field(default=500, validation_alias="AI_REQUESTS_PER_MINUTE")

    # 成本控制
    ai_daily_budget_usd: float = Field(default=5.0, validation_alias="AI_DAILY_BUDGET_USD")
    ai_monthly_budget_usd: float = Field(default=100.0, validation_alias="AI_MONTHLY_BUDGET_USD")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class StorageSettings(BaseSettings):
    """存储配置"""

    # 本地存储
    storage_type: str = Field(default="local", validation_alias="STORAGE_TYPE")  # local, s3, gcs
    storage_base_path: str = Field(default="./uploads", validation_alias="STORAGE_BASE_PATH")

    # S3 配置（可选）
    s3_bucket: Optional[str] = Field(default=None, validation_alias="S3_BUCKET")
    s3_region: Optional[str] = Field(default=None, validation_alias="S3_REGION")
    s3_access_key: Optional[str] = Field(default=None, validation_alias="S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = Field(default=None, validation_alias="S3_SECRET_KEY")
    s3_endpoint_url: Optional[str] = Field(default=None, validation_alias="S3_ENDPOINT_URL")

    # CDN 配置（可选）
    cdn_domain: Optional[str] = Field(default=None, validation_alias="CDN_DOMAIN")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class CelerySettings(BaseSettings):
    """Celery 配置"""

    # 使用 Celery 还是简单队列
    use_celery: bool = Field(default=False, validation_alias="USE_CELERY")

    # Celery 配置
    celery_broker_url: str = Field(default="redis://localhost:6379/1", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", validation_alias="CELERY_RESULT_BACKEND")
    celery_worker_concurrency: int = Field(default=4, validation_alias="CELERY_WORKER_CONCURRENCY")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class FirebaseSettings(BaseSettings):
    """Firebase / FCM configuration."""

    credentials_path: Optional[str] = Field(
        default=None,
        validation_alias="FIREBASE_CREDENTIALS_PATH",
    )
    credentials_json: Optional[str] = Field(
        default=None,
        validation_alias="FIREBASE_CREDENTIALS_JSON",
    )
    daily_briefing_hour_utc: int = Field(
        default=8,
        validation_alias="DAILY_BRIEFING_HOUR_UTC",
    )

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class AnalyticsSettings(BaseSettings):
    """Client analytics configuration."""

    retention_days: int = Field(default=90, validation_alias="ANALYTICS_RETENTION_DAYS")
    dashboard_token: Optional[str] = Field(default=None, validation_alias="ANALYTICS_DASHBOARD_TOKEN")
    admin_emails: Optional[str] = Field(default=None, validation_alias="ANALYTICS_ADMIN_EMAILS")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    @property
    def admin_emails_list(self) -> list[str]:
        if not self.admin_emails:
            return []
        return [email.strip().lower() for email in self.admin_emails.split(",") if email.strip()]


class SecuritySettings(BaseSettings):
    """安全配置"""

    # JWT
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    cors_origins: str = Field(default="*", validation_alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class Settings(BaseSettings):
    """主配置类"""

    # 应用配置
    app_name: str = Field(default="NewsFlow", validation_alias="APP_NAME")
    app_version: str = Field(default="1.0.0", validation_alias="APP_VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")  # development, staging, production

    # 服务配置
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    workers: int = Field(default=4, validation_alias="WORKERS")

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    firebase: FirebaseSettings = Field(default_factory=FirebaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_read_urls_list(self) -> list[str]:
        """解析读数据库 URL 列表"""
        if self.database.database_read_urls:
            return [url.strip() for url in self.database.database_read_urls.split(",")]
        return []

    @property
    def redis_sentinel_urls_list(self) -> list[tuple[str, int]]:
        """解析 Redis Sentinel 地址列表"""
        if self.redis.redis_sentinel_urls:
            urls = []
            for url in self.redis.redis_sentinel_urls.split(","):
                host, port = url.strip().split(":")
                urls.append((host, int(port)))
            return urls
        return []

    @property
    def cors_origins_list(self) -> list[str]:
        """解析 CORS 来源列表"""
        if self.security.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.security.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
