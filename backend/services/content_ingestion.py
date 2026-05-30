"""
Content ingestion service implementation.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from uuid import uuid4

import feedparser
import httpx
from selectolax.parser import HTMLParser
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from models.article import Source
from repositories.sqlalchemy.article import ArticleRepository, SourceRepository, EventRepository
from services.deduplication import DeduplicationService
from services.interfaces import IContentIngestionService
from services.article import enqueue_generate_summary_task


class ContentIngestionService(IContentIngestionService):
    """Fetch RSS feeds, deduplicate articles, and persist normalized content."""
    MAX_CONCURRENT_FETCHES = 10
    HOT_PLATFORM_REQUEST_INTERVAL_SECONDS = 2
    HOT_TOPIC_LIMIT_PER_PLATFORM = 20
    HOT_PLATFORMS = (
        {
            "key": "hackernews",
            "name": "Hacker News",
            "source_url": "https://news.ycombinator.com",
            "api_url": "https://hacker-news.firebaseio.com/v0/topstories.json",
        },
        {
            "key": "reddit",
            "name": "Reddit",
            "source_url": "https://www.reddit.com/r/all",
            "api_url": "https://www.reddit.com/r/all/hot.json?limit=25",
        },
        {
            "key": "github",
            "name": "GitHub Trending",
            "source_url": "https://github.com/trending",
            "api_url": "https://api.github.com/search/repositories?q=created:>={date}&sort=stars&order=desc&per_page=25",
        },
        {
            "key": "google_trends",
            "name": "Google Trends",
            "source_url": "https://trends.google.com",
            "api_url": "https://trends.google.com/trending/rss?geo=US",
        },
        {
            "key": "product_hunt",
            "name": "Product Hunt",
            "source_url": "https://www.producthunt.com",
            "api_url": "https://www.producthunt.com/feed",
        },
        {
            "key": "weibo",
            "name": "Weibo Hot Search",
            "source_url": "https://weibo.com",
            "api_url": "https://weibo.com/ajax/side/hotSearch",
        },
        {
            "key": "zhihu",
            "name": "Zhihu Hot",
            "source_url": "https://www.zhihu.com",
            "api_url": "https://www.zhihu.com/api/v3/feed/topstory/hot-list",
        },
        {
            "key": "baidu",
            "name": "Baidu Hot Search",
            "source_url": "https://top.baidu.com",
            "api_url": "https://top.baidu.com/api/board?platform=wise&tab=realtime",
        },
        {
            "key": "bilibili",
            "name": "Bilibili Hot",
            "source_url": "https://www.bilibili.com",
            "api_url": "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all",
        },
    )

    def __init__(
        self,
        source_repo: SourceRepository,
        article_repo: ArticleRepository,
        dedup_service: Optional[DeduplicationService] = None,
        event_repo: Optional[EventRepository] = None,
    ) -> None:
        self.source_repo = source_repo
        self.article_repo = article_repo
        self.dedup_service = dedup_service or DeduplicationService(article_repo)
        self.event_repo = event_repo

    async def fetch_feed(self, source_id: str) -> List[Dict]:
        source = await self.source_repo.get_by_id(source_id)
        if not source or source.source_type != "rss" or not source.feed_url:
            return []

        try:
            parsed = await asyncio.to_thread(feedparser.parse, source.feed_url)
            entries = parsed.entries or []
            inserted_articles: List[Dict] = []

            for entry in entries:
                normalized = await self._normalize_entry(entry, source)
                if not normalized:
                    continue

                article_id = await self.process_article(normalized)
                if article_id:
                    inserted_articles.append(
                        {
                            "id": article_id,
                            "title": normalized["title"],
                            "url": normalized["url"],
                            "published_at": normalized["published_at"].isoformat()
                            if normalized["published_at"]
                            else None,
                        }
                    )

            await self.source_repo.update_fetch_status(str(source.id), success=True)
            return inserted_articles
        except Exception as exc:
            await self.source_repo.update_fetch_status(
                str(source.id),
                success=False,
                error=str(exc),
            )
            return []

    async def fetch_all_feeds(self) -> Dict:
        sources = await self.source_repo.get_active_sources()
        rss_sources = [
            source
            for source in sources
            if source.source_type == "rss" and source.feed_url
        ]

        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_FETCHES)

        async def _fetch_with_limit(source: Source):
            async with semaphore:
                return await self.fetch_feed(str(source.id))

        results = await asyncio.gather(
            *(_fetch_with_limit(source) for source in rss_sources),
            return_exceptions=True,
        )

        success_sources = 0
        failed_sources = 0
        inserted_count = 0
        failures: List[Dict[str, str]] = []

        for source, result in zip(rss_sources, results):
            if isinstance(result, Exception):
                failed_sources += 1
                failures.append({"source_id": str(source.id), "error": str(result)})
                continue
            success_sources += 1
            inserted_count += len(result)

        return {
            "total_sources": len(rss_sources),
            "success_sources": success_sources,
            "failed_sources": failed_sources,
            "inserted_articles": inserted_count,
            "failures": failures,
        }

    async def crawl_hot_topics(self) -> List[Dict]:
        results: List[Dict[str, Any]] = []

        for index, platform in enumerate(self.HOT_PLATFORMS):
            if index > 0:
                await asyncio.sleep(self.HOT_PLATFORM_REQUEST_INTERVAL_SECONDS)

            platform_key = platform["key"]
            source = await self._resolve_or_create_hot_source(platform)
            if source is None:
                results.append(
                    {
                        "platform": platform_key,
                        "success": False,
                        "inserted_articles": 0,
                        "error": "source_creation_failed",
                    }
                )
                continue

            try:
                hot_items = await self._fetch_platform_hot_items(platform)
                inserted = 0
                for item in hot_items[: self.HOT_TOPIC_LIMIT_PER_PLATFORM]:
                    article_payload = self._build_hot_topic_payload(item, source, platform_key)
                    if not article_payload:
                        continue
                    article_id = await self.process_article(article_payload)
                    if article_id:
                        inserted += 1

                await self.source_repo.update_fetch_status(str(source.id), success=True)
                results.append(
                    {
                        "platform": platform_key,
                        "success": True,
                        "fetched_items": len(hot_items),
                        "inserted_articles": inserted,
                    }
                )
            except Exception as exc:
                await self.source_repo.update_fetch_status(
                    str(source.id),
                    success=False,
                    error=str(exc),
                )
                results.append(
                    {
                        "platform": platform_key,
                        "success": False,
                        "inserted_articles": 0,
                        "error": str(exc),
                    }
                )

        return results

    async def fetch_web_content(self, url: str) -> Optional[Dict[str, str]]:
        """Extract title and excerpt from a web page."""
        html = await self._fetch_html_with_retry(url)
        if not html:
            return None

        parser = HTMLParser(html)
        title_node = parser.css_first("h1") or parser.css_first("title")
        title = self._normalize_title(title_node.text() if title_node else "")

        paragraphs = parser.css("article p, main p, p")
        cleaned_paragraphs: List[tuple[int, str]] = []
        for index, node in enumerate(paragraphs):
            text = re.sub(r"\s+", " ", node.text()).strip()
            if len(text) >= 40:
                cleaned_paragraphs.append((index, text))

        if cleaned_paragraphs:
            # Keep the longest paragraph set while preserving source order.
            longest = sorted(cleaned_paragraphs, key=lambda item: len(item[1]), reverse=True)[:5]
            longest = sorted(longest, key=lambda item: item[0])
            content_excerpt = " ".join(text for _, text in longest)
        else:
            content_excerpt = ""

        content_excerpt = self._build_excerpt(content_excerpt, max_length=1200) or ""
        if not title and not content_excerpt:
            return None

        return {
            "title": title,
            "content_excerpt": content_excerpt,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
        reraise=True,
    )
    async def _fetch_html_with_retry(self, url: str) -> str:
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            response.raise_for_status()
            return response.text

    async def process_article(self, article_data: Dict) -> Optional[str]:
        duplicate_result = await self.dedup_service.check_duplicate(article_data)
        if duplicate_result["is_duplicate"] and duplicate_result.get("layer") == "url_hash":
            return None

        event_id: Optional[str] = None
        if duplicate_result["is_duplicate"]:
            event_id = await self._resolve_event_for_duplicate(duplicate_result, article_data)

        article = await self.article_repo.create(
            {
                "title": article_data["title"],
                "url": article_data["url"],
                "content": article_data.get("content"),
                "excerpt": article_data.get("excerpt"),
                "source_id": article_data["source_id"],
                "author": article_data.get("author"),
                "published_at": article_data.get("published_at"),
                "category": article_data.get("category"),
                "tags": article_data.get("tags", []),
                "event_id": event_id,
                "url_hash": article_data["url_hash"],
                "title_hash": article_data.get("title_hash"),
                "content_hash": article_data.get("content_hash"),
                "simhash": article_data.get("simhash"),
                "is_processed": False,
                "is_summary_generated": False,
                "metadata_": {
                    "ingestion_source": article_data.get("ingestion_source", "rss"),
                    "platform": article_data.get("platform"),
                    "duplicate_of": duplicate_result.get("duplicate_of"),
                    "duplicate_layer": duplicate_result.get("layer"),
                    "summary_status": "pending",
                },
            }
        )

        if self.event_repo:
            if event_id:
                await self.event_repo.update_article_count(event_id, increment=1)
                await self.event_repo.sync_source_count(event_id)
            else:
                created_event = await self._create_event_for_article(article, article_data)
                if created_event:
                    await self.article_repo.update(str(article.id), {"event_id": created_event.id})
                    await self.event_repo.sync_source_count(str(created_event.id))

        # Enqueue summary generation asynchronously; failures must not block ingestion.
        await enqueue_generate_summary_task(str(article.id))
        return str(article.id)

    async def _normalize_entry(self, entry: Any, source: Source) -> Optional[Dict]:
        raw_url = (entry.get("link") or "").strip()
        raw_title = entry.get("title") or ""
        title = self._normalize_title(raw_title)
        if not raw_url or not title:
            return None

        normalized_url = self._normalize_url(raw_url)
        content = self._extract_content(entry)
        if not content:
            fallback = await self.fetch_web_content(normalized_url)
            if fallback:
                content = fallback.get("content_excerpt", "")
                if not title and fallback.get("title"):
                    title = fallback["title"]
        excerpt = self._build_excerpt(content)
        published_at = self._parse_datetime(entry)

        return {
            "title": title,
            "url": normalized_url,
            "content": content,
            "excerpt": excerpt,
            "source_id": source.id,
            "author": (entry.get("author") or "").strip() or None,
            "published_at": published_at,
            "category": source.category,
            "tags": [],
            "url_hash": self._sha256(normalized_url),
            "title_hash": self._sha256(title.lower()),
            "content_hash": self._sha256(content.strip()) if content else None,
            "simhash": self.dedup_service.compute_simhash(content or title),
        }

    @staticmethod
    def _normalize_title(title: str) -> str:
        cleaned = re.sub(r"<[^>]+>", "", title)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _extract_content(entry: Any) -> str:
        if entry.get("content"):
            blocks = [block.get("value", "") for block in entry["content"] if block.get("value")]
            text = " ".join(blocks)
        else:
            text = entry.get("summary") or entry.get("description") or ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _build_excerpt(content: str, max_length: int = 280) -> Optional[str]:
        if not content:
            return None
        return content[:max_length]

    @staticmethod
    def _parse_datetime(entry: Any) -> Optional[datetime]:
        for key in ("published", "updated", "created"):
            value = entry.get(key)
            if not value:
                continue
            try:
                parsed = parsedate_to_datetime(value)
                if parsed.tzinfo:
                    return parsed.astimezone(timezone.utc).replace(tzinfo=None)
                return parsed
            except (TypeError, ValueError):
                continue

        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            struct_value = entry.get(key)
            if struct_value:
                return datetime(*struct_value[:6])
        return None

    @staticmethod
    def _normalize_url(url: str) -> str:
        split = urlsplit(url.strip())
        filtered_query = [
            (k, v)
            for k, v in parse_qsl(split.query, keep_blank_values=True)
            if not (
                k.lower().startswith("utm_")
                or k.lower() in {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"}
            )
        ]
        normalized_query = urlencode(sorted(filtered_query))
        return urlunsplit(
            (
                split.scheme.lower(),
                split.netloc.lower(),
                split.path.rstrip("/") or "/",
                normalized_query,
                "",
            )
        )

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    async def _resolve_or_create_hot_source(self, platform: Dict[str, str]) -> Optional[Source]:
        platform_key = platform["key"]
        source_name = platform["name"]
        existing_sources = await self.source_repo.list(
            filters={"source_type": "api"},
            limit=300,
        )
        for source in existing_sources:
            metadata = getattr(source, "metadata_", {}) or {}
            if metadata.get("platform_key") == platform_key or source.name == source_name:
                return source

        return await self.source_repo.create(
            {
                "name": source_name,
                "url": platform["source_url"],
                "source_type": "api",
                "feed_url": platform["api_url"],
                "category": "hot",
                "language": "multi",
                "is_active": True,
                "metadata_": {
                    "platform_key": platform_key,
                    "is_hot_platform": True,
                },
            }
        )

    async def _fetch_platform_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        key = platform["key"]
        if key == "hackernews":
            return await self._fetch_hackernews_hot_items(platform)
        if key == "reddit":
            return await self._fetch_reddit_hot_items(platform)
        if key == "github":
            return await self._fetch_github_hot_items(platform)
        if key == "google_trends":
            return await self._fetch_google_trends_hot_items(platform)
        if key == "product_hunt":
            return await self._fetch_product_hunt_hot_items(platform)
        if key == "weibo":
            return await self._fetch_weibo_hot_items(platform)
        if key == "zhihu":
            return await self._fetch_zhihu_hot_items(platform)
        if key == "baidu":
            return await self._fetch_baidu_hot_items(platform)
        if key == "bilibili":
            return await self._fetch_bilibili_hot_items(platform)
        return []

    @staticmethod
    def _platform_auth_headers(platform_key: str) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if platform_key == "github":
            token = os.getenv("GITHUB_TOKEN", "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif platform_key == "product_hunt":
            token = os.getenv("PRODUCT_HUNT_BEARER_TOKEN", "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _fetch_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        timeout = httpx.Timeout(30.0)
        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
        }
        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=default_headers)
            response.raise_for_status()
            return response.json()

    async def _fetch_hackernews_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        story_ids = await self._fetch_json(platform["api_url"])
        top_ids = story_ids[: self.HOT_TOPIC_LIMIT_PER_PLATFORM]
        timeout = httpx.Timeout(30.0)
        items: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            for story_id in top_ids:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                response = await client.get(item_url)
                response.raise_for_status()
                item = response.json()
                if not item or not item.get("title"):
                    continue
                published_at = datetime.utcfromtimestamp(item.get("time", 0)) if item.get("time") else None
                items.append(
                    {
                        "title": item["title"],
                        "url": item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                        "content": item.get("text") or "",
                        "published_at": published_at,
                        "score": item.get("score"),
                        "author": item.get("by"),
                    }
                )
        return items

    async def _fetch_reddit_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        payload = await self._fetch_json(
            platform["api_url"],
            headers={"User-Agent": "newsflow-bot/1.0"},
        )
        posts = payload.get("data", {}).get("children", [])
        items: List[Dict[str, Any]] = []
        for post in posts:
            data = post.get("data", {})
            permalink = data.get("permalink") or ""
            published_at = datetime.utcfromtimestamp(data["created_utc"]) if data.get("created_utc") else None
            items.append(
                {
                    "title": data.get("title", ""),
                    "url": f"https://www.reddit.com{permalink}" if permalink else data.get("url", ""),
                    "content": data.get("selftext", ""),
                    "published_at": published_at,
                    "score": data.get("score"),
                    "author": data.get("author"),
                }
            )
        return items

    async def _fetch_github_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        since_date = (datetime.utcnow() - timedelta(days=7)).date().isoformat()
        api_url = platform["api_url"].format(date=since_date)
        headers = {"Accept": "application/vnd.github+json"}
        headers.update(self._platform_auth_headers("github"))
        payload = await self._fetch_json(api_url, headers=headers)
        repos = payload.get("items", [])
        items: List[Dict[str, Any]] = []
        for repo in repos:
            items.append(
                {
                    "title": repo.get("full_name", ""),
                    "url": repo.get("html_url", ""),
                    "content": repo.get("description") or "",
                    "published_at": self._parse_iso_datetime(repo.get("updated_at")),
                    "score": repo.get("stargazers_count"),
                    "author": (repo.get("owner") or {}).get("login"),
                }
            )
        return items

    async def _fetch_google_trends_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        feed = await asyncio.to_thread(feedparser.parse, platform["api_url"])
        items: List[Dict[str, Any]] = []
        for entry in (feed.entries or []):
            link = (entry.get("link") or "").strip()
            if not link:
                continue
            items.append(
                {
                    "title": self._normalize_title(entry.get("title") or ""),
                    "url": link,
                    "content": self._extract_content(entry),
                    "published_at": self._parse_datetime(entry),
                    "author": entry.get("source"),
                }
            )
        return items

    async def _fetch_product_hunt_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        # Product Hunt currently uses public feed for compatibility;
        # when PRODUCT_HUNT_BEARER_TOKEN is set, it is retained for future API migration.
        _ = self._platform_auth_headers("product_hunt")
        feed = await asyncio.to_thread(feedparser.parse, platform["api_url"])
        items: List[Dict[str, Any]] = []
        for entry in (feed.entries or []):
            link = (entry.get("link") or "").strip()
            if not link:
                continue
            items.append(
                {
                    "title": self._normalize_title(entry.get("title") or ""),
                    "url": link,
                    "content": self._extract_content(entry),
                    "published_at": self._parse_datetime(entry),
                    "author": entry.get("author"),
                }
            )
        return items

    async def _fetch_weibo_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        payload = await self._fetch_json(platform["api_url"])
        rows = payload.get("data", {}).get("realtime", [])
        items: List[Dict[str, Any]] = []
        for row in rows:
            keyword = row.get("word") or row.get("word_scheme")
            if not keyword:
                continue
            query = keyword.replace("#", "")
            items.append(
                {
                    "title": query,
                    "url": f"https://s.weibo.com/weibo?q={query}",
                    "content": row.get("note") or "",
                    "score": row.get("num"),
                }
            )
        return items

    async def _fetch_zhihu_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        payload = await self._fetch_json(platform["api_url"])
        rows = payload.get("data", [])
        items: List[Dict[str, Any]] = []
        for row in rows:
            target = row.get("target", {})
            title = target.get("title") or row.get("detail_text")
            if not title:
                continue
            question_id = target.get("id")
            items.append(
                {
                    "title": title,
                    "url": f"https://www.zhihu.com/question/{question_id}" if question_id else "https://www.zhihu.com/hot",
                    "content": target.get("excerpt") or row.get("detail_text") or "",
                    "score": row.get("detail_text"),
                    "author": (target.get("author") or {}).get("name"),
                }
            )
        return items

    async def _fetch_baidu_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        payload = await self._fetch_json(platform["api_url"])
        content = payload.get("data", {}).get("cards", [])
        rows: List[Dict[str, Any]] = []
        for card in content:
            card_rows = card.get("content") or card.get("list") or []
            if card_rows:
                rows = card_rows
                break
        items: List[Dict[str, Any]] = []
        for row in rows:
            title = row.get("word") or row.get("query")
            if not title:
                continue
            items.append(
                {
                    "title": title,
                    "url": row.get("url") or f"https://www.baidu.com/s?wd={title}",
                    "content": row.get("desc") or "",
                    "score": row.get("hotScore") or row.get("hot_score"),
                }
            )
        return items

    async def _fetch_bilibili_hot_items(self, platform: Dict[str, str]) -> List[Dict[str, Any]]:
        payload = await self._fetch_json(platform["api_url"])
        rows = payload.get("data", {}).get("list", [])
        items: List[Dict[str, Any]] = []
        for row in rows:
            bvid = row.get("bvid")
            items.append(
                {
                    "title": row.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{bvid}" if bvid else "https://www.bilibili.com",
                    "content": row.get("desc") or "",
                    "score": row.get("stat", {}).get("view"),
                    "author": row.get("owner", {}).get("name"),
                    "published_at": datetime.utcfromtimestamp(row["pubdate"]) if row.get("pubdate") else None,
                }
            )
        return items

    def _build_hot_topic_payload(
        self,
        item: Dict[str, Any],
        source: Source,
        platform_key: str,
    ) -> Optional[Dict[str, Any]]:
        title = self._normalize_title(str(item.get("title") or ""))
        raw_url = str(item.get("url") or "").strip()
        if not title:
            return None
        if not raw_url:
            raw_url = f"https://newsflow.local/hot/{platform_key}/{uuid4().hex}"

        normalized_url = self._normalize_url(raw_url)
        content = str(item.get("content") or "").strip()
        excerpt = self._build_excerpt(content)
        published_at = item.get("published_at")
        if published_at and not isinstance(published_at, datetime):
            published_at = None
        score = item.get("score")
        score_value: Optional[float]
        try:
            score_value = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_value = None

        return {
            "title": title,
            "url": normalized_url,
            "content": content or title,
            "excerpt": excerpt,
            "source_id": source.id,
            "author": item.get("author"),
            "published_at": published_at,
            "category": "hot",
            "tags": [platform_key, "hot"],
            "url_hash": self._sha256(normalized_url),
            "title_hash": self._sha256(title.lower()),
            "content_hash": self._sha256((content or title).strip()),
            "simhash": self.dedup_service.compute_simhash(content or title),
            "relevance_score": score_value,
            "ingestion_source": "hot_platform",
            "platform": platform_key,
        }

    @staticmethod
    def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo:
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            return None

    async def _resolve_event_for_duplicate(
        self,
        duplicate_result: Dict[str, Any],
        article_data: Dict[str, Any],
    ) -> Optional[str]:
        if not self.event_repo:
            return duplicate_result.get("event_id")

        existing_event_id = duplicate_result.get("event_id")
        if existing_event_id:
            return existing_event_id

        duplicate_of = duplicate_result.get("duplicate_of")
        if not duplicate_of:
            return None
        duplicate_article = await self.article_repo.get_by_id(duplicate_of)
        if not duplicate_article:
            return None

        if duplicate_article.event_id:
            return str(duplicate_article.event_id)

        representative_hash = (
            duplicate_article.content_hash
            or article_data.get("content_hash")
            or article_data.get("simhash")
        )
        event = None
        if representative_hash:
            event = await self.event_repo.get_by_article_hash(representative_hash)

        if event is None:
            event = await self.event_repo.create(
                {
                    "title": duplicate_article.title,
                    "category": duplicate_article.category,
                    "representative_article_id": duplicate_article.id,
                    "representative_hash": representative_hash,
                    "article_count": 1,
                    "source_count": 1,
                    "first_seen_at": duplicate_article.created_at,
                    "last_updated_at": datetime.utcnow(),
                }
            )

        await self.article_repo.update(str(duplicate_article.id), {"event_id": event.id})
        return str(event.id)

    async def _create_event_for_article(self, article: Any, article_data: Dict[str, Any]):
        if not self.event_repo:
            return None
        representative_hash = article_data.get("content_hash") or article_data.get("simhash")
        event = await self.event_repo.create(
            {
                "title": article.title,
                "category": article.category,
                "representative_article_id": article.id,
                "representative_hash": representative_hash,
                "article_count": 1,
                "source_count": 1,
                "first_seen_at": article.created_at,
                "last_updated_at": datetime.utcnow(),
            }
        )
        return event
