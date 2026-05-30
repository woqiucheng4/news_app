from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.article import ArticleService
from services.content_ingestion import ContentIngestionService
from services.deduplication import DeduplicationService


@dataclass
class FakeSource:
    id: object
    source_type: str
    feed_url: Optional[str]
    category: str = "tech"
    name: str = "Tech Feed"


class FakeSourceRepo:
    def __init__(self, source: FakeSource):
        self.source = source
        self.status_updates: list[dict] = []

    async def get_by_id(self, source_id: str):
        return self.source if str(self.source.id) == source_id else None

    async def get_active_sources(self):
        return [self.source]

    async def update_fetch_status(self, source_id: str, success: bool, error: str = None):
        self.status_updates.append(
            {"source_id": source_id, "success": success, "error": error}
        )
        return True


class FakeArticleRepo:
    def __init__(self):
        self.items: dict[str, SimpleNamespace] = {}
        self.by_url_hash: dict[str, SimpleNamespace] = {}
        self.session = None

    async def create(self, data: dict):
        article_id = uuid4()
        item = SimpleNamespace(
            id=article_id,
            title=data["title"],
            url=data["url"],
            content=data.get("content"),
            excerpt=data.get("excerpt"),
            source=SimpleNamespace(id=data["source_id"], name="Tech Feed"),
            category=data.get("category"),
            tags=data.get("tags", []),
            summary=None,
            summary_model=None,
            summary_generated_at=None,
            relevance_score=None,
            is_summary_generated=False,
            url_hash=data["url_hash"],
            author=data.get("author"),
            published_at=data.get("published_at"),
            created_at=data.get("published_at") or __import__("datetime").datetime.utcnow(),
            view_count=0,
            bookmark_count=0,
            event_id=data.get("event_id"),
            content_hash=data.get("content_hash"),
            simhash=data.get("simhash"),
            is_deleted=False,
        )
        self.items[str(article_id)] = item
        self.by_url_hash[data["url_hash"]] = item
        return item

    async def get_by_id(self, article_id: str):
        return self.items.get(str(article_id))

    async def get_by_url_hash(self, url_hash: str):
        return self.by_url_hash.get(url_hash)

    async def get_recent(self, category: str = None, limit: int = 20):
        items = list(self.items.values())
        if category:
            items = [item for item in items if item.category == category]
        return items[:limit]

    async def update_summary(self, id: str, summary: str, model: str, relevance_score: Optional[float] = None):
        item = self.items.get(str(id))
        if not item:
            return False
        item.summary = summary
        item.summary_model = model
        item.relevance_score = relevance_score
        item.is_summary_generated = True
        return True

    async def update(self, id: str, data: dict):
        item = self.items.get(str(id))
        if not item:
            return None
        for key, value in data.items():
            setattr(item, key, value)
        return item


@pytest.mark.asyncio
async def test_rss_to_dedup_to_storage_to_summary(monkeypatch, fake_ai_response):
    source = FakeSource(
        id=uuid4(),
        source_type="rss",
        feed_url="https://example.com/feed.xml",
    )
    source_repo = FakeSourceRepo(source)
    article_repo = FakeArticleRepo()
    dedup_service = DeduplicationService(article_repo)
    ingestion = ContentIngestionService(
        source_repo=source_repo,
        article_repo=article_repo,
        dedup_service=dedup_service,
    )

    parsed_feed = SimpleNamespace(
        entries=[
            {
                "title": "AI model release update",
                "link": "https://example.com/posts/1?utm_source=rss",
                "summary": "New model release details and benchmark results.",
                "author": "editor",
                "published": "Thu, 23 May 2024 10:00:00 GMT",
            }
        ]
    )
    enqueued_ids: list[str] = []

    async def fake_enqueue(article_id: str):
        enqueued_ids.append(article_id)
        return "task-id"

    async def fake_cache_get(_key: str):
        return None

    async def fake_cache_set(_key: str, _value: dict, ttl: int):
        return True

    async def fake_cache_delete(_key: str):
        return True

    async def fake_ai_generate(**_kwargs):
        return fake_ai_response

    monkeypatch.setattr("services.content_ingestion.feedparser.parse", lambda _url: parsed_feed)
    monkeypatch.setattr("services.content_ingestion.enqueue_generate_summary_task", fake_enqueue)
    monkeypatch.setattr("services.article.cache_manager.get", fake_cache_get)
    monkeypatch.setattr("services.article.cache_manager.set", fake_cache_set)
    monkeypatch.setattr("services.article.cache_manager.delete", fake_cache_delete)
    monkeypatch.setattr("services.article.ai_manager.generate", fake_ai_generate)

    inserted = await ingestion.fetch_feed(str(source.id))
    assert len(inserted) == 1
    assert enqueued_ids and enqueued_ids[0] == inserted[0]["id"]

    article_service = ArticleService(article_repo)
    summary = await article_service.generate_summary(inserted[0]["id"])
    assert summary == "integration summary"

    saved = await article_repo.get_by_id(inserted[0]["id"])
    assert saved is not None
    assert saved.is_summary_generated is True
    assert saved.relevance_score == 88.0
