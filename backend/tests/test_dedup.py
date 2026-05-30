import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.deduplication import DeduplicationService


@dataclass
class FakeArticle:
    id: object
    title: str
    url_hash: str
    content: str = ""
    simhash: Optional[str] = None
    event_id: Optional[object] = None


class FakeArticleRepo:
    def __init__(self, articles: list[FakeArticle]):
        self._articles = articles

    async def get_by_url_hash(self, url_hash: str):
        for article in self._articles:
            if article.url_hash == url_hash:
                return article
        return None

    async def get_recent(self, category: str = None, limit: int = 20):
        return self._articles[:limit]


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


@pytest.mark.asyncio
async def test_check_duplicate_by_url_hash():
    existing = FakeArticle(
        id=uuid4(),
        title="Apple releases new device",
        url_hash=_hash_url("https://news.example.com/item/1"),
    )
    repo = FakeArticleRepo([existing])
    service = DeduplicationService(repo)

    result = await service.check_duplicate(
        {
            "url": "https://news.example.com/item/1?utm_source=twitter",
            "title": "Completely different title",
            "content": "Different content",
        }
    )

    assert result["is_duplicate"] is True
    assert result["layer"] == "url_hash"
    assert result["duplicate_of"] == str(existing.id)


@pytest.mark.asyncio
async def test_check_duplicate_by_title_similarity():
    existing = FakeArticle(
        id=uuid4(),
        title="OpenAI launches GPT model for code generation",
        url_hash=_hash_url("https://news.example.com/item/a"),
        content="Some content",
    )
    repo = FakeArticleRepo([existing])
    service = DeduplicationService(repo, title_similarity_threshold=0.7)

    result = await service.check_duplicate(
        {
            "url": "https://news.example.com/item/b",
                "title": "OpenAI launches GPT model for code generation update",
            "content": "Completely unrelated body text",
        }
    )

    assert result["is_duplicate"] is True
    assert result["layer"] == "title_minhash"
    assert result["duplicate_of"] == str(existing.id)
    assert result["similarity"] >= 0.7


@pytest.mark.asyncio
async def test_check_duplicate_by_content_simhash():
    base_content = (
        "Apple announced new M-series chips for professional laptops "
        "with better battery life and improved graphics performance."
    )
    existing = FakeArticle(
        id=uuid4(),
        title="Tech event highlights",
        url_hash=_hash_url("https://news.example.com/item/x"),
        content=base_content,
    )
    repo = FakeArticleRepo([existing])
    service = DeduplicationService(repo, title_similarity_threshold=0.95, simhash_distance_threshold=3)

    result = await service.check_duplicate(
        {
            "url": "https://news.example.com/item/y",
            "title": "Market wrap",
                "content": base_content,
        }
    )

    assert result["is_duplicate"] is True
    assert result["layer"] == "content_simhash"
    assert result["duplicate_of"] == str(existing.id)


@pytest.mark.asyncio
async def test_check_duplicate_returns_false_for_new_article():
    existing = FakeArticle(
        id=uuid4(),
        title="Global markets rally after policy update",
        url_hash=_hash_url("https://news.example.com/item/m"),
        content="Finance content",
    )
    repo = FakeArticleRepo([existing])
    service = DeduplicationService(repo, title_similarity_threshold=0.9, simhash_distance_threshold=1)

    result = await service.check_duplicate(
        {
            "url": "https://news.example.com/item/n",
            "title": "NASA discovers a new exoplanet",
            "content": "Space telescope captured signals from a distant world.",
        }
    )

    assert result == {
        "is_duplicate": False,
        "duplicate_of": None,
        "event_id": None,
        "similarity": 0.0,
        "layer": None,
    }
