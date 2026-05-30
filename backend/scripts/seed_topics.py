"""Seed initial topics for subscription/category browsing."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@dataclass(frozen=True)
class TopicSeed:
    name: str
    slug: str
    category: str
    description: str


INITIAL_TOPICS: tuple[TopicSeed, ...] = (
    TopicSeed("AI", "ai", "tech", "Artificial intelligence trends and breakthroughs"),
    TopicSeed("Machine Learning", "machine-learning", "tech", "ML research, tools, and applied cases"),
    TopicSeed("Startups", "startups", "tech", "Startup ecosystem, funding, and launches"),
    TopicSeed("Cybersecurity", "cybersecurity", "tech", "Security incidents, defense, and vulnerabilities"),
    TopicSeed("Mobile", "mobile", "tech", "Mobile platforms, devices, and app ecosystem"),
    TopicSeed("Cloud", "cloud", "tech", "Cloud platforms, infra updates, and pricing"),
    TopicSeed("US Market", "us-market", "finance", "US market movement and macro signals"),
    TopicSeed("Earnings", "earnings", "finance", "Quarterly earnings and financial reports"),
    TopicSeed("Crypto", "crypto", "finance", "Crypto assets, regulation, and infrastructure"),
    TopicSeed("Commodities", "commodities", "finance", "Oil, gold, and commodity dynamics"),
    TopicSeed("Global Politics", "global-politics", "news", "Geopolitical updates and diplomacy"),
    TopicSeed("Climate", "climate", "news", "Climate policy, science, and energy transition"),
    TopicSeed("Health", "health", "news", "Public health, biotech, and medical updates"),
    TopicSeed("Science", "science", "news", "Scientific discoveries and space exploration"),
    TopicSeed("Gaming", "gaming", "entertainment", "Games, platforms, and industry news"),
    TopicSeed("Movies", "movies", "entertainment", "Film releases, box office, and production"),
    TopicSeed("Music", "music", "entertainment", "Music releases, industry, and artist activity"),
    TopicSeed("Football", "football", "sports", "Football leagues, transfers, and tournaments"),
    TopicSeed("Basketball", "basketball", "sports", "Basketball leagues, games, and analysis"),
    TopicSeed("Tennis", "tennis", "sports", "Tennis tours, rankings, and grand slams"),
)


async def seed_topics() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for seeding topics")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        existing_rows = await session.execute(text("SELECT slug FROM topics WHERE is_deleted = false"))
        existing_slugs = {row[0] for row in existing_rows.fetchall() if row[0]}
        to_insert = [topic for topic in INITIAL_TOPICS if topic.slug not in existing_slugs]

        if to_insert:
            await session.execute(
                text(
                    """
                    INSERT INTO topics (
                        name,
                        slug,
                        description,
                        category,
                        subscriber_count,
                        article_count,
                        icon_url,
                        metadata,
                        created_at,
                        updated_at,
                        is_deleted
                    )
                    VALUES (
                        :name,
                        :slug,
                        :description,
                        :category,
                        0,
                        0,
                        NULL,
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
            print(f"Inserted {len(to_insert)} topics")
        else:
            print("Topic seed data already exists, nothing inserted")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_topics())
