# NewsFlow — 项目上下文文档

> 本文档汇总了 2026-05-08 的完整讨论成果，用于在其他设备上继续开发讨论时恢复上下文。

---

## 1. 项目概述

**NewsFlow** 是一款 AI 驱动的全源信息聚合 App。用户订阅感兴趣的话题（新闻、股票、演唱会等），系统从全网爬取信息并通过 AI 汇总为简洁摘要推送给用户。

**核心价值：** 用户只需订阅感兴趣的话题，就能高效获取全网最新信息的 AI 摘要——无需自己逐个网站浏览。

**目标市场：** 面向全球通用信息消费者，先海外后国内。

---

## 2. 约束条件

| 约束 | 详情 |
|------|------|
| 预算 | 月支出 < $50，优先使用免费层和低成本方案 |
| 合规 | GDPR 优先，数据存海外服务器 |
| 版权 | 仅展示摘要 + 链接跳转，不缓存全文 |
| 独立开发 | 一人全栈，需控制复杂度，优先核心功能 |
| 市场 | 先海外再国内，国内版需独立合规方案（ICP 备案等） |

---

## 3. 技术栈

### 核心技术

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | Flutter | 3.x | 跨平台 iOS/Android/Web |
| 后端 | Python FastAPI | 0.128.x | 异步 REST API |
| 数据库 | PostgreSQL | 16+ | 主数据库 + JSONB |
| 托管 | Supabase Cloud | Free | 数据库 + Auth + OAuth |
| AI 摘要 | GPT-4o-mini | — | 日常摘要，$0.15/MTok |
| AI 深度 | Claude Haiku 4.5 | — | 付费功能，$1/$5 MTok |
| 推送 | Firebase Cloud Messaging | — | 免费无限制 |
| 调度 | APScheduler | 4.x | 进程内定时任务 |

### 采集层

| 库 | 用途 |
|----|------|
| feedparser 6.x | RSS/Atom 解析 |
| httpx 0.28.x | 异步 HTTP 客户端 |
| selectolax | HTML 解析（比 BS4 快 10-100x） |

### 后端依赖

| 库 | 用途 |
|----|------|
| SQLAlchemy 2.0.x | ORM + async 支持 |
| asyncpg 0.30.x | PostgreSQL 异步驱动 |
| Alembic 1.14.x | 数据库迁移 |
| Pydantic 2.x | 数据验证 |
| python-jose 3.x | JWT 处理 |
| tenacity 9.x | 重试逻辑 |
| structlog 24.x | 结构化日志 |

### 前端依赖

| 库 | 用途 |
|----|------|
| flutter_riverpod 3.3.x | 状态管理 |
| go_router 17.x | 声明式路由 |
| dio 5.x | HTTP 客户端 |
| freezed 2.x | 不可变数据类 |

### 成本估算

| 项目 | 月费 |
|------|------|
| Supabase Free | $0 |
| Fly.io Hobby | $0-5 |
| FCM | $0 |
| GPT-4o-mini（1000 篇/天） | ~$6 |
| Claude Haiku（付费用户） | ~$5-10 |
| 域名 | ~$1 |
| **总计** | **~$12-22** |

---

## 4. 系统架构

### 整体架构

```
Flutter App (iOS/Android/Web)
        │ HTTPS REST API
        ▼
┌─────────────────────────────────┐
│       FastAPI Application       │
│  ┌───────┐ ┌───────┐ ┌───────┐ │
│  │ Auth  │ │Topics │ │Items  │ │
│  │Router │ │Router │ │Router │ │
│  └───────┘ └───────┘ └───────┘ │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│     Ingestion Layer (后台)       │
│                                 │
│  APScheduler (每15分钟)          │
│     │                           │
│     ▼                           │
│  ┌──────────┐  ┌──────────┐    │
│  │RSS Fetch │  │Web Scrape│    │
│  └────┬─────┘  └────┬─────┘    │
│       └──────┬───────┘          │
│              ▼                  │
│       ┌──────────┐              │
│       │Normalizer│              │
│       └────┬─────┘              │
│            ▼                    │
│       ┌──────────┐              │
│       │  Dedup   │              │
│       │  Engine  │              │
│       └────┬─────┘              │
│            ▼                    │
│       ┌──────────┐              │
│       │AI Summary│ ← GPT-4o-mini│
│       └──────────┘              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PostgreSQL (Supabase Cloud)    │
│  users / topics / items /       │
│  sources / source_health        │
└─────────────────────────────────┘
```

### 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI app + lifespan (scheduler init)
│   ├── config.py            # 环境变量、配置管理
│   ├── database.py          # SQLAlchemy async engine + session
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── source.py        # 信息源 (RSS feed / 网页 URL)
│   │   ├── item.py          # 采集到的信息条目
│   │   └── source_health.py # 源健康状态
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── routers/             # API 路由层 (极薄)
│   │   ├── health.py        # 健康检查
│   │   └── sources.py       # 源管理 API
│   ├── ingestion/           # 信息采集层 (后台任务)
│   │   ├── scheduler.py     # APScheduler 配置
│   │   ├── rss_fetcher.py   # RSS/Atom 拉取
│   │   ├── web_scraper.py   # 网页爬虫
│   │   ├── normalizer.py    # 数据标准化
│   │   ├── dedup.py         # 去重引擎
│   │   └── summarizer.py    # AI 摘要生成
│   └── utils/
│       ├── hash.py          # SHA-256 哈希计算
│       └── text.py          # 文本处理工具
├── alembic/
├── tests/
├── pyproject.toml
└── Dockerfile
```

---

## 5. 需求清单 (38 条 v1 需求)

### Content Aggregation (内容聚合) — Phase 1

| ID | 需求 | 状态 |
|----|------|------|
| CONT-01 | 系统可自动解析和抓取预置 RSS 订阅源 | Pending |
| CONT-02 | 用户可添加自定义 RSS 订阅地址 | Pending |
| CONT-03 | 用户可添加任意网页 URL，系统定期爬取更新 | Pending |
| CONT-04 | 系统按用户关键词从多个源搜索并聚合相关内容 | Pending |
| CONT-05 | 系统自动检测并合并重复内容（URL → 标题相似度 → 内容指纹） | Pending |
| CONT-06 | RSS 源健康监控，失效源自动告警 | Pending |
| CONT-07 | 内容采集高频更新（热门话题 15-60 分钟） | Pending |

### AI Features (AI 功能) — Phase 1 + 4 + 5

| ID | 需求 | Phase | 状态 |
|----|------|-------|------|
| AI-01 | 每条聚合信息自动生成简短 AI 摘要 | 1 | Pending |
| AI-02 | AI 摘要使用低成本模型（GPT-4o-mini）控制预算 | 1 | Pending |
| AI-03 | AI 摘要结果缓存，避免重复调用 | 1 | Pending |
| AI-04 | 按订阅主题生成每日信息概览（每日简报） | 4 | Pending |
| AI-05 | 付费用户可获得趋势分析、情感判断等深度洞察 | 5 | Pending |
| AI-06 | 付费用户可获得多源报道的综合摘要（事件聚类） | 5 | Pending |
| AI-07 | AI 内容审核，自动过滤敏感/违规内容 | 1 | Pending |
| AI-08 | 版权合规的摘要 prompt 设计 | 1 | Pending |

### User System (用户系统) — Phase 2

| ID | 需求 | 状态 |
|----|------|------|
| USER-01 | 用户可通过邮箱注册和登录 | Pending |
| USER-02 | 用户可通过 Google 账号登录 | Pending |
| USER-03 | 用户可通过 Apple 账号登录 | Pending |
| USER-04 | 用户可浏览分类目录并订阅感兴趣的话题 | Pending |
| USER-05 | 用户可通过关键词添加订阅 | Pending |
| USER-06 | 用户可管理订阅列表（添加、删除、排序） | Pending |
| USER-07 | 用户可搜索已聚合的内容 | Pending |
| USER-08 | 用户可设置个人偏好（通知频率、显示设置等） | Pending |
| USER-09 | 用户数据符合 GDPR 规范，支持数据导出和删除 | Pending |

### Distribution & Push (分发与推送) — Phase 3 + 4

| ID | 需求 | Phase | 状态 |
|----|------|-------|------|
| DIST-01 | 综合信息流展示所有订阅的最新信息 | 3 | Pending |
| DIST-02 | 可切换到单个主题的独立视图 | 3 | Pending |
| DIST-03 | 卡片式低密度信息展示（标题 + 来源 + 时间） | 3 | Pending |
| DIST-04 | 重大更新即时推送通知 | 4 | Pending |
| DIST-05 | 每日定时推送今日摘要 | 4 | Pending |
| DIST-06 | 异常/突发事件即时推送 | 4 | Pending |
| DIST-07 | 推送频率控制，防止通知疲劳 | 4 | Pending |

### Freemium (免费增值) — Phase 5

| ID | 需求 | 状态 |
|----|------|------|
| FREE-01 | 免费用户可订阅有限数量的话题 | Pending |
| FREE-02 | 免费用户可查看基础摘要 | Pending |
| FREE-03 | 免费用户有每日查看次数限制 | Pending |
| FREE-04 | 付费用户可无限订阅话题 | Pending |
| FREE-05 | 付费用户可使用深度 AI 分析功能 | Pending |
| FREE-06 | 付费用户享有优先推送 | Pending |
| FREE-07 | 订阅付费流程（应用内购买） | Pending |

### v2 需求（已推迟）

- AIC-01/02/03: AI 对话追问
- ADV-01/02/03/04: 离线阅读、TTS 音频、多视角分析、智能推荐

---

## 6. 路线图

### 5 阶段垂直 MVP 路线图

| Phase | 目标 | 依赖 | 状态 |
|-------|------|------|------|
| **Phase 1** | 基础架构 + 内容采集管道 | 无 | 研究完成，待规划 |
| **Phase 2** | 用户系统 + 订阅管理 | Phase 1 | — |
| **Phase 3** | Flutter 移动应用 | Phase 2 | — |
| **Phase 4** | 推送通知 + 每日简报 | Phase 3 | — |
| **Phase 5** | 免费增值 + 上线准备 | Phase 4 | — |

### Phase 1 详情

**目标：** 建立可运行的后端服务，能从 RSS 源和网页自动采集、去重、生成 AI 摘要并存储

**需求覆盖：** CONT-01~07, AI-01~03, AI-07~08

**成功标准：**
1. 用户可通过 API 添加自定义 RSS 订阅地址和任意网页 URL，系统自动定期抓取更新
2. 系统自动检测并合并重复内容（URL 去重 + 内容哈希），用户不会看到重复信息
3. 每条聚合信息自动生成简洁 AI 摘要，且月度 AI 成本控制在 $50 以内
4. 系统自动监控 RSS 源健康状态，失效源产生告警
5. 摘要仅包含 2-3 句话 + 来源链接跳转，不缓存全文

**Phase 1 研究已完成**（详见 `.planning/phases/01-foundation-ingestion/01-RESEARCH.md`）

---

## 7. 关键架构决策

| 决策 | 理由 | 状态 |
|------|------|------|
| RSS 优先 + 爬虫补充 | RSS 标准化程度高、稳定性好，爬虫覆盖无 RSS 的源 | 已确定 |
| 摘要用小模型、深度分析用大模型 | 控制成本，$50/月 预算下平衡质量和费用 | 已确定 |
| PostgreSQL + JSONB | 一套数据库兼顾结构化和非结构化数据 | 已确定 |
| 单体 FastAPI + APScheduler | 避免微服务过度工程化，独立开发者友好 | 已确定 |
| 先去重再摘要 | 避免重复 AI 调用导致成本失控 | 已确定 |
| FCM 主题推送 | 免费无限制，topic 订阅模式匹配产品逻辑 | 已确定 |

---

## 8. 10 大关键风险

| # | 风险 | 严重程度 | 预防措施 | 应在 Phase |
|---|------|----------|----------|-----------|
| 1 | AI API 成本失控 | Critical | token 预算 + 先去重再摘要 + prompt caching | 1 |
| 2 | 内容去重失败 | Critical | 多层去重（URL → SHA-256 → SimHash） | 1 |
| 3 | 爬虫被反爬封锁 | High | RSS 优先策略，爬虫仅作兜底 | 1 |
| 4 | RSS 源可靠性衰减 | High | source_health 表 + 连续失败告警 | 1 |
| 5 | 版权纠纷 | High | 摘要 ≤ 2-3 句 + 不复制原文 + 来源归属 | 1 |
| 6 | 推送通知疲劳 | Medium | 频率上限（3-5 条/天）+ 智能聚合 | 4 |
| 7 | GDPR 合规疏忽 | Medium | 数据最小化 + 删除功能 + DPA 签署 | 2 |
| 8 | 应用商店审核被拒 | Medium | 突出 AI 价值 + 内容过滤 + 审核缓冲 | 5 |
| 9 | 数据库设计缺陷 | Medium | articles/events/summaries 分表 + 时序索引 | 1 |
| 10 | 免费增值转化陷阱 | Medium | 精确计算每用户成本 + 硬性成本上限 | 5 |

---

## 9. Phase 1 技术方案

### 核心数据流

```
APScheduler (每15分钟)
    │
    ▼
┌─────────────┐     ┌─────────────┐
│ RSS Fetcher │     │ Web Scraper │
│ (feedparser │     │ (httpx +    │
│  + httpx)   │     │ selectolax) │
└──────┬──────┘     └──────┬──────┘
       └────────┬───────────┘
                ▼
       ┌─────────────┐
       │ Normalizer  │ ← 统一格式、解析时间、提取字段
       └──────┬──────┘
              ▼
       ┌─────────────┐
       │ Dedup       │ ← Layer1: URL → Layer2: SHA-256 → Layer3: SimHash(v2)
       └──────┬──────┘
              ▼
       ┌─────────────┐
       │ PostgreSQL  │ ← items 表, status="pending_summary"
       └──────┬──────┘
              ▼ (APScheduler 每5分钟)
       ┌─────────────┐
       │ AI Summarizer│ ← GPT-4o-mini 批量处理 + 成本监控
       └──────┬──────┘
              ▼
       ┌─────────────┐
       │ PostgreSQL  │ ← 更新 summary, status="ready"
       └─────────────┘
```

### 关键代码模式

**1. FastAPI Lifespan + APScheduler 集成：**

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.interval import IntervalTrigger

scheduler: AsyncScheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global scheduler
    engine = create_async_engine(settings.DATABASE_URL)
    data_store = SQLAlchemyDataStore(engine)
    scheduler = AsyncScheduler(data_store)

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

**2. 分层去重引擎：**

```python
import hashlib

class DedupEngine:
    def __init__(self, db_session):
        self.db = db_session

    async def is_duplicate(self, item: dict) -> bool:
        # Layer 1: URL 精确匹配
        if await self._url_exists(item["link"]):
            return True
        # Layer 2: 内容哈希匹配
        content = (item.get("title", "") + item.get("summary", "")).strip()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if await self._hash_exists(content_hash):
            return True
        return False
```

**3. AI 摘要异步队列 + 成本控制：**

```python
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
        messages=[
            {"role": "system", "content": "你是新闻摘要助手。用 2-3 句话客观总结新闻核心事实，不复制原文句子，不发表观点。"},
            {"role": "user", "content": f"标题：{title}\n\n内容：{content[:2000]}"}
        ],
        max_tokens=200,
    )
    return response.choices[0].message.content
```

**4. 成本监控：**

```python
@dataclass
class DailyCostTracker:
    daily_budget_usd: float = 5.0

    def record(self, input_tokens: int, output_tokens: int):
        # GPT-4o-mini: $0.15/MTok input, $0.60/MTok output
        cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        self.total_cost_usd += cost

    def is_over_budget(self) -> bool:
        return self.total_cost_usd >= self.daily_budget_usd * 0.8  # 80% 熔断
```

### Phase 1 验证计划

| Task | 需求 | 测试类型 |
|------|------|----------|
| 项目脚手架 | — | smoke test |
| DB schema | CONT-01~07 | unit test |
| RSS 采集器 | CONT-01, CONT-02 | unit test |
| URL 爬虫 | CONT-03 | unit test |
| 去重引擎 | CONT-05 | unit test |
| AI 摘要 | AI-01, AI-02, AI-03 | unit test |
| 内容 API | CONT-04 | integration test |
| 调度器 | CONT-06, CONT-07 | unit test |
| 内容过滤 | AI-07, AI-08 | unit test |

---

## 10. 待解决的问题

| # | 问题 | 当前状态 | 建议 |
|---|------|----------|------|
| 1 | Python 版本（当前 3.9.6，需 3.12+） | 未解决 | 用 pyenv 或 uv 安装 3.12+ |
| 2 | APScheduler 3.x vs 4.x | 倾向 4.x | 4.x 官方推荐，如有问题回退 3.x |
| 3 | RSS 源列表 | 未确定 | Phase 1 建立源管理机制，初始源列表后续补充 |
| 4 | AI 摘要质量验证 | 未验证 | Phase 1 建立摘要质量评分机制 |
| 5 | RSS 源覆盖率调研 | 未调研 | 建立"已验证 RSS 源"数据库 |

---

## 11. 当前项目状态

**位置：** Phase 1 研究完成，准备进入计划阶段

**已完成：**
- [x] 项目研究（5 份研究文档）
- [x] 需求定义（38 条 v1 需求）
- [x] 路线图（5 阶段）
- [x] Phase 1 技术研究 + 验证策略

**下一步：**
- [ ] Phase 1 详细实施计划
- [ ] 开始编码

**文件位置：**
- 项目根目录：`/Users/qc/Documents/news/`
- 规划文档：`.planning/` 目录
  - `PROJECT.md` — 项目定义
  - `REQUIREMENTS.md` — 38 条需求
  - `ROADMAP.md` — 5 阶段路线图
  - `STATE.md` — 当前状态
  - `research/` — 5 份研究文档
  - `phases/01-foundation-ingestion/` — Phase 1 研究 + 验证策略

---

## 12. 继续讨论的提示

在新设备上继续讨论时，可以：

1. **规划 Phase 1** — 基于研究结论制定详细实施计划
2. **直接开始编码** — 从项目脚手架开始
3. **调整需求** — 如有新的想法或优先级变化
4. **深入某个技术点** — 如去重策略、AI prompt 设计等

---

*文档生成时间：2026-05-09*
*基于 2026-05-08 的完整讨论成果*
