"""
APScheduler 调度器：驱动内容采集与摘要任务。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select, update

from core.database import db_manager
from repositories.sqlalchemy.article import ArticleRepository, SourceRepository, EventRepository
from services.article import enqueue_generate_summary_task
from services.content_ingestion import ContentIngestionService
from models.article import Article, Source
from models.subscription import UserFeed

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """内容采集调度器"""
    RSS_FETCH_BASE_INTERVAL_MINUTES = 5
    HIGH_HEAT_INTERVAL_MINUTES = 5
    MEDIUM_HEAT_INTERVAL_MINUTES = 15
    NORMAL_HEAT_INTERVAL_MINUTES = 30
    LOW_HEAT_INTERVAL_MINUTES = 120
    IDLE_HEAT_INTERVAL_MINUTES = 360

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._scheduler and self._scheduler.running:
                return

            scheduler = AsyncIOScheduler(timezone="UTC")
            scheduler.add_job(
                self._run_rss_ingestion,
                "interval",
                minutes=self.RSS_FETCH_BASE_INTERVAL_MINUTES,
                id="rss_ingestion",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            scheduler.add_job(
                self._run_summary_generation,
                "interval",
                minutes=15,
                id="summary_generation",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            scheduler.add_job(
                self._run_source_health_check,
                "interval",
                hours=1,
                id="source_health_check",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            scheduler.add_job(
                self._run_heat_score_update,
                "interval",
                hours=1,
                id="source_heat_update",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            scheduler.add_job(
                self._run_hot_topics_crawl,
                "interval",
                minutes=20,
                id="hot_topics_crawl",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            scheduler.add_job(
                self._run_analytics_retention,
                "cron",
                hour=3,
                minute=15,
                id="analytics_retention",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )
            from core.config import get_settings

            briefing_hour = get_settings().firebase.daily_briefing_hour_utc
            scheduler.add_job(
                self._run_daily_briefing,
                "cron",
                hour=briefing_hour,
                minute=0,
                id="daily_briefing",
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )

            scheduler.start()
            self._scheduler = scheduler
            logger.info("Ingestion scheduler started")

    async def stop(self):
        async with self._lock:
            if not self._scheduler:
                return
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Ingestion scheduler stopped")

    async def health_check(self) -> bool:
        return bool(self._scheduler and self._scheduler.running)

    async def _run_rss_ingestion(self):
        try:
            async with db_manager.get_write_session() as session:
                source_repo = SourceRepository(session)
                article_repo = ArticleRepository(session)
                event_repo = EventRepository(session)
                service = ContentIngestionService(
                    source_repo=source_repo,
                    article_repo=article_repo,
                    event_repo=event_repo,
                )
                all_sources = await source_repo.get_active_sources()
                now = datetime.utcnow()
                due_sources = [
                    source
                    for source in all_sources
                    if source.source_type == "rss"
                    and source.feed_url
                    and self._is_source_due(source, now)
                ]
                if not due_sources:
                    logger.info("Scheduled RSS ingestion skipped: no due sources")
                    return

                semaphore = asyncio.Semaphore(ContentIngestionService.MAX_CONCURRENT_FETCHES)

                async def _run_one(source: Source):
                    async with semaphore:
                        return await service.fetch_feed(str(source.id))

                results = await asyncio.gather(
                    *(_run_one(source) for source in due_sources),
                    return_exceptions=True,
                )

                inserted_count = 0
                failed_sources = 0
                for result in results:
                    if isinstance(result, Exception):
                        failed_sources += 1
                        continue
                    inserted_count += len(result)

                result = {
                    "due_sources": len(due_sources),
                    "failed_sources": failed_sources,
                    "inserted_articles": inserted_count,
                }
                logger.info("Scheduled RSS ingestion completed: %s", result)
        except Exception:
            logger.exception("Scheduled RSS ingestion failed")

    async def _run_summary_generation(self):
        try:
            async with db_manager.get_write_session() as session:
                from repositories.sqlalchemy.cost import CostRepository
                from core.config import get_settings
                from services.cost import CostService

                article_repo = ArticleRepository(session)
                settings = get_settings()
                cost_service = CostService(
                    repo=CostRepository(session),
                    daily_budget_usd=settings.ai.ai_daily_budget_usd,
                    monthly_budget_usd=settings.ai.ai_monthly_budget_usd,
                )
                degradation = await cost_service.get_degradation_level()
                if degradation == "paused":
                    logger.info("Scheduled summary generation skipped: budget paused")
                    return

                batch_limit = 200
                if degradation == "degraded":
                    batch_limit = 50

                pending_articles = await article_repo.get_unsummarized(limit=batch_limit)
                for article in pending_articles:
                    await enqueue_generate_summary_task(str(article.id))
                logger.info(
                    "Scheduled summary generation enqueued tasks=%d degradation=%s",
                    len(pending_articles),
                    degradation,
                )
        except Exception:
            logger.exception("Scheduled summary generation failed")

    async def _run_hot_topics_crawl(self):
        try:
            async with db_manager.get_write_session() as session:
                source_repo = SourceRepository(session)
                article_repo = ArticleRepository(session)
                event_repo = EventRepository(session)
                service = ContentIngestionService(
                    source_repo=source_repo,
                    article_repo=article_repo,
                    event_repo=event_repo,
                )
                results = await service.crawl_hot_topics()
                inserted = sum(item.get("inserted_articles", 0) for item in results)
                logger.info(
                    "Scheduled hot topics crawl completed platforms=%d inserted=%d",
                    len(results),
                    inserted,
                )
        except Exception:
            logger.exception("Scheduled hot topics crawl failed")

    async def _run_source_health_check(self):
        try:
            async with db_manager.get_write_session() as session:
                stmt = (
                    update(Source)
                    .where(
                        Source.error_count >= 5,
                        Source.is_active == True,
                        Source.is_deleted == False,
                    )
                    .values(is_active=False)
                )
                result = await session.execute(stmt)
                logger.info(
                    "Scheduled source health check completed deactivated=%d",
                    result.rowcount or 0,
                )
        except Exception:
            logger.exception("Scheduled source health check failed")

    async def _run_heat_score_update(self):
        try:
            async with db_manager.get_write_session() as session:
                source_rows = await session.execute(
                    select(Source.id).where(
                        Source.is_deleted == False,
                        Source.is_active == True,
                        Source.source_type == "rss",
                    )
                )
                source_ids = source_rows.scalars().all()
                if not source_ids:
                    return

                since = datetime.utcnow() - timedelta(hours=24)
                count_rows = await session.execute(
                    select(Article.source_id, func.count(Article.id))
                    .where(
                        Article.is_deleted == False,
                        Article.created_at >= since,
                        Article.source_id.in_(source_ids),
                    )
                    .group_by(Article.source_id)
                )
                counts = {source_id: int(count) for source_id, count in count_rows.all()}

                subscription_rows = await session.execute(
                    select(UserFeed.source_id, func.count(UserFeed.id))
                    .where(
                        UserFeed.is_deleted == False,
                        UserFeed.is_active == True,
                        UserFeed.source_id.in_(source_ids),
                    )
                    .group_by(UserFeed.source_id)
                )
                subscribers = {
                    source_id: int(count)
                    for source_id, count in subscription_rows.all()
                    if source_id is not None
                }

                for source_id in source_ids:
                    article_count = counts.get(source_id, 0)
                    subscriber_count = subscribers.get(source_id, 0)
                    heat_score = self._calculate_heat_score(
                        article_count=article_count,
                        subscriber_count=subscriber_count,
                    )
                    fetch_interval_minutes = self._map_fetch_interval_minutes(heat_score)
                    await session.execute(
                        update(Source)
                        .where(Source.id == source_id)
                        .values(
                            heat_score=heat_score,
                            fetch_interval_minutes=fetch_interval_minutes,
                        )
                    )
                logger.info("Scheduled heat score update completed sources=%d", len(source_ids))
        except Exception:
            logger.exception("Scheduled heat score update failed")

    @classmethod
    def _is_source_due(cls, source: Source, current_time: datetime) -> bool:
        if source.last_fetched_at is None:
            return True
        interval_minutes = int(source.fetch_interval_minutes or cls.NORMAL_HEAT_INTERVAL_MINUTES)
        due_time = source.last_fetched_at + timedelta(minutes=max(interval_minutes, 1))
        return current_time >= due_time

    @staticmethod
    def _calculate_heat_score(article_count: int, subscriber_count: int) -> float:
        return float(article_count) * 0.6 + float(subscriber_count) * 0.4

    @classmethod
    def _map_fetch_interval_minutes(cls, heat_score: float) -> int:
        if heat_score >= 50:
            return cls.HIGH_HEAT_INTERVAL_MINUTES
        if heat_score >= 20:
            return cls.MEDIUM_HEAT_INTERVAL_MINUTES
        if heat_score >= 5:
            return cls.NORMAL_HEAT_INTERVAL_MINUTES
        if heat_score >= 1:
            return cls.LOW_HEAT_INTERVAL_MINUTES
        return cls.IDLE_HEAT_INTERVAL_MINUTES

    async def _run_analytics_retention(self):
        try:
            from core.config import get_settings
            from repositories.sqlalchemy.analytics import AnalyticsRepository
            from services.analytics import AnalyticsService

            settings = get_settings()
            retention_days = settings.analytics.retention_days
            async with db_manager.get_write_session() as session:
                service = AnalyticsService(AnalyticsRepository(session))
                deleted = await service.purge_old_events(retention_days=retention_days)
            logger.info(
                "Analytics retention completed",
                extra={"deleted_events": deleted, "retention_days": retention_days},
            )
        except Exception:
            logger.exception("Scheduled analytics retention failed")

    async def _run_daily_briefing(self):
        try:
            from services.daily_briefing import run_daily_briefing_batch

            result = await run_daily_briefing_batch()
            logger.info("Scheduled daily briefing completed: %s", result)
        except Exception:
            logger.exception("Scheduled daily briefing failed")


scheduler_manager = IngestionScheduler()

