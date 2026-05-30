from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from uuid import uuid4
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.article import ArticleService, enqueue_generate_summary_task


@dataclass
class FakeArticle:
    id: object
    title: str
    content: str
    url_hash: str
    is_summary_generated: bool = False
    summary: Optional[str] = None


class FakeArticleRepo:
    def __init__(self, article: FakeArticle):
        self.article = article
        self.updated_payloads: list[dict] = []

    async def get_by_id(self, _article_id: str):
        return self.article

    async def update_summary(
        self,
        id: str,
        summary: str,
        model: str,
        relevance_score: Optional[float] = None,
    ):
        self.updated_payloads.append(
            {
                "id": id,
                "summary": summary,
                "model": model,
                "relevance_score": relevance_score,
            }
        )
        self.article.summary = summary
        self.article.is_summary_generated = True
        return True


@pytest.mark.asyncio
async def test_generate_summary_uses_redis_cache_first(monkeypatch):
    article = FakeArticle(
        id=uuid4(),
        title="A title",
        content="A content body",
        url_hash="hash-1",
    )
    repo = FakeArticleRepo(article)
    service = ArticleService(repo)

    async def fake_cache_get(key: str):
        assert key == "summary:hash-1"
        return {"summary": "cached summary", "model": "cache-model", "relevance_score": 91}

    async def fake_delete(_key: str):
        return True

    async def fail_ai_call(**_kwargs):
        raise AssertionError("AI should not be called on summary cache hit")

    monkeypatch.setattr("services.article.cache_manager.get", fake_cache_get)
    monkeypatch.setattr("services.article.cache_manager.delete", fake_delete)
    monkeypatch.setattr("services.article.ai_manager.generate", fail_ai_call)

    result = await service.generate_summary(str(article.id))

    assert result == "cached summary"
    assert repo.updated_payloads[-1]["model"] == "cache-model"
    assert repo.updated_payloads[-1]["relevance_score"] == 91


@pytest.mark.asyncio
async def test_generate_summary_retries_and_persists(monkeypatch):
    article = FakeArticle(
        id=uuid4(),
        title="Important title",
        content="Important content",
        url_hash="hash-2",
    )
    repo = FakeArticleRepo(article)
    service = ArticleService(repo)
    calls = {"count": 0}
    cached_payloads: list[tuple[str, dict, int]] = []

    async def fake_cache_get(_key: str):
        return None

    async def fake_cache_set(key: str, value: dict, ttl: int):
        cached_payloads.append((key, value, ttl))
        return True

    async def fake_delete(_key: str):
        return True

    async def fake_ai_generate(**_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("timeout")
        return SimpleNamespace(
            content='{"summary":"final summary","relevance_score":87}',
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=40,
            total_tokens=140,
            cost_usd=0.001,
        )

    monkeypatch.setattr("services.article.cache_manager.get", fake_cache_get)
    monkeypatch.setattr("services.article.cache_manager.set", fake_cache_set)
    monkeypatch.setattr("services.article.cache_manager.delete", fake_delete)
    monkeypatch.setattr("services.article.ai_manager.generate", fake_ai_generate)

    result = await service.generate_summary(str(article.id))

    assert result == "final summary"
    assert calls["count"] == 2
    assert repo.updated_payloads[-1]["summary"] == "final summary"
    assert repo.updated_payloads[-1]["relevance_score"] == 87.0
    assert cached_payloads
    assert cached_payloads[-1][0] == "summary:hash-2"
    assert cached_payloads[-1][2] == ArticleService.SUMMARY_CACHE_TTL


@pytest.mark.asyncio
async def test_enqueue_generate_summary_task_does_not_raise(monkeypatch):
    async def fake_enqueue_task(*_args, **_kwargs):
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr("services.article.enqueue_task", fake_enqueue_task)
    result = await enqueue_generate_summary_task(str(uuid4()))
    assert result is None
