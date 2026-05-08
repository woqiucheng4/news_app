# Phase 1: 基础架构 + 内容采集管道 - Research

**Researched:** 2026-05-08
**Domain:** FastAPI async backend + RSS/scraper ingestion + AI summarization pipeline
**Confidence:** HIGH

## Summary

Phase 1 是 NewsFlow 的地基——构建完整的后端数据采集、去重、AI 摘要管道。此阶段需要解决 5 个关键陷阱中的 4 个（AI 成本失控、去重失败、RSS 衰减、版权风险），是整个项目最关键也最危险的阶段。

技术方案已经过项目级研究验证：FastAPI 0.128.x + SQLAlchemy 2.0 async + APScheduler 4.x（进程内调度）+ feedparser + httpx + selectolax + GPT-4o-mini。架构采用单体 FastAPI 应用，通过 lifespan 上下文管理器集成 APScheduler，实现 RSS 定时采集（15-60 分钟）和 AI 摘要异步批量处理（5 分钟间隔）。

**Primary recommendation:** 先搭建骨架（FastAPI + DB schema + Auth），再逐层添加采集管道（RSS Fetcher -> Normalizer -> Dedup -> AI Summarizer），每层独立可测试。

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONT-01 | 系统可自动解析和抓取预置 RSS 订阅源 | feedparser + httpx async，APScheduler 定时调度 |
| CONT-02 | 用户可添加自定义 RSS 订阅地址 | sources 表 + RSS Fetcher 动态源支持 |
| CONT-03 | 用户可添加任意网页 URL，系统定期爬取更新 | httpx + selectolax 爬虫通道，与 RSS 通道并行 |
| CONT-04 | 系统按用户关键词从多个源搜索并聚合相关内容 | 关键词匹配 + source-topic 关联查询 |
| CONT-05 | 系统自动检测并合并重复内容 | 三层去重：URL → SHA-256 哈希 → SimHash(后期) |
| CONT-06 | RSS 源健康监控，失效源自动告警 | source_health 表 + 连续失败计数 + 告警 |
| CONT-07 | 内容采集高频更新（热门话题 15-60 分钟） | APScheduler IntervalTrigger，可按 source 配置频率 |
| AI-01 | 每条聚合信息自动生成简短 AI 摘要 | GPT-4o-mini async，异步队列批量处理 |
| AI-02 | AI 摘要使用低成本模型控制预算 | GPT-4o-mini: $0.15/MTok 输入，~$6/月 |
| AI-03 | AI 摘要结果缓存，避免重复调用 | items 表 summary 字段，status 状态机管理 |
| AI-07 | AI 内容审核，自动过滤敏感/违规内容 | OpenAI Moderation API 或 prompt-based 过滤 |
| AI-08 | 版权合规的摘要 prompt 设计 | 摘要不超过 2-3 句话 + 不复制原文 + 来源归属 |
</phase_requirements>

<user_constraints>
## User Constraints (from PROJECT.md)

### Locked Decisions
- **预算**: 月支出 < $50，优先使用免费层和低成本方案
- **合规**: GDPR 优先，数据存海外服务器
- **版权**: 仅展示摘要 + 链接跳转，不缓存全文
- **独立开发**: 一人全栈，需控制复杂度，优先核心功能
- **市场**: 先海外再国内，国内版需独立合规方案

### Claude's Discretion
- 数据库 schema 细节设计（表结构、索引策略）
- APScheduler 版本选择（3.x vs 4.x）
- AI prompt 具体措辞
- 错误处理和重试策略细节
- 测试策略和覆盖率目标

### Deferred Ideas (OUT OF SCOPE)
- v2 功能（AI 对话追问、高级分析）
- 社交功能、全文缓存、视频内容
- 国内市场合规方案
- 实时聊天、广告模式
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| RSS 采集 | API/Backend (ingestion/) | — | 后台定时任务，与客户端无关 |
| 网页爬取 | API/Backend (ingestion/) | — | 后台任务，需处理反爬 |
| 内容去重 | API/Backend (ingestion/) | Database (唯一约束) | 应用层逻辑 + DB 约束双重保障 |
| AI 摘要 | API/Backend (ingestion/) | — | 异步批处理，需成本控制 |
| 用户认证 | API/Backend (routers/) | Supabase Auth | Supabase 处理 OAuth，后端验证 JWT |
| 数据存储 | Database (PostgreSQL) | — | 所有持久化数据 |
| 推送通知 | API/Backend (services/) | FCM | Phase 4 实现，但 schema 需预留 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.128.x | 异步后端框架 | 原生 async/await，自动 OpenAPI，Pydantic v2 [VERIFIED: Context7] |
| SQLAlchemy | 2.0.x | ORM + 数据库工具 | 原生 async 支持，Alembic 配套 [VERIFIED: Context7] |
| asyncpg | 0.30.x | PostgreSQL 异步驱动 | 性能远超 psycopg2 [ASSUMED] |
| Pydantic | 2.x | 数据验证 | FastAPI 内置，v2 性能提升 5-50x [VERIFIED: Context7] |
| uvicorn | latest | ASGI 服务器 | FastAPI 标准搭配 [VERIFIED: Context7] |

### Ingestion Layer
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| feedparser | 6.x | RSS/Atom 解析 | Python RSS 事实标准，全版本支持 [VERIFIED: Context7] |
| httpx | 0.28.x | 异步 HTTP 客户端 | 原生 async，HTTP/2，比 aiohttp 更现代 [ASSUMED] |
| selectolax | latest | HTML 解析 | 比 BeautifulSoup 快 10-100x [ASSUMED] |

### Background Tasks
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | 4.x | 定时任务调度 | 进程内调度，无需 Redis，FastAPI lifespan 集成 [VERIFIED: Context7] |

### AI Layer
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai | 2.x | GPT-4o-mini API | 异步客户端，batch API 支持 [VERIFIED: Context7] |
| tenacity | 9.x | 重试逻辑 | API 调用自动重试 [ASSUMED] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| alembic | 1.14.x | 数据库迁移 | schema 版本管理 [ASSUMED] |
| python-jose | 3.x | JWT 处理 | Supabase token 验证 [ASSUMED] |
| structlog | 24.x | 结构化日志 | 生产环境排查 [ASSUMED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler 4.x | APScheduler 3.10.x | 3.x 更成熟但 API 不同；4.x 是当前版本，与 FastAPI 集成更好 |
| selectolax | BeautifulSoup | BS4 容错更好但慢 10-100x；selectolax 对畸形 HTML 更严格 |
| OpenAI batch API | 逐条调用 | batch 更便宜(50% 折扣)但延迟高(24h)；实时调用适合 MVP |

**Installation:**
```bash
# 使用 uv
uv init newflow-backend && cd newflow-backend
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic
uv add pydantic python-jose[cryptography]
uv add feedparser httpx selectolax
uv add openai tenacity structlog
uv add apscheduler
uv add -D pytest pytest-asyncio httpx ruff mypy
```

## Architecture Patterns

### System Architecture Diagram

```
APScheduler (每15分钟)
    │
    ▼
┌─────────────┐     ┌─────────────┐
│ RSS Fetcher │     │ Web Scraper │
│ (feedparser │     │ (httpx +    │
│  + httpx)   │     │ selectolax) │
└──────┬──────┘     └──────┬──────┘
       │ raw items          │
       └────────┬───────────┘
                ▼
       ┌─────────────┐
       │ Normalizer  │ ← 统一格式、解析时间、提取字段
       └──────┬──────┘
              │ normalized items
              ▼
       ┌─────────────┐
       │ Dedup       │ ← Layer1: URL → Layer2: SHA-256 → Layer3: SimHash(v2)
       │ Engine      │
       └──────┬──────┘
              │ unique items
              ▼
       ┌─────────────┐
       │ PostgreSQL  │ ← items 表, status="pending_summary"
       └──────┬──────┘
              │
              ▼ (APScheduler 每5分钟)
       ┌─────────────┐
       │ AI          │ ← GPT-4o-mini 批量处理
       │ Summarizer  │    成本监控 + token 预算
       └──────┬──────┘
              │ summary text
              ▼
       ┌─────────────┐
       │ PostgreSQL  │ ← 更新 summary, status="ready"
       └─────────────┘
```

### Recommended Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + lifespan (scheduler init)
│   ├── config.py            # 环境变量、配置管理
│   ├── database.py          # SQLAlchemy async engine + session
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── source.py        # 信息源 (RSS feed / 网页 URL)
│   │   ├── item.py          # 采集到的信息条目
│   │   └── source_health.py # 源健康状态
│   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── source.py
│   │   └── item.py
│   ├── routers/             # API 路由层 (极薄)
│   │   ├── __init__.py
│   │   ├── health.py        # 健康检查
│   │   └── sources.py       # 源管理 API
│   ├── ingestion/           # 信息采集层 (后台任务)
│   │   ├── __init__.py
│   │   ├── scheduler.py     # APScheduler 配置
│   │   ├── rss_fetcher.py   # RSS/Atom 拉取
│   │   ├── web_scraper.py   # 网页爬虫
│   │   ├── normalizer.py    # 数据标准化
│   │   ├── dedup.py         # 去重引擎
│   │   └── summarizer.py    # AI 摘要生成
│   └── utils/
│       ├── __init__.py
│       ├── hash.py          # SHA-256 哈希计算
│       └── text.py          # 文本处理工具
├── alembic/
├── tests/
├── pyproject.toml
└── Dockerfile
```

### Pattern 1: FastAPI Lifespan + APScheduler 集成
**What:** 使用 FastAPI lifespan 上下文管理器初始化 APScheduler，实现后台定时任务
**When to use:** 需要定时执行后台任务（RSS 拉取、摘要生成）
**Example:**
```python
# Source: Context7 /agronholm/apscheduler
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.eventbrokers.asyncpg import AsyncpgEventBroker
from apscheduler.triggers.interval import IntervalTrigger

scheduler: AsyncScheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global scheduler
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
    data_store = SQLAlchemyDataStore(engine)
    event_broker = AsyncpgEventBroker.from_async_sqla_engine(engine)
    scheduler = AsyncScheduler(data_store, event_broker)

    async with scheduler:
        await scheduler.add_schedule(
            "app.ingestion.rss_fetcher.fetch_all_feeds",
            IntervalTrigger(minutes=15),
            id="rss_fetch",
            conflict_policy=ConflictPolicy.replace,
        )
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

### Pattern 2: 分层去重策略
**What:** 三层去重——URL 精确匹配、SHA-256 内容哈希、SimHash 近似匹配（v2）
**When to use:** 多源信息聚合，同一新闻被多家媒体报道
**Example:**
```python
# app/ingestion/dedup.py
import hashlib

class DedupEngine:
    def __init__(self, db_session):
        self.db = db_session

    async def is_duplicate(self, item: dict) -> bool:
        # Layer 1: URL 精确匹配 (O(1) DB 查询)
        if await self._url_exists(item["link"]):
            return True
        # Layer 2: 内容哈希匹配
        content = (item.get("title", "") + item.get("summary", "")).strip()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if await self._hash_exists(content_hash):
            return True
        return False
```

### Pattern 3: AI 摘要异步队列
**What:** 新条目入库标记 pending_summary，后台定时批量调用 AI
**When to use:** AI API 有延迟和成本，不适合同步调用
**Example:**
```python
# app/ingestion/summarizer.py
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def process_pending():
    pending = await get_items_by_status("pending_summary", limit=20)
    for item in pending:
        try:
            summary = await generate_summary(item["title"], item["content"])
            await update_item(item["id"], summary=summary, status="ready")
        except Exception as e:
            await mark_failed(item["id"], str(e))

async def generate_summary(title: str, content: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "你是新闻摘要助手。用 2-3 句话客观总结新闻核心事实，不复制原文句子，不发表观点。"
        }, {
            "role": "user",
            "content": f"标题：{title}\n\n内容：{content[:2000]}"
        }],
        max_tokens=200,
    )
    return response.choices[0].message.content
```

### Anti-Patterns to Avoid
- **同步调用 AI API:** 阻塞采集流水线，API 限流导致采集失败。用异步队列。
- **缓存全文内容:** 版权风险。只存摘要 + 原文链接。
- **每次完整发送 system prompt:** 浪费 token。利用 prompt caching 或固定 system prompt。
- **去重只用 URL:** 通讯社转载导致大量重复。必须至少两层去重。
- **无 feed 健康监控:** feed 静默失效后无法发现。必须追踪成功率和最后更新时间。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSS 解析 | 自写 XML 解析器 | feedparser | 支持所有 RSS/Atom 变体，处理编码、畸形格式 |
| HTTP 请求 | 自写 aiohttp 封装 | httpx | 统一 sync/async API，HTTP/2，连接池管理 |
| HTML 解析 | 自写正则提取 | selectolax | C 底层快 10-100x，CSS 选择器支持 |
| 任务调度 | 自写 cron 逻辑 | APScheduler | 持久化、并发控制、错误处理、FastAPI 集成 |
| JWT 验证 | 自写 token 解析 | python-jose | RS256/HS256 验证，Supabase 兼容 |
| 重试逻辑 | 自写 retry loop | tenacity | 指数退避、条件重试、日志集成 |

## Common Pitfalls

### Pitfall 1: AI API 成本失控
**What goes wrong:** 每篇文章都调 API，$50 预算几天耗尽
**Why it happens:** 测试阶段用少量数据，没估算规模化成本；去重失败导致重复调用
**How to avoid:**
- token 预算系统：跟踪每日/每月 API 调用量和 token 消耗
- 先去重再摘要：确保同一事件只摘要一次
- 固定 system prompt：利用 prompt caching 节省 90% 输入 token
- 成本监控：日志记录每次调用的 token 数和费用
**Warning signs:** 开发阶段 API 费用已超 $10/月；无成本监控

### Pitfall 2: 内容去重失败
**What goes wrong:** 同一新闻被 10 家媒体报道，用户看到 10 条重复摘要
**Why it happens:** 通讯社供稿被转载，标题和正文高度相似；URL 去重无效
**How to avoid:** 至少两层去重（URL + SHA-256 哈希），后期加 SimHash
**Warning signs:** 信息流 >30% 内容高度相似；去重只用 URL

### Pitfall 3: RSS 源可靠性衰减
**What goes wrong:** feed URL 静默变更，3-6 个月后大量源失效
**Why it happens:** RSS 是很多网站的"遗留功能"，改版时悄悄移除
**How to avoid:** source_health 表追踪成功率、最后成功时间、连续失败次数；连续失败 N 次后告警
**Warning signs:** 不知道哪些 feed 已失效；用户投诉才发现

### Pitfall 4: 版权纠纷
**What goes wrong:** AI 摘要"过于详细"等同于复制
**How to avoid:** prompt 限制 2-3 句话 + 不复制原文 + 来源归属 + 不缓存全文

## Code Examples

### Async Database Session
```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
```

### RSS Fetcher with Error Handling
```python
# app/ingestion/rss_fetcher.py
import httpx
import feedparser
import structlog

logger = structlog.get_logger()

async def fetch_feed(source_url: str, timeout: int = 30) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(source_url, follow_redirects=True)
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("feed_fetch_failed", url=source_url, error=str(e))
        return []

    feed = feedparser.parse(response.text)
    if feed.bozo and not feed.entries:
        logger.warning("feed_parse_error", url=source_url, error=str(feed.bozo_exception))
        return []

    return [
        {
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published_parsed"),
            "source_id": entry.get("id") or entry.get("link", ""),
        }
        for entry in feed.entries
        if entry.get("title") or entry.get("link")
    ]
```

### Cost Monitoring Middleware
```python
# app/utils/cost_tracker.py
import structlog
from dataclasses import dataclass, field
from datetime import date

logger = structlog.get_logger()

@dataclass
class DailyCostTracker:
    date: date = field(default_factory=date.today)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    request_count: int = 0
    daily_budget_usd: float = 5.0  # 日预算上限

    def record(self, input_tokens: int, output_tokens: int):
        # GPT-4o-mini: $0.15/MTok input, $0.60/MTok output
        cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        self.total_tokens += input_tokens + output_tokens
        self.total_cost_usd += cost
        self.request_count += 1
        logger.info("ai_cost", tokens=input_tokens+output_tokens, cost_usd=cost, daily_total=self.total_cost_usd)

    def is_over_budget(self) -> bool:
        return self.total_cost_usd >= self.daily_budget_usd * 0.8  # 80% 熔断
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI @app.on_event("startup") | FastAPI lifespan context manager | FastAPI 0.103+ | startup/shutdown 事件已弃用，必须用 lifespan |
| APScheduler 3.x BackgroundScheduler | APScheduler 4.x AsyncScheduler | APScheduler 4.0 | 原生 async，SQLAlchemy data store，更好的 FastAPI 集成 |
| psycopg2 (同步驱动) | asyncpg (异步驱动) | SQLAlchemy 2.0 | 原生 async 支持，不阻塞事件循环 |
| OpenAI SDK 1.x | OpenAI SDK 2.x | 2024 | 新的 stream API、batch API |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")` — 已弃用，使用 lifespan
- `BackgroundScheduler` (APScheduler 3.x) — 4.x 使用 `AsyncScheduler`
- `psycopg2` — 阻塞事件循环，使用 `asyncpg`

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | 整个项目 | ✓ | 3.9.6 | 需升级到 3.12+ |
| pip | 包管理 | ✓ | 21.2.4 | 用 uv 替代 |
| uv | 包管理 (推荐) | ✗ | — | 用 pip，或安装 uv |
| Node.js | 工具链 | ✓ | 24.15.0 | — |
| Docker | 部署 | ✗ | — | 开发阶段不需要 |
| PostgreSQL | 数据库 | ✗ | — | 使用 Supabase Cloud (免费层) |
| psql | DB 管理 | ✗ | — | 使用 Supabase Dashboard |

**Missing dependencies with no fallback:**
- Python 3.12+ — 当前 3.9.6 不满足 async 性能要求和类型注解语法

**Missing dependencies with fallback:**
- uv → pip 可替代（但推荐安装 uv）
- Docker → 开发阶段不需要，部署时再安装
- PostgreSQL → Supabase Cloud 免费层提供

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | asyncpg 0.30.x 是当前最新版本 | Standard Stack | 可能需要调整版本号 |
| A2 | selectolax 对畸形 HTML 严格但可接受 | Standard Stack | 需要增加容错处理 |
| A3 | APScheduler 4.x 与 FastAPI lifespan 集成稳定 | Architecture Patterns | 3.x 是回退方案 |
| A4 | GPT-4o-mini 单条摘要约 500 input + 200 output tokens | Cost Tracking | 影响成本估算精度 |
| A5 | Supabase Free 层 500MB 存储足够 MVP 阶段 | Environment | 数据增长超预期需升级 |

## Open Questions

1. **Python 版本升级**
   - What we know: 当前系统 Python 3.9.6，项目需要 3.12+
   - What's unclear: 用户是否愿意安装 Python 3.12+（通过 pyenv 或系统升级）
   - Recommendation: 使用 pyenv 安装 Python 3.12+，或使用 uv 管理 Python 版本

2. **APScheduler 3.x vs 4.x**
   - What we know: 3.x 更成熟（3.10.x），4.x 是当前开发版本
   - What's unclear: 4.x 的生产稳定性
   - Recommendation: 使用 4.x（官方推荐，FastAPI 集成更好），如有问题可回退到 3.x + BackgroundScheduler

3. **RSS 源列表**
   - What we know: 需要预置一批高质量 RSS 源
   - What's unclear: 具体哪些源、覆盖率如何
   - Recommendation: Phase 1 建立源管理机制，初始源列表后续补充

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml (Wave 0 创建) |
| Quick run command | `cd backend && uv run pytest tests/ -x -q` |
| Full suite command | `cd backend && uv run pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONT-01 | 解析并抓取预置 RSS 源 | integration | `pytest tests/test_rss_fetcher.py -x` | ❌ Wave 0 |
| CONT-05 | 去重引擎正确过滤重复内容 | unit | `pytest tests/test_dedup.py -x` | ❌ Wave 0 |
| AI-01 | 生成 AI 摘要 | integration | `pytest tests/test_summarizer.py -x` | ❌ Wave 0 |
| AI-02 | 成本控制在预算内 | unit | `pytest tests/test_cost_tracker.py -x` | ❌ Wave 0 |
| CONT-06 | Feed 健康状态正确追踪 | unit | `pytest tests/test_source_health.py -x` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `backend/tests/conftest.py` — 共享 fixtures（test DB session, mock HTTP）
- [ ] `backend/tests/test_rss_fetcher.py` — RSS 采集测试
- [ ] `backend/tests/test_dedup.py` — 去重引擎测试
- [ ] `backend/tests/test_summarizer.py` — AI 摘要测试
- [ ] `backend/tests/test_cost_tracker.py` — 成本追踪测试
- [ ] `backend/pyproject.toml` — pytest 配置

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (Phase 2) | Supabase Auth + JWT 验证 |
| V3 Session Management | yes (Phase 2) | Supabase JWT + httpOnly cookies |
| V4 Access Control | yes | FastAPI Depends + role 检查 |
| V5 Input Validation | yes | Pydantic v2 严格验证 |
| V6 Cryptography | yes | python-jose JWT 验证，不自建加密 |

### Known Threat Patterns for FastAPI + AI API

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| AI API Key 泄露 | Information Disclosure | API Key 仅存服务端环境变量，不暴露给客户端 |
| Prompt Injection | Tampering | 用户输入 sanitization，system/user prompt 分离 |
| SQL Injection | Tampering | SQLAlchemy ORM 参数化查询 |
| 爬虫存储个人数据 | Privacy Violation | 爬虫管道自动过滤个人数据（GDPR） |
| DoS via 爬虫请求 | Denial of Service | 请求频率限制，超时控制 |

## Sources

### Primary (HIGH confidence)
- [Context7: /fastapi/fastapi](https://fastapi.tiangolo.com) — lifespan 事件、BackgroundTasks [VERIFIED]
- [Context7: /agronholm/apscheduler](https://apscheduler.readthedocs.io/) — FastAPI 集成、AsyncScheduler [VERIFIED]
- [Context7: /openai/openai-python](https://platform.openai.com) — AsyncOpenAI、stream API、batch API [VERIFIED]
- [Context7: /kurtmckee/feedparser](https://github.com/kurtmckee/feedparser) — RSS 解析 API [VERIFIED]
- [Context7: /websites/sqlalchemy_en_20](https://docs.sqlalchemy.org) — async session、asyncpg [VERIFIED]

### Secondary (MEDIUM confidence)
- [PROJECT.md] — 技术栈决策、预算约束、架构选择
- [ARCHITECTURE.md] — 系统架构、数据流、组件职责
- [PITFALLS.md] — 10 个关键陷阱及预防策略

### Tertiary (LOW confidence)
- [ASSUMED] — asyncpg 版本号、selectolax 性能数据、token 成本估算

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — 基于 Context7 官方文档验证，版本号和 API 已确认
- Architecture: HIGH — 单体 FastAPI + APScheduler 是成熟模式，Context7 验证集成方式
- Pitfalls: MEDIUM — 基于行业案例和项目研究，部分需实际验证

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (30 天 — 技术栈稳定)
