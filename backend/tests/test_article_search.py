from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.v1 import articles as articles_module
from api.v1.router import api_router
from repositories.sqlalchemy.article import ArticleRepository


def _build_search_article(
    article_id: str,
    title: str,
    content: str,
    summary: str,
    published_at: str,
    *,
    is_deleted: bool = False,
):
    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    return {
        "id": article_id,
        "title": title,
        "url": f"https://example.com/articles/{article_id}",
        "excerpt": None,
        "summary": summary,
        "author": "tester",
        "source": {"id": "src-1", "name": "Example Source"},
        "category": "tech",
        "tags": ["ai"],
        "published_at": dt.isoformat(),
        "created_at": dt.isoformat(),
        "view_count": 0,
        "bookmark_count": 0,
        "_content": content,
        "_is_deleted": is_deleted,
    }


class FakeArticleSearchService:
    def __init__(self):
        self._articles = [
            _build_search_article(
                article_id="a-title-latest",
                title="AI beats benchmark",
                content="Deep learning model reaches new score.",
                summary="Model update summary",
                published_at="2026-05-29T08:00:00Z",
            ),
            _build_search_article(
                article_id="a-content-only",
                title="Cloud update",
                content="Only content mentions edge-compute keyword.",
                summary="Infrastructure note",
                published_at="2026-05-28T08:00:00Z",
            ),
            _build_search_article(
                article_id="a-summary-only",
                title="Market brief",
                content="No matching token in content body.",
                summary="Summary includes raretoken for search.",
                published_at="2026-05-27T08:00:00Z",
            ),
            _build_search_article(
                article_id="a-chinese",
                title="人工智能行业观察",
                content="苹果发布新的 AI 功能。",
                summary="中文内容覆盖测试",
                published_at="2026-05-26T08:00:00Z",
            ),
            _build_search_article(
                article_id="a-deleted",
                title="AI should be hidden",
                content="Deleted article still contains AI token.",
                summary="Deleted",
                published_at="2026-05-30T08:00:00Z",
                is_deleted=True,
            ),
        ]

    async def search_articles(self, query: str, limit: int = 20):
        q = query.lower()
        filtered = []
        for article in self._articles:
            if article["_is_deleted"]:
                continue
            haystacks = (
                article["title"].lower(),
                article["_content"].lower(),
                (article["summary"] or "").lower(),
            )
            if any(q in haystack for haystack in haystacks):
                filtered.append(article)

        filtered.sort(key=lambda item: item["published_at"], reverse=True)
        response = []
        for item in filtered[:limit]:
            payload = dict(item)
            payload.pop("_content", None)
            payload.pop("_is_deleted", None)
            response.append(payload)
        return response


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)

    async def override_article_service():
        return FakeArticleSearchService()

    app.dependency_overrides[articles_module.get_article_service] = override_article_service
    return app


def test_search_semantics_title_content_summary_chinese_sort_limit_and_zero_result():
    client = TestClient(_build_test_app())

    resp_title = client.get("/api/v1/articles/search", params={"q": "AI", "limit": 20})
    assert resp_title.status_code == 200
    title_ids = [item["id"] for item in resp_title.json()]
    assert "a-title-latest" in title_ids
    assert "a-deleted" not in title_ids
    assert title_ids == sorted(
        title_ids,
        key=lambda article_id: {
            "a-title-latest": "2026-05-29T08:00:00+00:00",
            "a-chinese": "2026-05-26T08:00:00+00:00",
        }.get(article_id, "1970-01-01T00:00:00+00:00"),
        reverse=True,
    )

    resp_content = client.get("/api/v1/articles/search", params={"q": "edge-compute", "limit": 20})
    assert resp_content.status_code == 200
    assert [item["id"] for item in resp_content.json()] == ["a-content-only"]

    resp_summary = client.get("/api/v1/articles/search", params={"q": "raretoken", "limit": 20})
    assert resp_summary.status_code == 200
    assert [item["id"] for item in resp_summary.json()] == ["a-summary-only"]

    resp_chinese = client.get("/api/v1/articles/search", params={"q": "人工智能", "limit": 20})
    assert resp_chinese.status_code == 200
    assert [item["id"] for item in resp_chinese.json()] == ["a-chinese"]

    resp_limit = client.get("/api/v1/articles/search", params={"q": "AI", "limit": 1})
    assert resp_limit.status_code == 200
    assert len(resp_limit.json()) == 1
    assert resp_limit.json()[0]["id"] == "a-title-latest"

    resp_zero = client.get("/api/v1/articles/search", params={"q": "zzzzzzzzzzzz_no_match", "limit": 20})
    assert resp_zero.status_code == 200
    assert resp_zero.json() == []


def test_search_is_case_insensitive():
    client = TestClient(_build_test_app())

    lower = client.get("/api/v1/articles/search", params={"q": "ai", "limit": 20})
    upper = client.get("/api/v1/articles/search", params={"q": "AI", "limit": 20})
    mixed = client.get("/api/v1/articles/search", params={"q": "Ai", "limit": 20})

    assert lower.status_code == 200
    assert upper.status_code == 200
    assert mixed.status_code == 200
    assert lower.json() == upper.json() == mixed.json()


class _FakeExecuteResult:
    def scalars(self):
        return self

    def all(self):
        return []


class _CaptureSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _FakeExecuteResult()


@pytest.mark.asyncio
async def test_repository_search_uses_parameterized_ilike_and_deleted_filter():
    session = _CaptureSession()
    repo = ArticleRepository(session)
    query = "'; DROP TABLE articles; --"

    await repo.search(query, limit=7)
    assert session.statement is not None

    compiled = session.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled).lower()
    params = compiled.params

    assert "articles.is_deleted = false" in sql
    assert sql.count(" ilike ") >= 3
    assert "order by articles.published_at desc" in sql
    assert "limit" in sql
    assert query not in sql
    assert any(query in str(value) for value in params.values())
    assert compiled.params["param_1"] == 7
