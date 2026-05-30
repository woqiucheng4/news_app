"""Seed initial RSS sources for local development."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@dataclass(frozen=True)
class RSSSourceSeed:
    name: str
    url: str
    feed_url: str
    category: str
    language: str = "en"


INITIAL_RSS_SOURCES: tuple[RSSSourceSeed, ...] = (
    RSSSourceSeed("TechCrunch", "https://techcrunch.com", "https://techcrunch.com/feed/", "tech"),
    RSSSourceSeed("Reuters World", "https://www.reuters.com", "https://www.reutersagency.com/feed/?best-topics=world&post_type=best", "news"),
    RSSSourceSeed("Reuters Technology", "https://www.reuters.com", "https://www.reutersagency.com/feed/?best-topics=technology&post_type=best", "tech"),
    RSSSourceSeed("Hacker News", "https://news.ycombinator.com", "https://hnrss.org/frontpage", "tech"),
    RSSSourceSeed("The Verge", "https://www.theverge.com", "https://www.theverge.com/rss/index.xml", "tech"),
    RSSSourceSeed("Ars Technica", "https://arstechnica.com", "https://feeds.arstechnica.com/arstechnica/index", "tech"),
    RSSSourceSeed("Wired", "https://www.wired.com", "https://www.wired.com/feed/rss", "tech"),
    RSSSourceSeed("Bloomberg Markets", "https://www.bloomberg.com", "https://feeds.bloomberg.com/markets/news.rss", "finance"),
    RSSSourceSeed("CNBC Top News", "https://www.cnbc.com", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "finance"),
    RSSSourceSeed("Financial Times", "https://www.ft.com", "https://www.ft.com/rss/home", "finance"),
    RSSSourceSeed("CoinDesk", "https://www.coindesk.com", "https://www.coindesk.com/arc/outboundfeeds/rss/", "crypto"),
    RSSSourceSeed("MIT Technology Review", "https://www.technologyreview.com", "https://www.technologyreview.com/feed/", "tech"),
    RSSSourceSeed("The Guardian World", "https://www.theguardian.com", "https://www.theguardian.com/world/rss", "news"),
    RSSSourceSeed("BBC World", "https://www.bbc.com", "http://feeds.bbci.co.uk/news/world/rss.xml", "news"),
    RSSSourceSeed("NPR News", "https://www.npr.org", "https://feeds.npr.org/1001/rss.xml", "news"),
    RSSSourceSeed("Engadget", "https://www.engadget.com", "https://www.engadget.com/rss.xml", "tech"),
    RSSSourceSeed("VentureBeat", "https://venturebeat.com", "https://venturebeat.com/feed/", "tech"),
    RSSSourceSeed("Product Hunt", "https://www.producthunt.com", "https://www.producthunt.com/feed", "tech"),
    RSSSourceSeed("Reddit Technology", "https://www.reddit.com/r/technology", "https://www.reddit.com/r/technology/.rss", "tech"),
    RSSSourceSeed("Reddit World News", "https://www.reddit.com/r/worldnews", "https://www.reddit.com/r/worldnews/.rss", "news"),
)


async def seed_sources() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for seeding sources")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        existing_rows = await session.execute(text("SELECT feed_url FROM sources WHERE source_type = 'rss'"))
        existing_feed_urls = {row[0] for row in existing_rows.fetchall() if row[0]}

        to_insert = [source for source in INITIAL_RSS_SOURCES if source.feed_url not in existing_feed_urls]
        if to_insert:
            await session.execute(
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
                        :name,
                        :url,
                        'rss',
                        :feed_url,
                        true,
                        0,
                        :category,
                        :language,
                        30,
                        0,
                        '{}'::jsonb,
                        NOW(),
                        NOW(),
                        false
                    )
                    """
                ),
                [seed.__dict__ for seed in to_insert],
            )
            await session.commit()
            print(f"Inserted {len(to_insert)} RSS sources")
        else:
            print("RSS seed data already exists, nothing inserted")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_sources())
