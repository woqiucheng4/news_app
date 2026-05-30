from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.content_ingestion import ContentIngestionService


class FakeSourceRepo:
    async def get_by_id(self, _source_id: str):
        return None

    async def get_active_sources(self):
        return []

    async def update_fetch_status(self, _source_id: str, success: bool, error: str = None):
        return True

    async def list(self, filters=None, order_by=None, limit=100, offset=0):
        return []

    async def create(self, data: dict):
        return SimpleNamespace(
            id=uuid4(),
            name=data["name"],
            source_type=data["source_type"],
            feed_url=data.get("feed_url"),
            category=data.get("category"),
            metadata_=data.get("metadata_", {}),
        )


class FakeArticleRepo:
    async def create(self, data: dict):
        return SimpleNamespace(id=uuid4(), **data)

    async def get_recent(self, category: str = None, limit: int = 20):
        return []

    async def get_by_url_hash(self, url_hash: str):
        return None


class FakeDedupService:
    async def check_duplicate(self, article_data: dict):
        return {"is_duplicate": False, "duplicate_of": None, "event_id": None, "similarity": 0.0, "layer": None}

    def compute_simhash(self, text: str):
        return "0" * 16 if text else ""


@pytest.fixture
def service():
    return ContentIngestionService(FakeSourceRepo(), FakeArticleRepo(), FakeDedupService())


@pytest.mark.asyncio
async def test_reddit_and_github_fetchers_parse_json(monkeypatch, service):
    async def fake_fetch_json(url: str, headers=None):
        if "reddit.com" in url:
            return {
                "data": {
                    "children": [
                        {
                            "data": {
                                "title": "Reddit Hot",
                                "permalink": "/r/all/comments/abc",
                                "selftext": "body",
                                "created_utc": 1716450000,
                                "score": 123,
                                "author": "r-user",
                            }
                        }
                    ]
                }
            }
        return {
            "items": [
                {
                    "full_name": "org/repo",
                    "html_url": "https://github.com/org/repo",
                    "description": "repo desc",
                    "updated_at": "2026-05-28T08:00:00Z",
                    "stargazers_count": 999,
                    "owner": {"login": "octocat"},
                }
            ]
        }

    monkeypatch.setattr(service, "_fetch_json", fake_fetch_json)

    reddit_items = await service._fetch_reddit_hot_items(
        {"api_url": "https://www.reddit.com/r/all/hot.json?limit=25"}
    )
    github_items = await service._fetch_github_hot_items(
        {
            "api_url": "https://api.github.com/search/repositories?q=created:>={date}&sort=stars&order=desc&per_page=25"
        }
    )

    assert reddit_items and reddit_items[0]["title"] == "Reddit Hot"
    assert github_items and github_items[0]["title"] == "org/repo"


@pytest.mark.asyncio
async def test_cn_platform_fetchers_parse_json(monkeypatch, service):
    async def fake_fetch_json(url: str, headers=None):
        if "weibo" in url:
            return {"data": {"realtime": [{"word": "热搜词", "num": 9999, "note": "备注"}]}}
        if "zhihu" in url:
            return {
                "data": [
                    {
                        "target": {
                            "id": 123,
                            "title": "知乎热榜",
                            "excerpt": "知乎摘要",
                            "author": {"name": "知乎作者"},
                        }
                    }
                ]
            }
        if "baidu" in url:
            return {"data": {"cards": [{"content": [{"word": "百度热点", "hotScore": 5000}]}]}}
        return {
            "data": {
                "list": [
                    {
                        "bvid": "BV1xx411",
                        "title": "B站热门",
                        "desc": "bili desc",
                        "stat": {"view": 888},
                        "owner": {"name": "up"},
                        "pubdate": 1716450000,
                    }
                ]
            }
        }

    monkeypatch.setattr(service, "_fetch_json", fake_fetch_json)

    weibo_items = await service._fetch_weibo_hot_items({"api_url": "https://weibo.com/ajax/side/hotSearch"})
    zhihu_items = await service._fetch_zhihu_hot_items({"api_url": "https://www.zhihu.com/api/v3/feed/topstory/hot-list"})
    baidu_items = await service._fetch_baidu_hot_items({"api_url": "https://top.baidu.com/api/board"})
    bili_items = await service._fetch_bilibili_hot_items({"api_url": "https://api.bilibili.com/x/web-interface/ranking/v2"})

    assert weibo_items[0]["title"] == "热搜词"
    assert zhihu_items[0]["title"] == "知乎热榜"
    assert baidu_items[0]["title"] == "百度热点"
    assert bili_items[0]["title"] == "B站热门"


@pytest.mark.asyncio
async def test_feed_based_hot_fetchers_and_dispatch(monkeypatch, service):
    fake_feed = SimpleNamespace(
        entries=[
            {
                "title": "Trend A",
                "link": "https://example.com/trend-a",
                "summary": "trend summary",
                "published": "Thu, 23 May 2024 10:00:00 GMT",
                "author": "trend-author",
            }
        ]
    )

    async def fake_to_thread(func, url):
        return fake_feed

    monkeypatch.setattr("services.content_ingestion.asyncio.to_thread", fake_to_thread)

    trends_items = await service._fetch_google_trends_hot_items({"api_url": "https://trends.google.com/trending/rss?geo=US"})
    ph_items = await service._fetch_product_hunt_hot_items({"api_url": "https://www.producthunt.com/feed"})
    assert trends_items and trends_items[0]["title"] == "Trend A"
    assert ph_items and ph_items[0]["title"] == "Trend A"

    async def fake_reddit(_platform):
        return [{"title": "dispatched"}]

    monkeypatch.setattr(service, "_fetch_reddit_hot_items", fake_reddit)
    dispatched = await service._fetch_platform_hot_items({"key": "reddit"})
    unknown = await service._fetch_platform_hot_items({"key": "unknown"})
    assert dispatched[0]["title"] == "dispatched"
    assert unknown == []


@pytest.mark.asyncio
async def test_build_hot_payload_and_source_resolution(monkeypatch, service):
    source = await service._resolve_or_create_hot_source(
        {
            "key": "demo",
            "name": "Demo",
            "source_url": "https://example.com",
            "api_url": "https://example.com/api",
        }
    )
    payload = service._build_hot_topic_payload(
        item={"title": "Hot Topic", "url": "https://example.com/a?utm_source=x", "content": "hello", "score": "12"},
        source=source,
        platform_key="demo",
    )
    assert source is not None
    assert payload is not None
    assert payload["url"] == "https://example.com/a"
    assert payload["category"] == "hot"
