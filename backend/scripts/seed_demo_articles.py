"""Seed demo articles for feed UI smoke tests."""

from __future__ import annotations

import asyncio
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@dataclass(frozen=True)
class DemoArticleSeed:
    title: str
    url: str
    category: str
    tags: tuple[str, ...]
    excerpt: str
    summary: str
    content: str
    author: str = "NewsFlow Demo"


DEMO_ARTICLES: tuple[DemoArticleSeed, ...] = (
    DemoArticleSeed(
        title="Open-source AI models show rapid gains in coding benchmarks",
        url="https://demo.newsflow.app/articles/ai-coding-benchmarks",
        category="tech",
        tags=("ai", "coding", "open-source"),
        excerpt="Several open models narrowed the gap with top proprietary systems.",
        summary="New open-source AI models improved coding benchmark scores significantly this month. "
        "Teams report lower inference costs and faster iteration cycles. "
        "The trend may accelerate enterprise adoption of self-hosted AI stacks.",
        content="A set of newly released open-source models posted higher coding benchmark scores. "
        "Infrastructure teams highlighted cost savings and easier fine-tuning for internal workflows.",
    ),
    DemoArticleSeed(
        title="Chip supply chain update: capacity expansion eases lead time pressure",
        url="https://demo.newsflow.app/articles/chip-supply-chain-update",
        category="tech",
        tags=("semiconductor", "supply-chain"),
        excerpt="Manufacturing capacity expansion is reducing wait times for key components.",
        summary="Chip manufacturing capacity increased across multiple regions this quarter. "
        "Lead times for selected components are gradually normalizing. "
        "Analysts still caution that high-end nodes remain strategically constrained.",
        content="Foundries added production lines while downstream inventory policies improved forecasting. "
        "Vendors expect less volatility than last year, though advanced packaging remains a bottleneck.",
    ),
    DemoArticleSeed(
        title="US market closes higher as inflation data meets expectations",
        url="https://demo.newsflow.app/articles/us-market-inflation-session",
        category="finance",
        tags=("macro", "equities", "inflation"),
        excerpt="Equities advanced after inflation data came in near consensus estimates.",
        summary="Major US indices ended the session higher after inflation data matched market forecasts. "
        "Rate-cut expectations were largely unchanged in derivatives pricing. "
        "Cyclical sectors outperformed defensives into the close.",
        content="Traders cited stable inflation figures and resilient earnings guidance as support factors. "
        "Treasury yields moved in a narrow range during the afternoon session.",
    ),
    DemoArticleSeed(
        title="Crypto spot volumes rebound amid renewed ETF inflows",
        url="https://demo.newsflow.app/articles/crypto-spot-volume-rebound",
        category="finance",
        tags=("crypto", "etf", "markets"),
        excerpt="Spot trading activity picked up as institutional flows turned positive.",
        summary="Crypto spot volumes rose following a week of net positive ETF inflows. "
        "Large-cap assets led market depth recovery across major exchanges. "
        "Volatility remains elevated around macro event windows.",
        content="Market participants pointed to improved liquidity conditions and stronger risk sentiment. "
        "Order-book depth expanded in top pairs while funding rates stayed mostly balanced.",
    ),
    DemoArticleSeed(
        title="Global climate summit agrees on updated transition financing framework",
        url="https://demo.newsflow.app/articles/climate-summit-transition-finance",
        category="news",
        tags=("climate", "policy"),
        excerpt="Delegates finalized a financing framework targeting transition projects.",
        summary="Delegates at the global climate summit approved a revised transition financing framework. "
        "The package prioritizes grid modernization and industrial decarbonization projects. "
        "Implementation timelines vary by region and funding capacity.",
        content="Negotiators aligned on reporting standards and milestone tracking for funded projects. "
        "Observers said governance clarity improved compared with previous rounds.",
    ),
    DemoArticleSeed(
        title="Studio slate refresh drives strong opening weekend for sci-fi releases",
        url="https://demo.newsflow.app/articles/studio-slate-sci-fi-weekend",
        category="entertainment",
        tags=("movies", "box-office"),
        excerpt="New sci-fi titles delivered better-than-expected opening figures.",
        summary="Multiple sci-fi releases posted solid opening weekend numbers across key markets. "
        "Studios credited staggered release windows and targeted fan campaigns. "
        "Analysts expect follow-up performance to depend on weekday retention.",
        content="The latest studio slate leaned on franchise familiarity while introducing new directors. "
        "Early audience sentiment remained positive in post-screening surveys.",
    ),
    DemoArticleSeed(
        title="Major football league enters final stretch with tight title race",
        url="https://demo.newsflow.app/articles/football-title-race-final-stretch",
        category="sports",
        tags=("football", "league"),
        excerpt="Top teams remain within a narrow points margin before decisive fixtures.",
        summary="The league title race remains highly competitive as clubs enter the final stretch. "
        "A narrow points spread keeps multiple contenders in play. "
        "Upcoming head-to-head matches are likely to define the outcome.",
        content="Coaches emphasized squad rotation and injury management ahead of dense fixtures. "
        "Analysts flagged defensive consistency as the biggest differentiator.",
    ),
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def seed_demo_articles() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for demo article seed")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # Ensure one demo source exists.
        source_row = await session.execute(
            text(
                """
                SELECT id
                FROM sources
                WHERE name = 'NewsFlow Demo Wire'
                  AND is_deleted = false
                LIMIT 1
                """
            )
        )
        source_id = source_row.scalar_one_or_none()
        if source_id is None:
            created = await session.execute(
                text(
                    """
                    INSERT INTO sources (
                        name,
                        url,
                        source_type,
                        feed_url,
                        is_active,
                        error_count,
                        category,
                        language,
                        fetch_interval_minutes,
                        heat_score,
                        metadata,
                        created_at,
                        updated_at,
                        is_deleted
                    )
                    VALUES (
                        'NewsFlow Demo Wire',
                        'https://demo.newsflow.app',
                        'api',
                        NULL,
                        true,
                        0,
                        'demo',
                        'en',
                        60,
                        0,
                        '{}'::jsonb,
                        NOW(),
                        NOW(),
                        false
                    )
                    RETURNING id
                    """
                )
            )
            source_id = created.scalar_one()

        existing_hash_rows = await session.execute(text("SELECT url_hash FROM articles"))
        existing_hashes = {row[0] for row in existing_hash_rows.fetchall() if row[0]}

        now = datetime.utcnow()
        to_insert: list[dict] = []
        for idx, seed in enumerate(DEMO_ARTICLES):
            url_hash = _sha256(seed.url)
            if url_hash in existing_hashes:
                continue
            published_at = now - timedelta(hours=idx * 3)
            content_hash = _sha256(seed.content)
            to_insert.append(
                {
                    "title": seed.title,
                    "url": seed.url,
                    "content": seed.content,
                    "excerpt": seed.excerpt,
                    "source_id": source_id,
                    "author": seed.author,
                    "published_at": published_at,
                    "category": seed.category,
                    "tags": list(seed.tags),
                    "url_hash": url_hash,
                    "title_hash": _sha256(seed.title),
                    "content_hash": content_hash,
                    "simhash": content_hash,
                    "summary": seed.summary,
                    "summary_model": "demo-seed",
                    "summary_generated_at": published_at,
                    "is_processed": True,
                    "is_summary_generated": True,
                    "view_count": 0,
                    "bookmark_count": 0,
                }
            )

        if to_insert:
            await session.execute(
                text(
                    """
                    INSERT INTO articles (
                        title,
                        url,
                        content,
                        excerpt,
                        source_id,
                        author,
                        published_at,
                        category,
                        tags,
                        url_hash,
                        title_hash,
                        content_hash,
                        simhash,
                        summary,
                        summary_model,
                        summary_generated_at,
                        event_id,
                        is_processed,
                        is_summary_generated,
                        view_count,
                        bookmark_count,
                        metadata,
                        created_at,
                        updated_at,
                        is_deleted
                    )
                    VALUES (
                        :title,
                        :url,
                        :content,
                        :excerpt,
                        :source_id,
                        :author,
                        :published_at,
                        :category,
                        :tags,
                        :url_hash,
                        :title_hash,
                        :content_hash,
                        :simhash,
                        :summary,
                        :summary_model,
                        :summary_generated_at,
                        NULL,
                        :is_processed,
                        :is_summary_generated,
                        :view_count,
                        :bookmark_count,
                        '{}'::jsonb,
                        NOW(),
                        NOW(),
                        false
                    )
                    """
                ),
                to_insert,
            )
            await session.commit()
            print(f"Inserted {len(to_insert)} demo articles")
        else:
            print("Demo article seed already exists, nothing inserted")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_articles())
