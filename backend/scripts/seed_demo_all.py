"""Run all demo seed scripts for frontend smoke testing."""

from __future__ import annotations

import asyncio
import os

from seed_topics import seed_topics
from seed_demo_user_and_subscriptions import seed_demo_user_and_subscriptions
from seed_demo_articles import seed_demo_articles


async def seed_demo_all() -> None:
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required for demo seeds")

    print("Seeding topics ...")
    await seed_topics()

    print("Seeding demo user + subscriptions ...")
    await seed_demo_user_and_subscriptions()

    print("Seeding demo articles ...")
    await seed_demo_articles()

    print("All demo seeds completed")


if __name__ == "__main__":
    asyncio.run(seed_demo_all())
