"""Seed one demo user and subscriptions for frontend smoke tests."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@dataclass(frozen=True)
class DemoConfig:
    email: str
    display_name: str
    topic_slugs: tuple[str, ...]


def _parse_demo_config() -> DemoConfig:
    email = os.getenv("DEMO_USER_EMAIL", "demo@newsflow.app").strip()
    display_name = os.getenv("DEMO_USER_DISPLAY_NAME", "NewsFlow Demo").strip()
    raw_topic_slugs = os.getenv(
        "DEMO_TOPIC_SLUGS",
        "ai,machine-learning,us-market,global-politics,movies",
    )
    topic_slugs = tuple(
        slug.strip() for slug in raw_topic_slugs.split(",") if slug.strip()
    )
    if not topic_slugs:
        raise RuntimeError("DEMO_TOPIC_SLUGS must contain at least one slug")

    return DemoConfig(
        email=email,
        display_name=display_name,
        topic_slugs=topic_slugs,
    )


async def seed_demo_user_and_subscriptions() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for demo seed")

    config = _parse_demo_config()
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # 1) Ensure user exists.
        user_row = await session.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                  AND is_deleted = false
                """
            ),
            {"email": config.email},
        )
        user_id = user_row.scalar_one_or_none()
        created_user = False
        if user_id is None:
            inserted_user = await session.execute(
                text(
                    """
                    INSERT INTO users (
                        email,
                        display_name,
                        is_active,
                        is_verified,
                        is_premium,
                        settings,
                        created_at,
                        updated_at,
                        is_deleted
                    )
                    VALUES (
                        :email,
                        :display_name,
                        true,
                        true,
                        false,
                        '{}'::jsonb,
                        NOW(),
                        NOW(),
                        false
                    )
                    RETURNING id
                    """
                ),
                {
                    "email": config.email,
                    "display_name": config.display_name,
                },
            )
            user_id = inserted_user.scalar_one()
            created_user = True

        # 2) Ensure user settings exists.
        settings_row = await session.execute(
            text(
                """
                SELECT id
                FROM user_settings
                WHERE user_id = :user_id
                  AND is_deleted = false
                """
            ),
            {"user_id": user_id},
        )
        if settings_row.scalar_one_or_none() is None:
            await session.execute(
                text(
                    """
                    INSERT INTO user_settings (
                        user_id,
                        push_enabled,
                        push_daily_briefing,
                        push_breaking_news,
                        push_max_per_day,
                        language,
                        theme,
                        font_size,
                        summary_length,
                        summary_language,
                        extra,
                        created_at,
                        updated_at,
                        is_deleted
                    )
                    VALUES (
                        :user_id,
                        true,
                        true,
                        true,
                        5,
                        'en',
                        'system',
                        'medium',
                        'balanced',
                        'auto',
                        '{}'::jsonb,
                        NOW(),
                        NOW(),
                        false
                    )
                    """
                ),
                {"user_id": user_id},
            )

        # 3) Resolve topics by slugs.
        topics = await session.execute(
            text(
                """
                SELECT id, slug
                FROM topics
                WHERE slug = ANY(:slugs)
                  AND is_deleted = false
                """
            ),
            {"slugs": list(config.topic_slugs)},
        )
        topic_rows = topics.fetchall()
        topic_ids = [row[0] for row in topic_rows]
        found_slugs = {row[1] for row in topic_rows}
        missing_slugs = [slug for slug in config.topic_slugs if slug not in found_slugs]
        if not topic_ids:
            raise RuntimeError(
                "No matching topics found. Run `python scripts/seed_topics.py` first."
            )

        # 4) Upsert subscriptions.
        for topic_id in topic_ids:
            await session.execute(
                text(
                    """
                    INSERT INTO subscriptions (
                        user_id,
                        topic_id,
                        is_active,
                        priority,
                        push_enabled,
                        push_breaking_only,
                        subscribed_at,
                        created_at,
                        updated_at,
                        is_deleted
                    )
                    VALUES (
                        :user_id,
                        :topic_id,
                        true,
                        0,
                        true,
                        false,
                        NOW(),
                        NOW(),
                        NOW(),
                        false
                    )
                    ON CONFLICT (user_id, topic_id)
                    DO UPDATE SET
                        is_active = true,
                        push_enabled = true,
                        push_breaking_only = false,
                        is_deleted = false,
                        updated_at = NOW()
                    """
                ),
                {
                    "user_id": user_id,
                    "topic_id": topic_id,
                },
            )

        # 5) Recalculate topic subscriber_count for consistency.
        await session.execute(
            text(
                """
                UPDATE topics t
                SET subscriber_count = counts.cnt,
                    updated_at = NOW()
                FROM (
                    SELECT topic_id, COUNT(*)::int AS cnt
                    FROM subscriptions
                    WHERE is_deleted = false
                      AND is_active = true
                    GROUP BY topic_id
                ) counts
                WHERE t.id = counts.topic_id
                """
            )
        )
        await session.execute(
            text(
                """
                UPDATE topics
                SET subscriber_count = 0,
                    updated_at = NOW()
                WHERE id NOT IN (
                    SELECT topic_id
                    FROM subscriptions
                    WHERE is_deleted = false
                      AND is_active = true
                )
                """
            )
        )

        await session.commit()

        created_text = "created" if created_user else "already existed"
        print(
            f"Demo user {config.email} ({created_text}), "
            f"subscriptions ensured for {len(topic_ids)} topics"
        )
        if missing_slugs:
            print(
                "Skipped missing topic slugs: "
                + ", ".join(missing_slugs)
            )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_user_and_subscriptions())
