# Stack Research

**Domain:** AI-powered information aggregation app (NewsFlow)
**Researched:** 2026-05-08
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Flutter | 3.x (latest stable) | 跨平台前端 (iOS/Android/Web) | 单一代码库覆盖全平台，Dart 类型安全，热重载提升开发效率，Google 官方维护。独立开发者唯一合理选择——React Native 需要分别处理 iOS/Android 原生模块，Flutter 的自绘引擎保证一致性 |
| Dart | 3.x | Flutter 编程语言 | 与 Flutter 绑定，null safety、async/await、pattern matching (Dart 3+) |
| Python | 3.12+ | 后端语言 | 异步生态成熟 (asyncio)，AI/ML 库最丰富，FastAPI 性能优秀 |
| FastAPI | 0.128.x | 后端框架 | 原生 async/await，自动生成 OpenAPI 文档，依赖注入系统强大，Pydantic v2 数据验证，性能接近 Node.js/Go。比 Django 轻量得多，适合独立开发者 |
| PostgreSQL | 16+ | 主数据库 | JSONB 支持非结构化数据，全文搜索内置，免费开源，Supabase 免费层直接提供。比 MySQL 更适合复杂查询和 JSON 操作 |
| SQLAlchemy 2.0 | 2.0.x | ORM + 数据库工具 | Python 最成熟的 ORM，2.0 版原生 async 支持 (asyncpg)，Alembic 迁移工具官方配套 |
| Supabase | Cloud | 数据库托管 + Auth + 实时 | 免费层 500MB 存储 + 5GB 带宽 + 50K MAU Auth，内置 Google/Apple OAuth，省去自建认证系统的巨大工作量 |

### AI Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OpenAI Python SDK | 2.x | GPT-4o-mini API 调用 | 用于日常摘要生成。GPT-4o-mini 是当前最具性价比的摘要模型：$0.15/MTok 输入、$0.60/MTok 输出。1000 篇/天约 $5.85/月，完全在预算内 |
| Anthropic Python SDK | latest | Claude Haiku 4.5 API 调用 | 用于深度分析 (付费用户功能)。Claude Haiku 4.5: $1/MTok 输入、$5/MTok 输出，质量高于 GPT-4o-mini 但成本高约 7x。仅对付费用户的深度分析功能使用 |
| httpx | 0.28.x | 异步 HTTP 客户端 | 统一的 sync/async API，支持 HTTP/2，比 aiohttp 更现代化，Requests-like 接口学习成本低。用于爬虫和外部 API 调用 |

**成本估算 ($50/月预算分配):**

| 项目 | 月费 | 说明 |
|------|------|------|
| Supabase Free | $0 | 500MB 存储足够 MVP |
| Fly.io Hobby / Railway | $0-5 | 后端部署 |
| Firebase (FCM) | $0 | 推送通知免费 |
| GPT-4o-mini (日常摘要) | ~$6 | 1000 篇/天 |
| Claude Haiku (深度分析) | ~$5-10 | 付费用户少量调用 |
| 域名 | ~$1 | .com 域名分摊 |
| **总计** | **~$12-22** | 远低于 $50 预算上限 |

### Data Collection Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| feedparser | 6.x | RSS/Atom 解析 | Python RSS 解析事实标准，支持 RSS 0.9x/1.0/2.0 和 Atom 全部版本，API 简洁，活跃维护 |
| httpx | 0.28.x | 异步网页抓取 | 替代 requests，原生 async，HTTP/2 支持，适合高频爬取场景 |
| selectolax | latest | HTML 解析 | 比 BeautifulSoup 快 10-100x (基于 C 库 Modest)，内存占用低，适合高频爬虫场景。解析速度在爬虫场景下是关键性能指标 |

**为什么不选 Scrapy:** Scrapy 是重量级爬虫框架，学习曲线陡峭，进程模型与 FastAPI 的 async 不兼容。对于 RSS 优先的场景，feedparser + httpx + selectolax 的组合更轻量、更灵活，且可以直接集成到 FastAPI 的异步事件循环中。

### Background Task Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| APScheduler | 3.10.x | 定时任务调度 | 轻量级，无需外部 broker (Redis/RabbitMQ)，直接在 FastAPI 进程内运行。支持 cron 表达式，适合 RSS 定时抓取 (15-60 分钟间隔)。对独立开发者来说，Celery 的运维复杂度不值得 |
| FastAPI BackgroundTasks | built-in | 轻量后台任务 | 内置，零配置。用于 AI 摘要生成等不需要持久化的 fire-and-forget 任务 |

**为什么不用 Celery:** Celery 需要 Redis/RabbitMQ 作为 broker，增加一个需要运维的组件。对独立开发者和 $50 预算来说过度设计。APScheduler + FastAPI BackgroundTasks 足够覆盖 MVP 阶段需求。如果后期需要任务持久化和重试，再迁移到 Taskiq (比 Celery 更现代的替代品)。

### Push Notification Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Firebase Admin Python SDK | latest | FCM 推送 | 免费，无消息数量限制，支持 iOS/Android/Web，topic 订阅模式天然匹配 "订阅话题" 的产品逻辑 |
| firebase_messaging (Flutter) | latest | 客户端 FCM | Flutter 官方 Firebase 插件，成熟稳定 |

### Flutter Frontend Packages

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| flutter_riverpod | 3.3.x | 状态管理 | 全局状态管理首选。比 Provider 更安全 (编译时检查)，比 Bloc 更简洁 (更少样板代码)，Flutter 团队推荐方案之一。3.x 版本 API 更简洁，代码生成支持完善 |
| go_router | 17.x | 声明式路由 | Flutter 官方推荐路由方案。支持 deep link、ShellRoute (底部导航栏)、redirect (认证守卫)。feature-complete 状态，稳定可靠 |
| dio | 5.x | HTTP 客户端 | 比 http 包更强大：拦截器 (自动添加 auth token)、请求重试、FormData 上传。适合与 FastAPI 后端通信 |
| freezed | 2.x | 数据类生成 | 不可变数据类 + JSON 序列化 + union types。减少模型类样板代码 80%+，配合 json_serializable 使用 |
| json_serializable | 6.x | JSON 序列化 | 与 freezed 配合，类型安全的 JSON 解析。比手写 fromJson/toJson 更安全 |
| cached_network_image | 3.x | 图片缓存 | 列表卡片中的来源图标/缩略图缓存，减少重复网络请求 |
| flutter_local_notifications | 18.x | 本地通知 | 与 FCM 配合，处理通知点击、通知展示样式 |
| google_sign_in | 6.x | Google 登录 | Supabase Auth 的 Google OAuth 集成 |
| sign_in_with_apple | 6.x | Apple 登录 | iOS 必需，Supabase Auth 的 Apple OAuth 集成 |
| shimmer | 3.x | 加载占位符 | 卡片加载时的骨架屏效果，提升感知性能 |

### Backend Python Packages

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncpg | 0.30.x | PostgreSQL 异步驱动 | SQLAlchemy async 模式的底层驱动，性能远超 psycopg2 |
| pydantic | 2.x | 数据验证 | FastAPI 内置，请求/响应模型定义，v2 性能提升 5-50x |
| python-jose | 3.x | JWT 处理 | Supabase JWT token 验证 |
| feedparser | 6.x | RSS 解析 | RSS 源抓取和解析 |
| selectolax | latest | HTML 解析 | 网页内容提取，比 BeautifulSoup 快 10-100x |
| APScheduler | 3.10.x | 任务调度 | RSS 定时抓取 |
| firebase-admin | latest | FCM 推送 | 发送推送通知 |
| alembic | 1.14.x | 数据库迁移 | SQLAlchemy schema 版本管理 |
| tenacity | 9.x | 重试逻辑 | AI API 调用、爬虫请求的自动重试 |
| structlog | 24.x | 结构化日志 | 比标准 logging 更适合生产环境，JSON 格式日志便于排查问题 |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| FVM (Flutter Version Management) | Flutter 版本管理 | 锁定 Flutter 版本，避免团队/CI 版本不一致 |
| uv | Python 包管理 | 比 pip 快 10-100x，替代 poetry/pipenv。2025 年 Python 生态首选包管理器 |
| Docker | 容器化 | 后端部署标准，Fly.io/Railway 原生支持 |
| GitHub Actions | CI/CD | 免费 2000 分钟/月，Flutter + Python 测试和部署 |
| Supabase CLI | 本地开发 | 本地运行 Supabase，数据库迁移，Edge Functions 开发 |

## Installation

### Flutter 前端

```bash
# 安装 FVM
dart pub global activate fvm
fvm install stable
fvm use stable

# 核心依赖
flutter pub add flutter_riverpod go_router dio
flutter pub add freezed_annotation json_annotation cached_network_image
flutter pub add flutter_local_notifications google_sign_in sign_in_with_apple
flutter pub add supabase_flutter firebase_core firebase_messaging shimmer

# 开发依赖
flutter pub add -d build_runner freezed json_serializable riverpod_generator
```

### Python 后端

```bash
# 使用 uv (推荐)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 初始化项目
uv init newflow-backend
cd newflow-backend

# 核心依赖
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic
uv add pydantic python-jose[cryptography] passlib
uv add feedparser httpx selectolax
uv add apscheduler firebase-admin tenacity structlog
uv add supabase

# 开发依赖
uv add -D pytest pytest-asyncio httpx ruff mypy
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Flutter | React Native (Expo) | 团队已有 React 经验，或需要大量原生模块集成 |
| FastAPI | Django + DRF | 需要完整 admin 后台、ORM 迁移工具内置、团队熟悉 Django |
| Supabase Auth | Firebase Auth | 已深度使用 Firebase 生态 (但 Supabase 更适合 PostgreSQL 场景) |
| Supabase | Neon (Serverless PG) | 只需要 PostgreSQL 不需要 Auth/Storage，Neon 的 serverless 更便宜 |
| Riverpod | flutter_bloc | 团队偏好严格的状态机模式，或已有 Bloc 代码库 |
| feedparser | RssParser (Dart) | 想在 Flutter 端直接解析 RSS (不推荐，应在后端统一处理) |
| APScheduler | Celery + Redis | 需要分布式任务队列、任务持久化、重试机制 |
| GPT-4o-mini | Claude Haiku 4.5 | 对摘要质量要求更高，且预算允许 (成本约 7x) |
| selectolax | BeautifulSoup | 需要更宽松的容错解析 (selectolax 对畸形 HTML 更严格) |
| go_router | auto_route | 需要更强的类型安全路由和代码生成 (auto_route 的 type-safe 更好) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Celery + Redis | 需要额外运维 Redis，对独立开发者过度设计 | APScheduler (进程内调度) |
| Scrapy | 重量级框架，学习曲线陡，与 FastAPI async 不兼容 | feedparser + httpx + selectolax |
| Django | 对纯 API 后端来说过重，模板/admin 功能用不上 | FastAPI |
| MongoDB | 项目需求明确是关系型数据 (用户/订阅/文章)，JSONB 已覆盖非结构化需求 | PostgreSQL + JSONB |
| Beautiful Soup | 性能差 (纯 Python)，高频爬虫场景下是瓶颈 | selectolax (C 底层，快 10-100x) |
| Provider (Flutter) | 编译时无类型检查，运行时错误难调试 | Riverpod (编译时安全) |
| GetX (Flutter) | 魔法方法多，测试困难，社区争议大 | Riverpod |
| 自建 Auth 系统 | 工作量巨大 (OAuth、JWT、密码重置、邮箱验证)，安全风险高 | Supabase Auth |
| 自建推送系统 | APNs/FCM 协议复杂，维护成本高 | Firebase Cloud Messaging |
| SQLite | 不支持并发写入，不适合后端服务 | PostgreSQL |
| psycopg2 (同步驱动) | 阻塞事件循环，无法发挥 FastAPI 异步优势 | asyncpg |

## Stack Patterns by Variant

**如果预算极其紧张 (< $10/月):**
- 用 Supabase Free ($0) + Oracle Cloud Always Free 免费 VPS ($0)
- AI 用 GPT-4o-mini，严格控制调用量
- 免费层限制：500MB 存储，5GB 带宽，项目 1 周不活跃会暂停

**如果用户增长超出 Supabase 免费层:**
- 升级 Supabase Pro ($25/月) 或迁移到自托管 PostgreSQL (Fly.io Postgres)
- 数据库迁移用 Alembic，切换成本低

**如果需要更高的 AI 摘要质量:**
- 将日常摘要从 GPT-4o-mini 升级到 Claude Haiku 4.5
- 成本增加约 7x，但质量提升明显
- 或者用 prompt engineering 优化 GPT-4o-mini 的输出质量

**如果需要支持国内用户:**
- 后端需要部署到国内服务器 (阿里云/腾讯云)
- 需要 ICP 备案
- AI API 需要替换为国内服务 (通义千问/文心一言)
- 推送需要替换为极光推送/个推

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Flutter 3.x | Dart 3.x | 必须匹配，用 FVM 管理 |
| flutter_riverpod 3.3.x | riverpod 3.2.x | 自动依赖解析 |
| go_router 17.x | Flutter 3.x | 官方维护，兼容性好 |
| SQLAlchemy 2.0.x | asyncpg 0.29+ | 2.0 原生 async，需要 asyncpg 驱动 |
| SQLAlchemy 2.0.x | Alembic 1.14+ | Alembic 必须匹配 SQLAlchemy 主版本 |
| FastAPI 0.128.x | Pydantic 2.x | FastAPI 0.100+ 强制 Pydantic v2 |
| Python 3.12+ | asyncpg 0.29+ | 3.12 的 async 性能优化显著 |
| firebase-admin | Python 3.8+ | 无特殊兼容问题 |
| Dio 5.x | Flutter 3.x | 无特殊兼容问题 |

## Sources

- [Context7: /websites/flutter_dev](https://docs.flutter.dev) -- Flutter 状态管理推荐、Firebase 集成、push notifications (HIGH confidence)
- [Context7: /fastapi/fastapi](https://fastapi.tiangolo.com) -- FastAPI 最新版本 0.128.x、BackgroundTasks、lifespan、CORS (HIGH confidence)
- [Context7: /anthropics/anthropic-sdk-python](https://docs.anthropic.com) -- Claude API 异步调用、Haiku 4.5 定价 $1/$5 MTok (HIGH confidence)
- [Context7: /openai/openai-python](https://platform.openai.com) -- GPT-4o-mini 异步调用、streaming API (HIGH confidence)
- [Context7: /firebase/firebase-admin-python](https://firebase.google.com) -- FCM 推送、topic 订阅、批量发送 (HIGH confidence)
- [Context7: /websites/sqlalchemy_en_20](https://docs.sqlalchemy.org) -- async session、asyncpg 引擎创建 (HIGH confidence)
- [Context7: /kurtmckee/feedparser](https://github.com/kurtmckee/feedparser) -- RSS 解析 API、版本支持 (HIGH confidence)
- [Context7: /websites/alembic_sqlalchemy](https://alembic.sqlalchemy.org) -- async 迁移模板、autogenerate (HIGH confidence)
- [Context7: /supabase/supabase-flutter](https://supabase.com/docs) -- Flutter SDK 集成 (HIGH confidence)
- [Anthropic Models Page](https://platform.claude.com/docs/en/docs/about-claude/models) -- Claude Haiku 4.5 定价确认: $1/MTok 输入, $5/MTok 输出 (HIGH confidence)
- [Supabase Pricing](https://supabase.com/pricing) -- Free tier: 500MB DB, 5GB bandwidth, 50K MAU; Pro: $25/月 (HIGH confidence)
- [pub.dev: flutter_riverpod 3.3.1](https://pub.dev/packages/flutter_riverpod) -- 最新版本确认 (HIGH confidence)
- [pub.dev: go_router 17.2.3](https://pub.dev/packages/go_router) -- 最新版本确认，feature-complete 状态 (HIGH confidence)

---
*Stack research for: AI-powered information aggregation app (NewsFlow)*
*Researched: 2026-05-08*
