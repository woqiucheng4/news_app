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
3. What to watch next (1-2 bullet points as plain text lines)

Keep the total under 250 words. Be factual and neutral. Use the same language as the source material."""


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

        model = AIModel.CLAUDE_HAIKU if _anthropic_configured() else AIModel.GPT_4O_MINI
        prompt = (
            f"Title: {article.title}\n"
            f"Source category: {article.category or 'general'}\n\n"
            f"{content}"
        )

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
        }


def _anthropic_configured() -> bool:
    from core.config import get_settings

    return bool(get_settings().ai.anthropic_api_key)
