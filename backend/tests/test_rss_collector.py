from dataclasses import dataclass
from types import SimpleNamespace
from typing import Optional, Set
from uuid import uuid4
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.content_ingestion import ContentIngestionService


@dataclass
class FakeSource:
    id: object
    source_type: str
    feed_url: Optional[str]
    category: str = "tech"
    name: str = "source"


class FakeSourceRepo:
    def __init__(self, sources: list[FakeSource]):
        self.sources = {str(source.id): source for source in sources}
        self.status_updates: list[dict] = []

    async def get_by_id(self, source_id: str):
        return self.sources.get(source_id)

    async def get_active_sources(self):
        return list(self.sources.values())

    async def update_fetch_status(self, source_id: str, success: bool, error: str = None):
        self.status_updates.append(
            {"source_id": source_id, "success": success, "error": error}
        )
        return True


class FakeArticleRepo:
    def __init__(self):
        self.created: list[dict] = []

    async def create(self, data: dict):
        created_id = uuid4()
        self.created.append({"id": created_id, **data})
        return SimpleNamespace(id=created_id)

    async def get_recent(self, category: str = None, limit: int = 20):
        return []

    async def get_by_url_hash(self, url_hash: str):
        return None


class FakeDedupService:
    def __init__(self, duplicate_urls: Optional[Set[str]] = None):
        self.duplicate_urls = duplicate_urls or set()

    async def check_duplicate(self, article_data: dict) -> dict:
        is_dup = article_data["url"] in self.duplicate_urls
        return {
            "is_duplicate": is_dup,
            "duplicate_of": "existing-id" if is_dup else None,
            "event_id": None,
            "similarity": 1.0 if is_dup else 0.0,
            "layer": "url_hash" if is_dup else None,
        }

    def compute_simhash(self, text: str) -> str:
        # Stable fake simhash for tests.
        return "0" * 16 if text else ""


@pytest.mark.asyncio
async def test_fetch_feed_inserts_only_non_duplicate_entries(monkeypatch):
    source = FakeSource(
        id=uuid4(),
        source_type="rss",
        feed_url="https://example.com/feed.xml",
    )
    source_repo = FakeSourceRepo([source])
    article_repo = FakeArticleRepo()
    dedup = FakeDedupService(duplicate_urls={"https://example.com/dup"})
    service = ContentIngestionService(source_repo, article_repo, dedup)

    parsed_feed = SimpleNamespace(
        entries=[
            {
                "title": " First Article ",
                "link": "https://example.com/new?utm_source=x",
                "summary": "<p>Hello world</p>",
                "author": "author-a",
                "published": "Thu, 23 May 2024 10:00:00 GMT",
            },
            {
                "title": "Duplicate Article",
                "link": "https://example.com/dup",
                "summary": "dup",
                "author": "author-b",
                "published": "Thu, 23 May 2024 11:00:00 GMT",
            },
        ]
    )
    monkeypatch.setattr(
        "services.content_ingestion.feedparser.parse",
        lambda _: parsed_feed,
    )

    inserted = await service.fetch_feed(str(source.id))

    assert len(inserted) == 1
    assert len(article_repo.created) == 1
    assert article_repo.created[0]["title"] == "First Article"
    assert article_repo.created[0]["url"] == "https://example.com/new"
    assert source_repo.status_updates[-1]["success"] is True


@pytest.mark.asyncio
async def test_fetch_feed_marks_source_failed_on_parse_error(monkeypatch):
    source = FakeSource(
        id=uuid4(),
        source_type="rss",
        feed_url="https://example.com/feed.xml",
    )
    source_repo = FakeSourceRepo([source])
    article_repo = FakeArticleRepo()
    service = ContentIngestionService(source_repo, article_repo, FakeDedupService())

    def _raise(_: str):
        raise RuntimeError("network error")

    monkeypatch.setattr("services.content_ingestion.feedparser.parse", _raise)

    inserted = await service.fetch_feed(str(source.id))

    assert inserted == []
    assert source_repo.status_updates[-1]["success"] is False
    assert "network error" in source_repo.status_updates[-1]["error"]


@pytest.mark.asyncio
async def test_fetch_all_feeds_returns_aggregated_metrics(monkeypatch):
    source_a = FakeSource(id=uuid4(), source_type="rss", feed_url="https://a.com/rss")
    source_b = FakeSource(id=uuid4(), source_type="rss", feed_url="https://b.com/rss")
    source_repo = FakeSourceRepo([source_a, source_b])
    article_repo = FakeArticleRepo()
    service = ContentIngestionService(source_repo, article_repo, FakeDedupService())

    parsed_by_url = {
        source_a.feed_url: SimpleNamespace(
            entries=[
                {
                    "title": "A1",
                    "link": "https://a.com/1",
                    "summary": "content from feed A",
                }
            ]
        ),
        source_b.feed_url: SimpleNamespace(
            entries=[
                {
                    "title": "B1",
                    "link": "https://b.com/1",
                    "summary": "content from feed B",
                }
            ]
        ),
    }
    monkeypatch.setattr(
        "services.content_ingestion.feedparser.parse",
        lambda url: parsed_by_url[url],
    )

    result = await service.fetch_all_feeds()

    assert result["total_sources"] == 2
    assert result["success_sources"] == 2
    assert result["failed_sources"] == 0
    assert result["inserted_articles"] == 2
