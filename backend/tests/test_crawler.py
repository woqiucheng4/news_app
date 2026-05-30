from dataclasses import dataclass
from typing import Optional
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
    category: str = "news"
    name: str = "source"


class FakeSourceRepo:
    def __init__(self):
        self.created_sources: list[object] = []
        self.status_updates: list[dict] = []

    async def get_by_id(self, _source_id: str):
        return None

    async def get_active_sources(self):
        return []

    async def update_fetch_status(self, _source_id: str, success: bool, error: str = None):
        self.status_updates.append({"success": success, "error": error, "source_id": _source_id})
        return True

    async def list(self, filters: dict = None, order_by: str = None, limit: int = 100, offset: int = 0):
        return self.created_sources

    async def create(self, data: dict):
        source = type(
            "CreatedSource",
            (),
            {
                "id": uuid4(),
                "name": data["name"],
                "source_type": data["source_type"],
                "feed_url": data.get("feed_url"),
                "category": data.get("category", "hot"),
                "metadata_": data.get("metadata_", {}),
            },
        )()
        self.created_sources.append(source)
        return source


class FakeArticleRepo:
    def __init__(self):
        self.created: list[dict] = []

    async def create(self, data: dict):
        self.created.append(data)
        return type("Obj", (), {"id": uuid4()})()

    async def get_recent(self, category: str = None, limit: int = 20):
        return []

    async def get_by_url_hash(self, url_hash: str):
        return None


class FakeDedupService:
    async def check_duplicate(self, article_data: dict) -> dict:
        return {
            "is_duplicate": False,
            "duplicate_of": None,
            "event_id": None,
            "similarity": 0.0,
            "layer": None,
        }

    def compute_simhash(self, text: str) -> str:
        return "0" * 16 if text else ""


@pytest.mark.asyncio
async def test_fetch_web_content_extracts_title_and_excerpt(monkeypatch):
    service = ContentIngestionService(FakeSourceRepo(), FakeArticleRepo(), FakeDedupService())
    html = """
    <html>
      <body>
        <h1>Breaking Headline</h1>
        <article>
          <p>short</p>
          <p>This is a long paragraph that should be kept because it has meaningful length and details about the event.</p>
          <p>This is another detailed paragraph with enough content to be included in the final excerpt for processing.</p>
        </article>
      </body>
    </html>
    """

    async def fake_fetch(_url: str) -> str:
        return html

    monkeypatch.setattr(service, "_fetch_html_with_retry", fake_fetch)
    result = await service.fetch_web_content("https://example.com/post")

    assert result is not None
    assert result["title"] == "Breaking Headline"
    assert "meaningful length and details" in result["content_excerpt"]
    assert "another detailed paragraph" in result["content_excerpt"]


@pytest.mark.asyncio
async def test_normalize_entry_fallbacks_to_web_content(monkeypatch):
    service = ContentIngestionService(FakeSourceRepo(), FakeArticleRepo(), FakeDedupService())
    source = FakeSource(id=uuid4(), source_type="rss", feed_url="https://example.com/rss")
    entry = {
        "title": "No content in feed",
        "link": "https://example.com/p/1?utm_source=abc",
        "summary": "",
    }

    async def fake_fetch_web_content(_url: str):
        return {
            "title": "Web title",
            "content_excerpt": "Extracted from web page.",
        }

    monkeypatch.setattr(service, "fetch_web_content", fake_fetch_web_content)
    normalized = await service._normalize_entry(entry, source)

    assert normalized is not None
    assert normalized["url"] == "https://example.com/p/1"
    assert normalized["content"] == "Extracted from web page."
    assert normalized["excerpt"] == "Extracted from web page."


@pytest.mark.asyncio
async def test_crawl_hot_topics_ingests_platform_items(monkeypatch):
    source_repo = FakeSourceRepo()
    article_repo = FakeArticleRepo()
    service = ContentIngestionService(source_repo, article_repo, FakeDedupService())
    platform = {
        "key": "demo",
        "name": "Demo Platform",
        "source_url": "https://example.com",
        "api_url": "https://example.com/api",
    }
    monkeypatch.setattr(service, "HOT_PLATFORMS", (platform,))

    async def fake_fetch_platform_hot_items(_platform: dict):
        return [
            {"title": "Hot A", "url": "https://example.com/a", "content": "A content"},
            {"title": "Hot B", "url": "https://example.com/b", "content": "B content"},
        ]

    monkeypatch.setattr(service, "_fetch_platform_hot_items", fake_fetch_platform_hot_items)

    result = await service.crawl_hot_topics()

    assert len(result) == 1
    assert result[0]["success"] is True
    assert result[0]["inserted_articles"] == 2
    assert len(article_repo.created) == 2
    assert source_repo.created_sources


@pytest.mark.asyncio
async def test_crawl_hot_topics_marks_failure_when_platform_raises(monkeypatch):
    source_repo = FakeSourceRepo()
    article_repo = FakeArticleRepo()
    service = ContentIngestionService(source_repo, article_repo, FakeDedupService())
    platform = {
        "key": "demo",
        "name": "Demo Platform",
        "source_url": "https://example.com",
        "api_url": "https://example.com/api",
    }
    monkeypatch.setattr(service, "HOT_PLATFORMS", (platform,))

    async def fake_fetch_platform_hot_items(_platform: dict):
        raise RuntimeError("platform error")

    monkeypatch.setattr(service, "_fetch_platform_hot_items", fake_fetch_platform_hot_items)

    result = await service.crawl_hot_topics()

    assert len(result) == 1
    assert result[0]["success"] is False
    assert "platform error" in result[0]["error"]
    assert source_repo.status_updates[-1]["success"] is False
