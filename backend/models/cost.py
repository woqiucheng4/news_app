"""
成本监控模型
"""

from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Date, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import BaseModel


class APIUsageLog(BaseModel):
    """API 使用日志"""
    __tablename__ = "api_usage_logs"

    # 请求信息
    model = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(100), nullable=True)
    request_type = Column(String(50), nullable=True, index=True)  # summary, analysis, classification

    # Token 使用
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # 成本
    cost_usd = Column(Float, nullable=False)

    # 上下文
    article_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # 缓存信息
    cache_hit = Column(Boolean, default=False, nullable=False)
    prompt_cached = Column(Boolean, default=False, nullable=False)

    # 性能
    response_time_ms = Column(Integer, nullable=True)

    # 错误信息
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)


class DailyCostSummary(BaseModel):
    """每日成本汇总"""
    __tablename__ = "daily_cost_summary"

    date = Column(Date, nullable=False, unique=True, index=True)

    # 调用量
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    cached_requests = Column(Integer, default=0, nullable=False)

    # Token 使用
    total_input_tokens = Column(Integer, default=0, nullable=False)
    total_output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)

    # 成本
    total_cost_usd = Column(Float, default=0, nullable=False)

    # 按模型分
    cost_by_model = Column(JSONB, default={}, nullable=False)

    # 按类型分
    cost_by_type = Column(JSONB, default={}, nullable=False)

    # 去重统计
    articles_processed = Column(Integer, default=0, nullable=False)
    duplicates_detected = Column(Integer, default=0, nullable=False)
    dedup_rate = Column(Float, default=0, nullable=False)


class BudgetConfig(BaseModel):
    """预算配置"""
    __tablename__ = "budget_config"

    budget_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    amount_usd = Column(Float, nullable=False)

    # 告警阈值
    warning_threshold = Column(Float, default=0.80, nullable=False)
    critical_threshold = Column(Float, default=0.95, nullable=False)

    # 熔断阈值
    shutdown_at_threshold = Column(Float, default=1.00, nullable=False)

    # 降级策略
    degradation_strategy = Column(JSONB, default={}, nullable=False)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)


class CostAlert(BaseModel):
    """成本告警"""
    __tablename__ = "cost_alerts"

    level = Column(String(20), nullable=False)  # warning, critical, shutdown
    budget_type = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)

    # 状态
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
