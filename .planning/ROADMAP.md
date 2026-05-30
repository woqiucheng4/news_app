# Roadmap: NewsFlow

## Overview

NewsFlow 是一款 AI 驱动的信息聚合 App，核心价值是让用户只需订阅话题，就能高效获取全网最新信息的 AI 摘要。本路线图采用垂直 MVP 模式，5 个阶段从后端数据管道到前端应用再到商业化，每个阶段交付完整的端到端用户能力。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: 基础架构 + 内容采集管道** - 后端数据采集、去重、AI 摘要生成的完整管道
- [x] **Phase 2: 用户系统 + 订阅管理** - 用户认证、话题订阅、GDPR 合规的完整用户能力（3/3 plans done, UAT 全部清零）
- [ ] **Phase 3: Flutter 移动应用** - iOS/Android 可运行的信息浏览客户端
- [ ] **Phase 4: 推送通知 + 每日简报** - 智能推送系统和每日综合摘要
- [ ] **Phase 5: 免费增值 + 上线准备** - 订阅付费体系和应用商店上线

## Phase Details

### Phase 1: 基础架构 + 内容采集管道 + 热点聚合
**Goal**: 建立可运行的后端服务，能从 RSS 源采集内容、从各大平台抓取热点、去重、生成 AI 摘要，并通过最简 Web 界面展示
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: CONT-01, CONT-02, CONT-03, CONT-04, CONT-05, CONT-06, CONT-07, CONT-08, AI-01, AI-02, AI-03, AI-07, AI-08
**Success Criteria** (what must be TRUE):
  1. 用户可通过 API 添加自定义 RSS 订阅地址和任意网页 URL，系统自动定期抓取更新
  2. 系统自动检测并合并重复内容（URL 去重 + 内容哈希），用户不会看到重复信息
  3. 每条聚合信息自动生成简洁 AI 摘要，且月度 AI 成本控制在 $50 以内
  4. 系统自动监控 RSS 源健康状态，失效源产生告警
  5. 摘要仅包含 2-3 句话 + 来源链接跳转，不缓存全文，符合版权合规要求
  6. 系统每 15-30 分钟从各大平台抓取热点数据，聚合并展示在 Web 界面
  7. 热点数据采集遵守法律合规清单（尊重 robots.txt、不突破技术防护、不存储个人信息）

Plans:
- [ ] 01-01: 开发环境搭建 + 数据库迁移
- [ ] 01-02: 三层去重引擎
- [ ] 01-03: RSS 内容采集管道
- [ ] 01-04: 网页内容提取器
- [ ] 01-05: AI 摘要生成管道
- [ ] 01-06: 成本追踪与预算控制
- [ ] 01-07: 定时任务调度器
- [ ] 01-08: 热点平台爬虫（9 平台）
- [ ] 01-09: 自适应抓取频率
- [ ] 01-10: 事件聚类引擎
- [ ] 01-11: 最简 Web 界面
- [ ] 01-12: 测试 + 文档

#### 01-01: 开发环境搭建 + 数据库迁移
**Delivers:** 可运行的本地开发环境，数据库 schema 就绪
**Requirements:** 基础设施
**Details:**
- 创建 `.env.example`，定义所有环境变量（DATABASE_URL、REDIS_URL、OPENAI_API_KEY 等）
- 完善 Alembic 迁移脚本，覆盖 TECHNICAL_DESIGN.md 中定义的所有表（Article、Source、Event、User、Topic、Subscription、Notification、APIUsageLog、DailyCostSummary）
- 添加 `fetch_interval_minutes`、`heat_score`、`relevance_score` 等竞品分析新增字段
- `docker-compose up` 一键启动全部服务（API、PostgreSQL、Redis）
- 验证 `/health` 端点返回所有服务正常
- 种子数据脚本：插入 20 个初始 RSS 源（TechCrunch、Reuters、Hacker News 等）
**Acceptance:** `docker-compose up` 后访问 `http://localhost:8000/docs` 可见 Swagger，`/health` 返回 healthy

#### 01-02: 三层去重引擎
**Delivers:** `IDeduplicationService` 实现，三层去重逻辑可独立测试
**Requirements:** CONT-05
**Details:**
- 实现 `DeduplicationService`（`services/deduplication.py`）
- 第 1 层：URL 去重 — `SHA256(normalize_url(url))` 查询 Article.url_hash
- 第 2 层：标题相似度 — MinHash + Jaccard 相似度 ≥ 70% 判定重复
- 第 3 层：内容指纹 — SimHash + Hamming 距离 ≤ 3 判定重复
- `check_duplicate()` 返回 `{is_duplicate, duplicate_of, event_id, similarity, layer}`
- 需要安装依赖：`datasketch`（MinHash）、自实现 SimHash
**Acceptance:** 单元测试覆盖 3 层去重各场景（URL 相同、标题相似、内容相似、全新文章）

#### 01-03: RSS 内容采集管道
**Delivers:** 系统可从 RSS 源自动抓取并入库文章
**Requirements:** CONT-01, CONT-02, CONT-06
**Details:**
- 实现 `ContentIngestionService.fetch_feed()` — 抓取单个 RSS 源
- 实现 `ContentIngestionService.fetch_all_feeds()` — 并发抓取所有活跃源
- RSS 解析使用 `feedparser`，提取 title/url/content/published_at/author
- 数据清洗：标题规范化（去除 HTML、多余空白）、时间解析（多格式兼容）
- 调用去重服务过滤重复文章
- 入库后触发 AI 摘要生成（后台任务）
- 源健康监控：连续失败 ≥ 5 次自动标记 `is_active = False`
- 实现 `SourceRepository.update_fetch_status()` 更新抓取状态
**Acceptance:** 手动调用 `fetch_all_feeds()` 后，数据库中有新文章，重复文章被过滤

#### 01-04: 网页内容提取器
**Delivers:** 系统可从任意网页 URL 提取标题和正文
**Requirements:** CONT-03
**Details:**
- 实现 `ContentIngestionService` 中的网页抓取逻辑
- 使用 `httpx` + `selectolax` 提取标题（`<h1>`）和正文（最长 `<p>` 集合）
- 支持 RSS 中没有 content 只有 link 的条目，自动回退抓取原文
- 超时控制：单页 30 秒，重试 3 次（使用 `tenacity`）
- 仅提取元数据和摘要片段，不缓存全文（版权合规）
**Acceptance:** 输入一个新闻 URL，返回 `{title, content_excerpt}` 结构化数据

#### 01-05: AI 摘要生成管道
**Delivers:** 系统可自动生成文章摘要 + 推送价值评分
**Requirements:** AI-01, AI-02, AI-03, AI-08
**Details:**
- 完善 `core/ai.py`，封装 OpenAI API 调用
- 实现 `ArticleService.generate_summary()` — 生成摘要并更新 Article
- Prompt 输出 JSON 格式：`{summary, relevance_score}`
- 缓存策略：`summary:{url_hash}` 存 Redis，TTL 7 天
- 摘要长度：2-3 句话，50-100 字
- 语言与原文一致（中/英）
- 记录每次调用的 token 数和费用到 `APIUsageLog`
- 错误处理：API 超时/限流自动重试（tenacity），失败不阻塞文章入库
**Acceptance:** 新文章入库后自动生成摘要，`relevance_score` 存入 Article 表

#### 01-06: 成本追踪与预算控制
**Delivers:** AI 成本实时监控 + 预算超限自动降级
**Requirements:** AI-02
**Details:**
- 实现 `CostService`（`services/cost.py`）+ `CostRepository`（`repositories/sqlalchemy/cost.py`）
- `record_usage()` — 记录每次 AI 调用的 model/input_tokens/output_tokens/cost_usd
- `check_budget()` — 检查日预算（$5）和月预算（$100）
- `get_degradation_level()` — 返回当前降级级别（normal/degraded/paused）
- 降级策略：< 80% 正常 → 80-95% 降低频率 → 95-100% 仅返回缓存 → > 100% 暂停
- `GET /api/v1/dashboard/cost/summary` 端点返回实时成本数据
**Acceptance:** 模拟 100 次摘要生成，成本记录准确，超预算时自动降级

#### 01-07: 定时任务调度器
**Delivers:** APScheduler 驱动的定时采集 + 摘要生成循环
**Requirements:** CONT-07
**Details:**
- 在 FastAPI lifespan 中初始化 APScheduler
- 任务 1：RSS 采集 — 每 30 分钟执行 `fetch_all_feeds()`
- 任务 2：摘要生成 — 每 15 分钟处理未摘要文章队列
- 任务 3：源健康检查 — 每小时检查失效源并告警
- 任务 4：热度更新 — 每小时更新所有源的 `heat_score`
- 并发控制：`asyncio.Semaphore` 限制同时抓取数（默认 10）
- 错误隔离：单个源失败不影响其他源
**Acceptance:** 服务启动后自动按计划执行任务，日志可见调度记录

#### 01-08: 热点平台爬虫（9 平台）
**Delivers:** 从 9 个平台抓取热点数据，统一入库
**Requirements:** CONT-08
**Details:**
- 实现 `ContentIngestionService.crawl_hot_topics()`
- 平台及抓取方式：
  - Hacker News: 官方 API (`hacker-news.firebaseio.com`)
  - Reddit: JSON API (`reddit.com/r/{sub}/hot.json`)
  - GitHub: Trending API
  - Google Trends: pytrends 库
  - Product Hunt: 官方 API
  - 微博热搜: 移动端 API
  - 知乎热榜: API
  - 百度热搜: API
  - B站热门: API
- 每个平台独立爬虫类，实现统一 `HotSource` 接口
- 合规：遵守 robots.txt，请求间隔 ≥ 2 秒，不存储个人信息
- 热点数据作为特殊 Source 类型入库，参与去重和摘要流程
**Acceptance:** 调用 `crawl_hot_topics()` 后，9 个平台的热点数据出现在数据库中

#### 01-09: 自适应抓取频率
**Delivers:** 根据源热度动态调整抓取间隔
**Requirements:** CONT-07
**Details:**
- 实现 `AdaptiveFetchScheduler`（参考 TECHNICAL_DESIGN.md 5.4 节）
- 热度公式：`heat_score = (近24h新文章数 × 0.6) + (订阅用户数 × 0.4)`
- 频率映射：≥50 → 5min / 20-49 → 15min / 5-19 → 30min / 1-4 → 2h / 0 → 6h
- 每小时更新一次所有源的热度分数和抓取间隔
- 01-07 的调度器根据 `fetch_interval_minutes` 动态调度
**Acceptance:** 高热度源抓取频率明显高于低热度源，日志可见间隔调整

#### 01-10: 事件聚类引擎
**Delivers:** 相似文章自动聚类为事件
**Requirements:** CONT-05
**Details:**
- 去重引擎第 2/3 层命中时，将新文章关联到已有 Event
- 新文章与 Event 的 `representative_hash` 比较，Hamming ≤ 3 归入
- 否则创建新 Event，该文章为代表文章
- Event 表字段：title（取最早文章标题）、article_count、source_count
- `EventRepository.update_article_count()` 更新计数
- 提供 `GET /api/v1/articles/trending` 展示热门事件
**Acceptance:** 同一事件的多篇报道自动聚为一个 Event，article_count 正确递增

#### 01-11: 最简 Web 界面
**Delivers:** 可浏览信息流和热点的 Web 页面
**Requirements:** DIST-03
**Details:**
- 使用 Jinja2 模板（FastAPI 原生支持），不引入前端框架
- 页面 1：信息流 — 卡片列表展示最新文章（标题 + 来源 + 时间 + 摘要）
- 页面 2：热点聚合 — 按平台分组展示热门话题
- 页面 3：文章详情 — 摘要 + 原文链接
- 支持分类筛选（科技/财经/娱乐等）
- 响应式布局，手机可用
- 目的：验证数据管道端到端可用，非最终产品 UI
**Acceptance:** 浏览器访问可看到实时更新的信息流，点击可查看详情

#### 01-12: 测试 + 文档
**Delivers:** 核心模块测试覆盖 + API 文档
**Requirements:** 质量保障
**Details:**
- pytest 配置：`conftest.py`、fixtures（测试数据库、mock AI 响应）
- 单元测试：去重引擎（3 层各场景）、成本计算、摘要生成
- 集成测试：RSS 抓取 → 去重 → 入库 → 摘要生成完整流程
- API 测试：所有端点的基本请求/响应验证
- 覆盖率目标：核心模块 ≥ 70%
- 更新 README.md：项目介绍、本地启动步骤、API 文档链接
**Acceptance:** `pytest` 全部通过，覆盖率报告可见

### Phase 2: 用户系统 + 订阅管理
**Goal**: 建立完整的用户账户系统和话题订阅功能，支持个性化信息获取
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: USER-01, USER-02, USER-03, USER-04, USER-05, USER-06, USER-07, USER-09
**Success Criteria** (what must be TRUE):
  1. 用户可通过邮箱、Google 或 Apple 账号注册并登录
  2. 用户可浏览分类目录、通过关键词搜索并订阅感兴趣的话题
  3. 用户可管理订阅列表（添加、删除、排序）
  4. 用户可搜索已聚合的内容
  5. 用户可导出个人数据或请求删除账户，符合 GDPR 规范
**Plans**: 02-01 / 02-02 / 02-03 全部完成 ✅

Plans:
- [x] 02-01: 用户认证（邮箱/Google/Apple）+ GDPR 数据导出/删除（USER-01/02/03/09）— 见 [`phases/02-user-subscription/02-01-PHASE_SUMMARY.md`](./phases/02-user-subscription/02-01-PHASE_SUMMARY.md)
- [x] 02-02: 话题目录 + 关键词订阅 + 订阅管理细化（USER-04/05/06）— 见 [`phases/02-user-subscription/02-02-PHASE_SUMMARY.md`](./phases/02-user-subscription/02-02-PHASE_SUMMARY.md)
- [x] 02-03: 内容搜索（USER-07）— 见 [`phases/02-user-subscription/02-03-PHASE_SUMMARY.md`](./phases/02-user-subscription/02-03-PHASE_SUMMARY.md)

#### 02-01: 用户认证 + GDPR
**Delivers:** 4 个 auth 接口（注册/登录/OAuth/refresh）+ 4 个 user 接口（资料/设置/导出/注销）；JWT access+refresh 双 token 体系；Flutter Auth 接入完整骨架（含 Secure Storage / 401 自动刷新 / Google+Apple SDK / GDPR 操作）
**Requirements:** USER-01, USER-02, USER-03, USER-09
**Status:** ✅ Done — 详见 [`phases/02-user-subscription/02-01-PHASE_SUMMARY.md`](./phases/02-user-subscription/02-01-PHASE_SUMMARY.md) 与 [`phases/02-user-subscription/02-01-VALIDATION.md`](./phases/02-user-subscription/02-01-VALIDATION.md)
**Acceptance:** `pytest -q tests/test_auth_api.py tests/test_auth_service.py tests/test_user_service.py tests/test_auth_user_uat_flow.py` 通过；CI 全量 pytest 已隐含覆盖
**Open Hardening:** OAuth ID Token 签名验证、Refresh Token 旋转/撤销、GDPR 硬删除策略、邮箱验证、密码重置、登录速率限制（移交后续硬化 plan）

#### 02-02: 话题目录 + 关键词订阅 + 订阅管理细化
**Delivers:** 后端 9 个订阅接口 + 1 个 Feed 接口；Flutter 接入文档矩阵（5 篇）；CI / PR 模板 / CODEOWNERS / Demo seed 全套基础设施
**Requirements:** USER-04, USER-05, USER-06
**Status:** ✅ Done — 详见 [`phases/02-user-subscription/02-02-PHASE_SUMMARY.md`](./phases/02-user-subscription/02-02-PHASE_SUMMARY.md) 与 [`phases/02-user-subscription/02-02-VALIDATION.md`](./phases/02-user-subscription/02-02-VALIDATION.md)
**Acceptance:** `pytest -q tests/test_user_subscription_api.py tests/test_api_endpoints.py` 通过；Backend CI 已跑通 seed 语法检查 + 订阅回归 + 全量 pytest

#### 02-03: 内容搜索
**Delivers:** `GET /api/v1/articles/search?q=&limit=` 端点；ILIKE 三字段（title/content/summary）匹配 + 已删除排除 + published_at 倒序；Flutter 防抖 + 取消 + 双 Tab 搜索骨架
**Requirements:** USER-07
**Status:** ✅ Done — 详见 [`phases/02-user-subscription/02-03-PHASE_SUMMARY.md`](./phases/02-user-subscription/02-03-PHASE_SUMMARY.md) 与 [`phases/02-user-subscription/02-03-VALIDATION.md`](./phases/02-user-subscription/02-03-VALIDATION.md)
**Acceptance:** `pytest -q tests/test_api_endpoints.py tests/test_article_search.py` 通过；CI 全量 pytest 已隐含覆盖；UAT 15 项已清零
**Open Hardening:** PostgreSQL 全文索引（tsvector + GIN）、多关键词 AND、相关度排序、分页、公开端点限流（移交后续硬化 plan）

### Phase 3: Flutter 移动应用
**Goal**: 用户可在 iOS/Android 设备上浏览订阅信息流、搜索内容并管理设置
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: DIST-01, DIST-02, DIST-03, USER-08
**Success Criteria** (what must be TRUE):
  1. 用户可在手机上看到所有订阅的综合信息流，以卡片式布局展示标题、来源和时间
  2. 用户可切换到单个主题的独立视图查看特定话题的内容
  3. 用户可在应用内搜索已聚合的内容
  4. 用户可设置个人偏好（通知频率、显示设置等）
**Plans**: 03-01 全局搜索 ✅ · 03-02 单话题 Feed 视图 ✅ · 03-03 移动端打包与发布准备

Plans:
- [x] 03-01: 全局搜索页（`GET /articles/search` + 话题搜索双 Tab）— Flutter `SearchScreen`
- [x] 03-02: 单话题独立 Feed 视图（`GET /articles/feed?topic_id=` + 订阅列表入口）
- [ ] 03-03: iOS/Android 构建配置与冒烟测试清单

**UI hint**: yes

### Phase 4: 推送通知 + 每日简报
**Goal**: 用户可接收智能推送通知和每日综合摘要，保持信息时效性
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: DIST-04, DIST-05, DIST-06, DIST-07, AI-04
**Success Criteria** (what must be TRUE):
  1. 用户订阅的话题有重大更新时收到即时推送通知
  2. 用户每天定时收到当日信息综合摘要
  3. 异常/突发事件触发即时推送
  4. 推送频率可控，用户可设置每日推送上限防止通知疲劳
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: 免费增值 + 上线准备
**Goal**: 建立免费增值商业模式，应用通过 App Store / Google Play 审核正式上线
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: FREE-01, FREE-02, FREE-03, FREE-04, FREE-05, FREE-06, FREE-07, AI-05, AI-06
**Success Criteria** (what must be TRUE):
  1. 免费用户可订阅有限数量的话题并查看基础摘要，有每日查看次数限制
  2. 付费用户可无限订阅话题、使用深度 AI 分析功能并享有优先推送
  3. 用户可通过应用内购买完成订阅付费
  4. 应用通过 App Store 和 Google Play 审核并正式上架
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 基础架构 + 内容采集管道 + 热点聚合 | 0/12 | Not audited (实现已部分落地，待人工执行 `01-UAT.md`) | - |
| 2. 用户系统 + 订阅管理 | **3/3** | ✅ **All plans done** | 02-01: 2026-05-29 / 02-02: 2026-05-28 / 02-03: 2026-05-29 |
| 3. Flutter 移动应用 | 2/TBD | In progress (03-01/03-02 done) | 03-01: 2026-05-31 / 03-02: 2026-05-31 |
| 4. 推送通知 + 每日简报 | 0/TBD | Not started | - |
| 5. 免费增值 + 上线准备 | 0/TBD | Not started | - |
