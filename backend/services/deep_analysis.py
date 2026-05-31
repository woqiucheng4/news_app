"""
Premium deep analysis using Claude (fallback to GPT-4o-mini).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.ai import AIModel, ai_manager
from repositories.sqlalchemy.article import ArticleRepository
from services.freemium import FreemiumService

logger = logging.getLogger(__name__)

DEEP_ANALYSIS_SYSTEM_PROMPT = """You are a senior news analyst helping premium subscribers understand a story in depth.

Produce a structured brief with:
1. What happened (2-3 sentences)
2. Why it matters (2-3 sentences)
3. Multi-source synthesis — compare how different outlets cover the story (2-4 sentences, only when multiple sources are provided)
4. What to watch next (1-2 bullet points as plain text lines)

Keep the total under 300 words. Be factual and neutral. Use the same language as the source material."""


class DeepAnalysisService:
    """Generate premium deep analysis for an article."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.article_repo = ArticleRepository(session)
        self.freemium = FreemiumService(session)

    async def analyze(self, user_id: str, article_id: str) -> dict:
        await self.freemium.assert_premium_feature(user_id, "deep_analysis")

        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return {"found": False, "analysis": None}

        content = article.summary or article.content or article.title
        if not content:
            return {"found": True, "analysis": None}

        related_sources = await self._collect_related_sources(article)
        model = AIModel.CLAUDE_HAIKU if _anthropic_configured() else AIModel.GPT_4O_MINI
        prompt_parts = [
            f"Title: {article.title}",
            f"Source category: {article.category or 'general'}",
            "",
            "Primary article:",
            content,
        ]
        if related_sources:
            prompt_parts.extend(["", "Related coverage from other sources:"])
            prompt_parts.extend(related_sources)

        prompt = "\n".join(prompt_parts)

        try:
            response = await ai_manager.generate(
                prompt=prompt,
                system_prompt=DEEP_ANALYSIS_SYSTEM_PROMPT,
                model=model,
                max_tokens=400,
                temperature=0.4,
            )
            analysis = (response.content or "").strip()
        except Exception as exc:
            logger.warning("Deep analysis failed for %s: %s", article_id, exc)
            raise

        return {
            "found": True,
            "article_id": str(article.id),
            "model": model.value,
            "analysis": analysis,
            "related_source_count": len(related_sources),
        }


    async def _collect_related_sources(self, article) -> list[str]:
        """Gather summaries from other articles in the same event cluster."""
        event_id = getattr(article, "event_id", None)
        if not event_id:
            return []

        related = await self.article_repo.get_by_event_id(str(event_id))
        sources: list[str] = []
        for item in related:
            if str(item.id) == str(article.id):
                continue
            snippet = (item.summary or item.content or item.title or "").strip()
            if not snippet:
                continue
            source_name = getattr(getattr(item, "source", None), "name", None) or "Unknown source"
            sources.append(f"- {source_name}: {snippet[:400]}")
            if len(sources) >= 4:
                break
        return sources


def _anthropic_configured() -> bool:
    from core.config import get_settings

    return bool(get_settings().ai.anthropic_api_key)
