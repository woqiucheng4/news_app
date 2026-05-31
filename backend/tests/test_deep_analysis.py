from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.deep_analysis import DeepAnalysisService


@pytest.mark.asyncio
async def test_deep_analysis_includes_related_sources(monkeypatch):
    article_id = "article-1"
    event_id = "event-1"

    primary = SimpleNamespace(
        id=article_id,
        title="Market rally",
        category="finance",
        summary="Stocks rose on earnings.",
        content=None,
        event_id=event_id,
    )
    related = SimpleNamespace(
        id="article-2",
        title="Wall Street gains",
        summary="Indexes closed higher.",
        content=None,
        source=SimpleNamespace(name="Reuters"),
    )

    service = DeepAnalysisService(session=SimpleNamespace())
    service.freemium = SimpleNamespace(
        assert_premium_feature=AsyncMock(return_value=None),
    )
    service.article_repo = SimpleNamespace(
        get_by_id=AsyncMock(return_value=primary),
        get_by_event_id=AsyncMock(return_value=[primary, related]),
    )

    captured: dict = {}

    async def fake_generate(*, prompt, system_prompt, model, max_tokens, temperature):
        captured["prompt"] = prompt
        return SimpleNamespace(content="Analysis text")

    monkeypatch.setattr("services.deep_analysis.ai_manager.generate", fake_generate)
    monkeypatch.setattr("services.deep_analysis._anthropic_configured", lambda: False)

    result = await service.analyze("user-1", article_id)

    assert result["found"] is True
    assert result["related_source_count"] == 1
    assert "Related coverage from other sources:" in captured["prompt"]
    assert "Reuters" in captured["prompt"]
