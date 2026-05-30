from types import SimpleNamespace

import pytest

from services.article import ArticleService


class FakeArticleRepo:
    def __init__(self, article):
        self.article = article

    async def get_by_id(self, article_id: str):
        if self.article is None:
            return None
        return self.article if str(self.article.id) == article_id else None

    async def get_by_event_id(self, event_id: str):
        return []


@pytest.mark.asyncio
async def test_hydrate_cached_article_backfills_related_and_source_url(monkeypatch):
    article = SimpleNamespace(
        id="a-1",
        event_id=None,
        source=SimpleNamespace(id="s-1", name="Source", url="https://source.example"),
    )
    service = ArticleService(FakeArticleRepo(article))

    cached = {
        "id": "a-1",
        "title": "Title",
        "source": {"id": "s-1", "name": "Source"},
    }
    cache_writes = []

    async def fake_set(key, value, ttl=3600):
        cache_writes.append((key, value, ttl))

    monkeypatch.setattr(
        "services.article.cache_manager.set",
        fake_set,
    )

    hydrated = await service._hydrate_cached_article(cached, "a-1")

    assert hydrated["related_articles"] == []
    assert hydrated["related_articles_total"] == 0
    assert hydrated["source"]["url"] == "https://source.example"
    assert cache_writes
    assert cache_writes[0][0] == "article:a-1"
