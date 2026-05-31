"""
文章服务实现
"""

from typing import Optional, List, Dict, Any, Union
import json
import logging
import time
from uuid import UUID

from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from .interfaces import IArticleService
from repositories.sqlalchemy.article import ArticleRepository, EventRepository
from repositories.sqlalchemy.cost import CostRepository
from core.cache import cache_manager
from core.ai import ai_manager, AIModel, SUMMARY_SYSTEM_PROMPT
from core.config import get_settings
from core.database import db_manager
from core.tasks import task, enqueue_task, TaskConfig
from services.cost import CostService

logger = logging.getLogger(__name__)

RELATED_ARTICLE_LIMIT = 5


class ArticleService(IArticleService):
    """文章服务"""

    SUMMARY_CACHE_PREFIX = "summary"
    SUMMARY_CACHE_TTL = 86400 * 7  # 7 days

    def __init__(self, article_repo: ArticleRepository):
        self.repo = article_repo

    async def get_article(self, id: str) -> Optional[Dict]:
        """获取文章详情"""
        # 尝试从缓存获取
        cache_key = f"article:{id}"
        cached = await cache_manager.get(cache_key)
        if cached:
            # 异步增加浏览次数
            await self._increment_view_count(id)
            return await self._hydrate_cached_article(cached, id)

        # 从数据库获取
        article = await self.repo.get_by_id(id)
        if not article:
            return None

        # 转换为字典
        result = self._to_dict(article)
        result.update(await self._get_related_article_bundle(article))

        # 缓存
        await cache_manager.set(cache_key, result, ttl=3600)

        # 增加浏览次数
        await self._increment_view_count(id)

        return result

    async def get_related_articles(
        self,
        article_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[Dict]:
        """Paginate related articles for the same deduplication event."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None

        event_id = getattr(article, "event_id", None)
        if not event_id:
            return {
                "page": page,
                "page_size": page_size,
                "articles": [],
                "has_more": False,
                "total": 0,
            }

        related = await self.repo.get_by_event_id(str(event_id))
        filtered = [
            item for item in related if str(item.id) != str(article.id)
        ]
        total = len(filtered)
        offset = (page - 1) * page_size
        page_items = filtered[offset : offset + page_size]

        return {
            "page": page,
            "page_size": page_size,
            "articles": [self._to_dict(item) for item in page_items],
            "has_more": offset + len(page_items) < total,
            "total": total,
        }

    async def get_feed(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        topic_id: Optional[str] = None,
        topic_name: Optional[str] = None,
    ) -> Dict:
        """获取用户信息流"""
        if topic_id:
            cache_key = f"feed:{user_id}:topic:{topic_id}:page:{page}"
        else:
            cache_key = f"feed:{user_id}:page:{page}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        offset = (page - 1) * page_size
        if topic_id and topic_name:
            articles = await self.repo.list_for_topic(
                topic_name,
                limit=page_size,
                offset=offset,
            )
        else:
            articles = await self.repo.list(
                order_by="-published_at",
                limit=page_size,
                offset=offset,
            )

        result = {
            "page": page,
            "page_size": page_size,
            "articles": [self._to_dict(a) for a in articles],
            "has_more": len(articles) == page_size,
        }
        if topic_id:
            result["topic_id"] = topic_id

        await cache_manager.set(cache_key, result, ttl=300)

        return result

    async def search_articles(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索文章"""
        articles = await self.repo.search(query, limit)
        return [self._to_dict(a) for a in articles]

    async def get_trending(self, limit: int = 20) -> List[Dict]:
        """获取热门事件"""
        cache_key = f"trending:events:{limit}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        event_repo = EventRepository(self.repo.session)
        events = await event_repo.get_trending(limit=limit)
        result = [self._event_to_dict(event) for event in events]

        await cache_manager.set(cache_key, result, ttl=600)
        return result

    async def generate_summary(self, article_id: str) -> Optional[str]:
        """生成摘要"""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None

        if article.is_summary_generated:
            return article.summary

        # 检查是否有内容
        if not article.content:
            logger.warning(f"Article {article_id} has no content")
            return None

        cache_key = f"{self.SUMMARY_CACHE_PREFIX}:{article.url_hash}"
        cached_summary = await cache_manager.get(cache_key)
        if cached_summary and cached_summary.get("summary"):
            summary_text = cached_summary["summary"]
            cached_model = cached_summary.get("model", "cache")
            relevance_score = cached_summary.get("relevance_score")
            await self.repo.update_summary(
                article_id,
                summary_text,
                cached_model,
                relevance_score=relevance_score,
            )
            await cache_manager.delete(f"article:{article_id}")
            await self._record_usage(
                article_id=article.id,
                model=cached_model,
                request_type="summary",
                cache_hit=True,
                prompt_cached=True,
            )
            return summary_text

        started_at = time.perf_counter()
        retry_count = 0
        try:
            response, retry_count = await self._generate_with_retry(
                article.title,
                article.content,
            )
            summary_text, relevance_score = self._parse_summary_response(response.content)

            await self.repo.update_summary(
                article_id,
                summary_text,
                response.model,
                relevance_score=relevance_score,
            )
            await cache_manager.set(
                cache_key,
                {
                    "summary": summary_text,
                    "model": response.model,
                    "relevance_score": relevance_score,
                },
                ttl=self.SUMMARY_CACHE_TTL,
            )

            await cache_manager.delete(f"article:{article_id}")
            await self._record_usage(
                article_id=article.id,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                cost_usd=response.cost_usd,
                response_time_ms=int((time.perf_counter() - started_at) * 1000),
                retry_count=retry_count,
                request_type="summary",
                cache_hit=False,
                prompt_cached=False,
            )

            return summary_text

        except Exception as e:
            logger.error(f"Failed to generate summary for {article_id}: {e}")
            await self._record_usage(
                article_id=article.id,
                model=AIModel.GPT_4O_MINI.value,
                response_time_ms=int((time.perf_counter() - started_at) * 1000),
                retry_count=retry_count,
                request_type="summary",
                cache_hit=False,
                prompt_cached=False,
                error_code=e.__class__.__name__,
                error_message=str(e),
            )
            return None

    async def _generate_with_retry(self, title: str, content: str):
        last_attempt = 0
        response = None
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception(self._is_retryable_ai_exception),
            reraise=True,
        ):
            with attempt:
                last_attempt = attempt.retry_state.attempt_number
                response = await ai_manager.generate(
                    prompt=(
                        "请基于以下内容输出 JSON，且必须仅包含 JSON："
                        '\n{"summary":"2-3句、50-100字摘要","relevance_score":0-100}'
                        f"\n\n标题：{title}\n\n正文：{content}"
                    ),
                    system_prompt=SUMMARY_SYSTEM_PROMPT,
                    model=AIModel.GPT_4O_MINI,
                    max_tokens=220,
                    use_cache=False,
                )
        return response, max(last_attempt - 1, 0)

    @staticmethod
    def _is_retryable_ai_exception(exc: Exception) -> bool:
        message = str(exc).lower()
        name = exc.__class__.__name__.lower()
        retry_hints = (
            "timeout",
            "timed out",
            "rate limit",
            "too many requests",
            "429",
            "temporarily",
            "connection",
            "apierror",
            "service unavailable",
        )
        return any(hint in message or hint in name for hint in retry_hints)

    @staticmethod
    def _parse_summary_response(content: str) -> tuple[str, Optional[float]]:
        if not content:
            return "", None
        summary_text = content.strip()
        relevance_score: Optional[float] = None
        try:
            payload = json.loads(summary_text)
            if isinstance(payload, dict):
                parsed_summary = str(payload.get("summary", "")).strip()
                if parsed_summary:
                    summary_text = parsed_summary
                raw_score = payload.get("relevance_score")
                if raw_score is not None:
                    score_value = float(raw_score)
                    relevance_score = max(0.0, min(100.0, score_value))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return summary_text, relevance_score

    async def _record_usage(
        self,
        article_id: Union[UUID, str],
        model: str,
        request_type: str,
        cache_hit: bool,
        prompt_cached: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        cost_usd: float = 0.0,
        response_time_ms: Optional[int] = None,
        retry_count: int = 0,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        session = getattr(self.repo, "session", None)
        if session is None:
            return

        settings = get_settings()
        cost_service = CostService(
            repo=CostRepository(session),
            daily_budget_usd=settings.ai.ai_daily_budget_usd,
            monthly_budget_usd=settings.ai.ai_monthly_budget_usd,
        )
        await cost_service.record_usage(
            {
                "model": model,
                "endpoint": "generate_summary",
                "request_type": request_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd,
                "article_id": article_id,
                "cache_hit": cache_hit,
                "prompt_cached": prompt_cached,
                "response_time_ms": response_time_ms,
                "error_code": error_code,
                "error_message": error_message,
                "retry_count": retry_count,
            }
        )

    async def _increment_view_count(self, article_id: str):
        """异步增加浏览次数"""
        try:
            await self.repo.update(article_id, {"view_count": {"increment": 1}})
        except Exception:
            pass  # 非关键操作，忽略错误

    async def _hydrate_cached_article(self, cached: Dict, article_id: str) -> Dict:
        """Backfill fields added after older cache entries were written."""
        updated = dict(cached)
        source = updated.get("source")
        needs_related = "related_articles" not in updated
        needs_related_total = "related_articles_total" not in updated
        needs_source_url = isinstance(source, dict) and not source.get("url")

        if not needs_related and not needs_related_total and not needs_source_url:
            updated.setdefault("related_articles", [])
            updated.setdefault("related_articles_total", len(updated["related_articles"]))
            return updated

        article = await self.repo.get_by_id(article_id)
        if not article:
            updated.setdefault("related_articles", [])
            return updated

        if needs_related or needs_related_total:
            bundle = await self._get_related_article_bundle(article)
            updated.update(bundle)

        if needs_source_url and article.source:
            patched_source = dict(source) if isinstance(source, dict) else {}
            patched_source["url"] = article.source.url
            updated["source"] = patched_source

        await cache_manager.set(f"article:{article_id}", updated, ttl=3600)
        return updated

    async def _get_related_article_bundle(self, article) -> Dict:
        """Fetch preview related articles and total count for the same event."""
        event_id = getattr(article, "event_id", None)
        if not event_id:
            return {"related_articles": [], "related_articles_total": 0}

        related = await self.repo.get_by_event_id(str(event_id))
        filtered = [
            item for item in related if str(item.id) != str(article.id)
        ]
        return {
            "related_articles": [
                self._to_dict(item) for item in filtered[:RELATED_ARTICLE_LIMIT]
            ],
            "related_articles_total": len(filtered),
        }

    def _to_dict(self, article) -> Dict:
        """转换为字典"""
        return {
            "id": str(article.id),
            "title": article.title,
            "url": article.url,
            "excerpt": article.excerpt,
            "summary": article.summary,
            "author": article.author,
            "source": {
                "id": str(article.source.id) if article.source else None,
                "name": article.source.name if article.source else None,
                "url": article.source.url if article.source else None,
            },
            "category": article.category,
            "tags": article.tags or [],
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "created_at": article.created_at.isoformat(),
            "view_count": article.view_count,
            "bookmark_count": article.bookmark_count,
        }

    @staticmethod
    def _event_to_dict(event) -> Dict:
        return {
            "id": str(event.id),
            "title": event.title,
            "summary": event.summary,
            "category": event.category,
            "article_count": event.article_count,
            "source_count": event.source_count,
            "last_updated_at": event.last_updated_at.isoformat() if event.last_updated_at else None,
        }


@task(name="generate_article_summary", max_retries=3, retry_delay=15, timeout=180)
async def generate_article_summary_task(article_id: str) -> Dict[str, Any]:
    """
    后台摘要任务：异步生成摘要，不阻塞采集入库流程。
    """
    async with db_manager.get_write_session() as session:
        repo = ArticleRepository(session)
        service = ArticleService(repo)
        summary = await service.generate_summary(article_id)
        if summary is not None:
            from services.notification import push_article_update

            await push_article_update(article_id)
        return {"article_id": article_id, "generated": summary is not None}


async def enqueue_generate_summary_task(article_id: str) -> Optional[str]:
    """
    将摘要任务放入队列，失败不抛出，避免影响主流程。
    """
    try:
        return await enqueue_task(
            task_name="generate_article_summary",
            args=(article_id,),
            config=TaskConfig(
                max_retries=3,
                retry_delay=15,
                timeout=180,
            ),
        )
    except Exception as exc:
        logger.warning(f"Failed to enqueue summary task for {article_id}: {exc}")
        return None
