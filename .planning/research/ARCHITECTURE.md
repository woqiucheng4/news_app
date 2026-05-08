# Architecture Research

**Domain:** AI-powered information aggregation system
**Researched:** 2026-05-08
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Flutter Mobile App                        │    │
│  │  (订阅管理 / 信息流浏览 / 推送接收 / 用户设置)                │    │
│  └────────────────────────┬────────────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────────────┘
                            │ HTTPS / REST API
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Layer                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application                       │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    │
│  │  │ Auth     │  │ Topics   │  │ Items    │  │ User     │    │    │
│  │  │ Router   │  │ Router   │  │ Router   │  │ Router   │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Service Layer (Business Logic)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Auth     │  │ Topic    │  │ Item     │  │ Notif    │            │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Ingestion Layer (Background)                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              APScheduler (via FastAPI lifespan)              │    │
│  │                                                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │    │
│  │  │ RSS Fetcher  │  │ Web Scraper  │  │ Dedup        │       │    │
│  │  │ (feedparser) │  │ (httpx+BS4)  │  │ Engine       │       │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │    │
│  │         │                 │                 │                │    │
│  │         └────────┬────────┘                 │                │    │
│  │                  ▼                          │                │    │
│  │         ┌──────────────┐                    │                │    │
│  │         │ Normalizer   │────────────────────┘                │    │
│  │         └──────┬───────┘                                     │    │
│  │                │                                             │    │
│  │                ▼                                             │    │
│  │         ┌──────────────┐                                     │    │
│  │         │ AI Summarizer│ (Claude Haiku / GPT-4o-mini)        │    │
│  │         └──────────────┘                                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    PostgreSQL + JSONB                        │    │
│  │                                                              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    │
│  │  │ users    │  │ topics   │  │ items    │  │ sources  │    │    │
│  │  │          │  │          │  │          │  │          │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Firebase Cloud Messaging                  │    │
│  │                    (Push Notification Delivery)              │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Flutter App** | 用户界面、订阅管理、信息流浏览、推送接收 | Flutter + Dart, Riverpod 状态管理 |
| **FastAPI App** | REST API、认证鉴权、业务逻辑 | Python FastAPI + Pydantic |
| **RSS Fetcher** | 定时拉取 RSS/Atom feeds | feedparser + httpx (async) |
| **Web Scraper** | 爬取无 RSS 的信息源 | httpx + BeautifulSoup4 |
| **Normalizer** | 数据清洗、格式统一、去重判定 | 自定义 Python 模块 |
| **Dedup Engine** | 精确去重 + 近似去重 | SHA-256 哈希 + SimHash/TF-IDF |
| **AI Summarizer** | 生成内容摘要 | Claude Haiku / GPT-4o-mini API |
| **Notification Service** | 推送通知管理 | Firebase Admin SDK |
| **APScheduler** | 后台定时任务调度 | APScheduler 4.x + FastAPI lifespan |
| **PostgreSQL** | 结构化数据 + JSONB 存储 | PostgreSQL 15+ (Supabase/Neon free tier) |

## Recommended Project Structure

```
newflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app + lifespan (scheduler init)
│   │   ├── config.py               # 环境变量、配置管理
│   │   ├── database.py             # SQLAlchemy async engine + session
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── topic.py            # 话题/订阅模型
│   │   │   ├── item.py             # 信息条目模型
│   │   │   └── source.py           # 信息源模型
│   │   │
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── topic.py
│   │   │   └── item.py
│   │   │
│   │   ├── routers/                # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # 认证 (邮箱/Google/Apple)
│   │   │   ├── topics.py           # 话题 CRUD
│   │   │   ├── items.py            # 信息条目查询
│   │   │   └── users.py            # 用户设置
│   │   │
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # 认证逻辑
│   │   │   ├── topic.py            # 话题管理
│   │   │   ├── item.py             # 条目查询/过滤
│   │   │   └── notification.py     # 推送通知
│   │   │
│   │   ├── ingestion/              # 信息采集层 (后台任务)
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py        # APScheduler 配置
│   │   │   ├── rss_fetcher.py      # RSS/Atom 拉取
│   │   │   ├── web_scraper.py      # 网页爬虫
│   │   │   ├── normalizer.py       # 数据标准化
│   │   │   ├── dedup.py            # 去重引擎
│   │   │   └── summarizer.py       # AI 摘要生成
│   │   │
│   │   └── utils/                  # 工具函数
│   │       ├── __init__.py
│   │       ├── hash.py             # 哈希/指纹计算
│   │       └── text.py             # 文本处理工具
│   │
│   ├── alembic/                    # 数据库迁移
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
└── mobile/
    ├── lib/
    │   ├── main.dart
    │   ├── app/                    # App 配置、路由
    │   ├── models/                 # 数据模型
    │   ├── providers/              # Riverpod 状态管理
    │   ├── screens/                # 页面
    │   ├── widgets/                # 组件
    │   └── services/               # API 调用、推送服务
    ├── pubspec.yaml
    └── ...
```

### Structure Rationale

- **`ingestion/` 独立于 `services/`:** 信息采集是后台任务，与用户请求的业务逻辑分离，便于独立开发和测试
- **`models/` 和 `schemas/` 分离:** ORM 模型负责数据库映射，Pydantic 模型负责 API 验证，职责清晰
- **`routers/` 极薄:** 路由层只做请求分发，业务逻辑全部下沉到 `services/`
- **单体架构:** 独立开发者 + $50 预算，微服务过度工程化，单体足够支撑初期

## Architectural Patterns

### Pattern 1: FastAPI Lifespan + APScheduler 集成

**What:** 使用 FastAPI 的 lifespan 上下文管理器初始化和管理 APScheduler，实现后台定时任务
**When to use:** 需要定时执行后台任务（如 RSS 拉取、摘要生成）的场景
**Trade-offs:**
- 优点：单进程运行，无需额外的消息队列（Redis/RabbitMQ），降低运维成本
- 缺点：单点故障，进程重启会丢失调度状态（可通过持久化 data store 缓解）

**Example:**
```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.interval import IntervalTrigger

scheduler: AsyncScheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global scheduler
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
    data_store = SQLAlchemyDataStore(engine)
    scheduler = AsyncScheduler(data_store)

    async with scheduler:
        # RSS 拉取任务：每 15 分钟
        await scheduler.add_schedule(
            "app.ingestion.rss_fetcher.fetch_all_feeds",
            IntervalTrigger(minutes=15),
            id="rss_fetch",
            conflict_policy=ConflictPolicy.replace,
        )
        # AI 摘要任务：每 5 分钟处理待摘要队列
        await scheduler.add_schedule(
            "app.ingestion.summarizer.process_pending",
            IntervalTrigger(minutes=5),
            id="summarize_pending",
            conflict_policy=ConflictPolicy.replace,
        )
        await scheduler.start_in_background()
        yield

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: RSS 优先 + 爬虫补充的双通道采集

**What:** 信息采集分两个通道——RSS 通道（标准化、稳定）和爬虫通道（覆盖无 RSS 的源）
**When to use:** 需要覆盖多种信息源（新闻网站、社交平台、垂直数据源）的场景
**Trade-offs:**
- 优点：RSS 通道高可靠、低维护；爬虫通道覆盖面广
- 缺点：爬虫通道需要处理反爬、页面结构变化等

**Example:**
```python
# app/ingestion/rss_fetcher.py
import httpx
import feedparser
from datetime import datetime

async def fetch_feed(source_url: str) -> list[dict]:
    """拉取并解析单个 RSS feed"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(source_url)
        feed = feedparser.parse(response.text)

    items = []
    for entry in feed.entries:
        items.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published_parsed"),
            "source_id": entry.get("id", entry.get("link", "")),
        })
    return items

# app/ingestion/web_scraper.py
async def scrape_url(url: str) -> dict:
    """爬取无 RSS 的网页内容"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, follow_redirects=True)
    soup = BeautifulSoup(response.text, "html.parser")
    # 提取标题、正文、发布时间等
    return {"title": ..., "content": ..., "published": ...}
```

### Pattern 3: 分层去重策略

**What:** 采用三层去重——GUID/URL 精确去重、内容哈希去重、SimHash 近似去重
**When to use:** 多源信息聚合场景，同一新闻可能被多个源转载
**Trade-offs:**
- 优点：逐层递进，精确去重快速（O(1)），近似去重处理转载/改写
- 缺点：SimHash 需要额外计算，初期可只用前两层

**Example:**
```python
# app/ingestion/dedup.py
import hashlib

class DedupEngine:
    def __init__(self, db_session):
        self.db = db_session

    async def is_duplicate(self, item: dict) -> bool:
        """三层去重判定"""
        # Layer 1: GUID/URL 精确匹配
        if await self._exact_match(item.get("source_id") or item["link"]):
            return True

        # Layer 2: 内容哈希匹配
        content_hash = self._compute_hash(item["title"] + item.get("summary", ""))
        if await self._hash_match(content_hash):
            return True

        # Layer 3: SimHash 近似匹配 (v2 实现，初期可跳过)
        # if await self._simhash_match(item["summary"]):
        #     return True

        return False

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()
```

### Pattern 4: AI 摘要异步队列

**What:** 新条目入库后标记为"待摘要"，由后台定时任务批量调用 AI API 生成摘要
**When to use:** AI API 调用有延迟和成本，不适合在入库时同步调用
**Trade-offs:**
- 优点：批量处理降低成本、避免 API 限流、失败可重试
- 缺点：用户看到新条目时可能还没有摘要（可用"摘要生成中"状态过渡）

**Example:**
```python
# app/ingestion/summarizer.py
import anthropic

async def process_pending():
    """处理所有待摘要的条目"""
    pending_items = await get_items_by_status("pending_summary")
    for item in pending_items[:20]:  # 批量处理，每批最多 20 条
        try:
            summary = await generate_summary(item["title"], item["content"])
            await update_item_summary(item["id"], summary)
        except Exception as e:
            await mark_summary_failed(item["id"], str(e))

async def generate_summary(title: str, content: str) -> str:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-haiku-3",  # 小模型，成本低
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"请用 2-3 句话总结以下新闻内容，保持客观中立：\n\n标题：{title}\n\n内容：{content[:2000]}"
        }]
    )
    return response.content[0].text
```

### Pattern 5: FCM 主题推送

**What:** 使用 Firebase Cloud Messaging 的主题（Topic）功能，用户订阅话题时自动订阅对应 FCM 主题
**When to use:** 需要按话题推送通知，而非按用户逐一推送
**Trade-offs:**
- 优点：FCM 免费、主题推送自动管理订阅关系、无需维护设备 token 映射
- 缺点：主题数量有上限（约 2000 万）、无法精确控制每个用户的推送时间

**Example:**
```python
# app/services/notification.py
from firebase_admin import messaging

async def push_topic_update(topic_id: str, title: str, body: str):
    """向订阅了某个话题的所有用户推送通知"""
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        topic=f"topic_{topic_id}",
        android=messaging.AndroidConfig(priority="normal"),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(aps=messaging.Aps(badge=1))
        ),
    )
    messaging.send(message)

async def push_daily_digest(user_token: str, summaries: list[str]):
    """每日定时摘要推送到单个设备"""
    body = "\n".join(summaries[:5])  # 最多 5 条
    message = messaging.Message(
        notification=messaging.Notification(title="今日摘要", body=body),
        token=user_token,
    )
    messaging.send(message)
```

## Data Flow

### 信息采集流 (Ingestion Flow)

```
信息源 (RSS/网站)
    │
    ▼
┌─────────────┐
│ RSS Fetcher │ ← APScheduler 每 15 分钟触发
│ / Scraper   │
└──────┬──────┘
       │ raw items
       ▼
┌─────────────┐
│ Normalizer  │ ← 统一格式、提取字段、解析时间
└──────┬──────┘
       │ normalized items
       ▼
┌─────────────┐
│ Dedup       │ ← GUID/URL → 内容哈希 → SimHash
│ Engine      │
└──────┬──────┘
       │ unique items only
       ▼
┌─────────────┐
│ PostgreSQL  │ ← 写入 items 表，status="pending_summary"
└──────┬──────┘
       │
       ▼ (async, separate schedule)
┌─────────────┐
│ AI          │ ← APScheduler 每 5 分钟触发
│ Summarizer  │
└──────┬──────┘
       │ summary text
       ▼
┌─────────────┐
│ PostgreSQL  │ ← 更新 items.summary，status="ready"
└──────┬──────┘
       │
       ▼ (if "重大更新" or "突发")
┌─────────────┐
│ FCM Push    │ ← 推送给订阅该话题的用户
└─────────────┘
```

### 用户请求流 (API Request Flow)

```
Flutter App
    │
    ▼ (HTTPS REST)
┌─────────────┐
│ FastAPI     │
│ Router      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Service     │ ← 业务逻辑、权限检查
│ Layer       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │ ← 查询 items/topics/users
└─────────────┘
       │
       ▼
JSON Response → Flutter App
```

### 关键数据流

1. **RSS 采集流:** Scheduler → RSS Fetcher → Normalizer → Dedup → DB (15min 周期)
2. **AI 摘要流:** DB (pending) → Summarizer → DB (ready) → Push (5min 周期)
3. **用户订阅流:** App → API → Topic Service → DB + FCM Topic Subscribe
4. **信息浏览流:** App → API → Item Service → DB → App (pull, 分页加载)
5. **推送通知流:** DB (new items) → Notif Service → FCM → App

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 用户 | 单进程 FastAPI + APScheduler 足够，数据库用 Supabase/Neon 免费层 |
| 100-1k 用户 | 考虑将 APScheduler 持久化到 PostgreSQL（多实例协调），增加数据库连接池 |
| 1k-10k 用户 | 拆分 ingestion 为独立 worker 进程，使用 Redis 做任务队列 |
| 10k+ 用户 | 考虑 CDN 缓存 API 响应、读写分离、分库分表 |

### Scaling Priorities

1. **First bottleneck:** AI API 调用成本和延迟（$50 预算限制）→ 批量处理 + 小模型 + 缓存已摘要内容
2. **Second bottleneck:** 数据库连接数（PostgreSQL 默认 100）→ 连接池配置 + 查询优化
3. **Third bottleneck:** RSS 拉取并发数（大量源同时拉取）→ 分批调度 + 限速

## Anti-Patterns

### Anti-Pattern 1: 同步调用 AI API

**What people do:** 在 RSS 采集入库时同步调用 AI 生成摘要
**Why it's wrong:** AI API 调用延迟高（1-5s），阻塞采集流水线；API 限流导致采集失败
**Do this instead:** 先入库标记 status="pending_summary"，后台定时批量调用 AI，失败可重试

### Anti-Pattern 2: 缓存全文内容

**What people do:** 将爬取的全文内容存入数据库供用户阅读
**Why it's wrong:** 版权风险（尤其海外）、存储成本高、法律合规问题
**Do this instead:** 只存储摘要 + 原文链接，用户点击跳转到原网站阅读

### Anti-Pattern 3: 每个用户单独推送

**What people do:** 遍历所有用户，逐一发送推送通知
**Why it's wrong:** 用户量增长后推送时间线性增加、API 调用量爆炸
**Do this instead:** 使用 FCM 主题推送（Topic Push），用户订阅话题时自动加入 FCM 主题

### Anti-Pattern 4: 微服务架构

**What people do:** 独立开发者一开始就拆分微服务（API 服务、采集服务、通知服务...）
**Why it's wrong:** 运维复杂度爆炸、部署成本高、独立开发者难以维护
**Do this instead:** 单体 FastAPI 应用 + APScheduler，需要时再拆分独立 worker

### Anti-Pattern 5: 过度设计去重系统

**What people do:** 一开始就实现 SimHash/MinHash + 向量相似度等复杂去重
**Why it's wrong:** 初期数据量小，精确去重（GUID/URL + 内容哈希）足够
**Do this instead:** 先实现 GUID/URL + SHA-256 哈希去重，数据量增长后再加 SimHash

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Claude Haiku API** | REST API (async httpx) | 成本控制：$0.25/1M input tokens，优先用小模型 |
| **GPT-4o-mini API** | REST API (async httpx) | 备选方案，价格相近 |
| **Firebase Cloud Messaging** | firebase-admin SDK | 免费，无限推送，需配置 service account |
| **Supabase/Neon** | PostgreSQL 连接 | 免费层：500MB/1GB 存储，足够初期 |
| **Google OAuth** | OAuth 2.0 | 用于 Google 登录 |
| **Sign in with Apple** | OAuth 2.0 | 用于 Apple 登录 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Routers ↔ Services** | 函数调用 | 路由层极薄，只做请求分发和响应格式化 |
| **Services ↔ Models** | SQLAlchemy async session | 通过依赖注入传递 session |
| **Ingestion ↔ Services** | 共享 models 层 | 采集层直接操作 ORM 模型，不经过 service 层 |
| **Ingestion ↔ AI API** | HTTP 请求 | 异步 httpx 调用，带重试和超时 |
| **Services ↔ FCM** | firebase-admin SDK | 同步 SDK，通过 BackgroundTasks 异步执行 |

## Build Order Implications

基于组件依赖关系，建议的构建顺序：

```
Phase 1: Foundation
├── PostgreSQL schema (users, topics, items, sources)
├── FastAPI app skeleton + config
└── Auth (邮箱注册登录)

Phase 2: Ingestion Core
├── RSS Fetcher (feedparser + httpx)
├── Normalizer
├── Basic Dedup (GUID/URL + hash)
└── APScheduler integration

Phase 3: AI + Content
├── AI Summarizer (Claude Haiku)
├── Item API (查询、分页)
└── Topic CRUD API

Phase 4: Mobile App
├── Flutter app skeleton
├── Topic subscription UI
├── Feed browsing UI
└── API integration

Phase 5: Push + Polish
├── FCM integration (Flutter + backend)
├── Push notification logic
├── Daily digest
└── Content moderation
```

**依赖关系：**
- Phase 2 依赖 Phase 1（需要数据库和 app 骨架）
- Phase 3 依赖 Phase 2（需要采集到的数据来测试摘要）
- Phase 4 可与 Phase 3 并行（API 定义好即可开始移动端开发）
- Phase 5 依赖 Phase 4（需要 Flutter 端处理推送）

## Sources

- FastAPI Official Documentation - Lifespan Events: https://fastapi.tiangolo.com/advanced/events/
- FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- APScheduler 4.x Documentation: https://apscheduler.readthedocs.io/
- Feedparser Documentation: https://feedparser.readthedocs.io/
- Firebase Admin Python SDK - FCM: https://firebase.google.com/docs/cloud-messaging
- HTTPX Async Client: https://www.python-httpx.org/

---
*Architecture research for: AI-powered information aggregation system*
*Researched: 2026-05-08*
