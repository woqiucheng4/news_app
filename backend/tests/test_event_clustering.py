from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.content_ingestion import ContentIngestionService


@dataclass
class FakeSource:
    id: object
    source_type: str
    feed_url: Optional[str]
    category: str = "news"
    name: str = "source"


@dataclass
class FakeArticle:
    id: object
    title: str
    url_hash: str
    content_hash: Optional[str] = None
    simhash: Optional[str] = None
    category: Optional[str] = "news"
    event_id: Optional[object] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class FakeSourceRepo:
    async def get_by_id(self, _source_id: str):
        return None

    async def get_active_sources(self):
        return []

    async def update_fetch_status(self, _source_id: str, success: bool, error: str = None):
        return True


class FakeArticleRepo:
    def __init__(self, existing: Optional[list[FakeArticle]] = None):
        self._existing = {str(item.id): item for item in (existing or [])}
        self.created_payloads: list[dict] = []
        self.updated_payloads: list[dict] = []

    async def create(self, data: dict):
        created_id = uuid4()
        created = SimpleNamespace(
            id=created_id,
            title=data["title"],
            category=data.get("category"),
            created_at=datetime.utcnow(),
        )
        self.created_payloads.append(data)
        self._existing[str(created_id)] = FakeArticle(
            id=created_id,
            title=data["title"],
            url_hash=data["url_hash"],
            content_hash=data.get("content_hash"),
            simhash=data.get("simhash"),
            category=data.get("category"),
            event_id=data.get("event_id"),
        )
        return created

    async def get_by_id(self, article_id: str):
        return self._existing.get(str(article_id))

    async def update(self, article_id: str, data: dict):
        self.updated_payloads.append({"id": str(article_id), "data": data})
        article = self._existing.get(str(article_id))
        if article and "event_id" in data:
            article.event_id = data["event_id"]
        return article


class FakeEventRepo:
    def __init__(self):
        self.created_events: list[SimpleNamespace] = []
        self.updated_counts: list[dict] = []
        self.synced_source_counts: list[str] = []

    async def get_by_article_hash(self, content_hash: str):
        for event in self.created_events:
            if event.representative_hash == content_hash:
                return event
        return None

    async def create(self, data: dict):
        event = SimpleNamespace(id=uuid4(), **data)
        self.created_events.append(event)
        return event

    async def update_article_count(self, event_id: str, increment: int = 1):
        self.updated_counts.append({"id": str(event_id), "increment": increment})
        return True

    async def sync_source_count(self, event_id: str):
        self.synced_source_counts.append(str(event_id))
        return True


class FakeDedupService:
    def __init__(self, result: dict):
        self.result = result

    async def check_duplicate(self, article_data: dict) -> dict:
        return self.result

    def compute_simhash(self, text: str) -> str:
        return "0" * 16 if text else ""


@pytest.mark.asyncio
async def test_process_article_skips_exact_url_duplicates():
    article_repo = FakeArticleRepo()
    event_repo = FakeEventRepo()
    dedup = FakeDedupService(
        {
            "is_duplicate": True,
            "duplicate_of": str(uuid4()),
            "event_id": None,
            "similarity": 1.0,
            "layer": "url_hash",
        }
    )
    service = ContentIngestionService(FakeSourceRepo(), article_repo, dedup_service=dedup, event_repo=event_repo)

    result = await service.process_article(
        {
            "title": "t",
            "url": "https://example.com/t",
            "source_id": uuid4(),
            "url_hash": "hash1",
        }
    )

    assert result is None
    assert article_repo.created_payloads == []
    assert event_repo.created_events == []


@pytest.mark.asyncio
async def test_process_article_links_layer2_duplicates_to_event():
    existing_article = FakeArticle(
        id=uuid4(),
        title="Existing title",
        url_hash="existing-hash",
        content_hash="content-hash-1",
        event_id=None,
    )
    article_repo = FakeArticleRepo(existing=[existing_article])
    event_repo = FakeEventRepo()
    dedup = FakeDedupService(
        {
            "is_duplicate": True,
            "duplicate_of": str(existing_article.id),
            "event_id": None,
            "similarity": 0.82,
            "layer": "title_minhash",
        }
    )
    service = ContentIngestionService(FakeSourceRepo(), article_repo, dedup_service=dedup, event_repo=event_repo)

    new_article_id = await service.process_article(
        {
            "title": "Similar title",
            "url": "https://example.com/new",
            "source_id": uuid4(),
            "url_hash": "new-hash",
            "content_hash": "content-hash-1",
            "simhash": "f" * 16,
            "category": "news",
        }
    )

    assert new_article_id is not None
    assert len(event_repo.created_events) == 1
    created_event = event_repo.created_events[0]
    assert str(article_repo.created_payloads[0]["event_id"]) == str(created_event.id)
    assert event_repo.updated_counts and event_repo.updated_counts[0]["increment"] == 1
    assert str(created_event.id) in event_repo.synced_source_counts
    # Existing representative article should be linked to event as well.
    assert any(item["id"] == str(existing_article.id) for item in article_repo.updated_payloads)


@pytest.mark.asyncio
async def test_process_article_creates_new_event_for_fresh_article():
    article_repo = FakeArticleRepo()
    event_repo = FakeEventRepo()
    dedup = FakeDedupService(
        {
            "is_duplicate": False,
            "duplicate_of": None,
            "event_id": None,
            "similarity": 0.0,
            "layer": None,
        }
    )
    service = ContentIngestionService(FakeSourceRepo(), article_repo, dedup_service=dedup, event_repo=event_repo)

    new_article_id = await service.process_article(
        {
            "title": "Brand new topic",
            "url": "https://example.com/topic",
            "source_id": uuid4(),
            "url_hash": "topic-hash",
            "content_hash": "topic-content-hash",
            "simhash": "a" * 16,
            "category": "tech",
        }
    )

    assert new_article_id is not None
    assert len(event_repo.created_events) == 1
    assert article_repo.updated_payloads
    assert article_repo.updated_payloads[0]["data"].get("event_id") == event_repo.created_events[0].id
    assert str(event_repo.created_events[0].id) in event_repo.synced_source_counts
