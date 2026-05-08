# Project Research Summary

**Project:** NewsFlow — AI-powered information aggregation app
**Domain:** 信息聚合 / AI 摘要 / 新闻阅读器
**Researched:** 2026-05-08
**Confidence:** MEDIUM-HIGH

## Executive Summary

NewsFlow 是一款 AI 驱动的信息聚合应用，核心价值是用 AI 为多源新闻生成摘要，让用户在 5 分钟内掌握当日要闻。产品定位在 Google News（算法推荐但无 AI 摘要）和 Inoreader（功能复杂但 AI 非核心）之间，以 "AI-first 摘要 + 简洁 UX" 作为差异化竞争点。研究分析了 9 款竞品（Google News、Apple News、Feedly、Inoreader、Flipboard、SmartNews、Artifact、今日头条、即刻），确定了 11 项必备功能和 4 项核心差异化功能。

技术栈推荐采用 Flutter（跨平台前端）+ Python FastAPI（异步后端）+ PostgreSQL/Supabase（数据库+认证）+ GPT-4o-mini/Claude Haiku（AI 摘要）的组合。架构采用单体 FastAPI 应用 + APScheduler 进程内调度，避免微服务过度工程化。月运营成本估算 $12-22，远低于 $50 预算上限。关键风险集中在 AI API 成本控制、内容去重、反爬对抗三个方面——这三个问题如果在第一阶段没有妥善处理，后续修复成本极高。

本项目最大的技术决策共识是：RSS 优先采集（而非爬虫）、异步 AI 摘要队列（而非同步调用）、FCM 主题推送（而非逐用户推送）、单体架构（而非微服务）。这四个决策直接决定了系统的可维护性和成本可控性。

## Key Findings

### Recommended Stack

基于 Context7 官方文档验证和成本分析，推荐的技术栈如下：

**Core technologies:**
- **Flutter 3.x**: 跨平台前端 — 单一代码库覆盖 iOS/Android/Web，自绘引擎保证一致性，独立开发者唯一合理选择
- **FastAPI 0.128.x**: 异步后端框架 — 原生 async/await，自动 OpenAPI 文档，Pydantic v2 验证，比 Django 轻量得多
- **PostgreSQL 16+**: 主数据库 — JSONB 支持非结构化数据，全文搜索内置，Supabase 免费层直接提供
- **Supabase Cloud**: 数据库托管 + Auth — 免费层 500MB 存储 + 50K MAU Auth，内置 Google/Apple OAuth，省去自建认证
- **GPT-4o-mini**: 日常 AI 摘要 — $0.15/MTok 输入，1000 篇/天约 $5.85/月，最具性价比
- **Claude Haiku 4.5**: 深度分析（付费功能）— $1/$5 MTok，质量更高，仅对付费用户使用
- **APScheduler 3.10.x**: 后台定时任务 — 轻量级，无需 Redis/RabbitMQ，直接在 FastAPI 进程内运行
- **Firebase Cloud Messaging**: 推送通知 — 免费无限制，topic 订阅模式匹配产品逻辑

**Cost breakdown ($12-22/month):**
- Supabase Free: $0 | 部署 (Fly.io): $0-5 | FCM: $0 | GPT-4o-mini: ~$6 | Claude Haiku: ~$5-10 | 域名: ~$1

详见: [STACK.md](./STACK.md)

### Expected Features

基于 9 款竞品分析，功能分层如下：

**Must have (table stakes — 缺一不可):**
- Content aggregation (RSS + scraper) — 核心价值基础
- Topic/interest subscription — 用户声明兴趣
- User accounts (Email + Google/Apple OAuth) — 个性化前提
- AI-generated summaries — 核心价值主张
- Personalized feed — 基于参与度排序
- Cross-platform (Mobile + Web) — Flutter 覆盖
- Push notifications — 时效性信息必备
- Article save/bookmark — "稍后阅读"通用期望
- Search — 全文搜索聚合内容
- Source attribution + link-out — 法律和伦理要求
- Offline reading of saved items — 通勤场景

**Should have (v1.1 — 竞争差异化):**
- Daily briefing — 每日一条综合摘要，高留存价值
- Smart notification filtering — AI 评分重要性，防止推送疲劳
- Share to external apps — 病毒传播机制
- Offline reading — 离线阅读缓存

**Defer (v2+):**
- Multi-source synthesis — 需要事件聚类，复杂度高
- Multi-perspective coverage — 需要来源多样性评分
- Audio narration (TTS) — 锦上添花
- Clickbait detection — 有趣但非必需
- Automation rules — 重度用户功能，MVP 过于复杂

**Never build:**
- Full article caching（版权风险）、comments（审核负担）、social network（Artifact 的失败教训）、video（不同产品）、UGC、ads

详见: [FEATURES.md](./FEATURES.md)

### Architecture Approach

采用单体 FastAPI 应用 + APScheduler 进程内调度的架构，分为 5 层：Client（Flutter）→ API（FastAPI Routers）→ Service（业务逻辑）→ Ingestion（RSS/爬虫/AI 摘要，后台任务）→ Data（PostgreSQL + FCM）。项目结构分为 `backend/`（FastAPI 单体）和 `mobile/`（Flutter 应用）两个顶层目录。

**Major components:**
1. **FastAPI Application** — REST API、认证鉴权、业务逻辑，routers 极薄只做分发
2. **Ingestion Layer** — RSS Fetcher + Web Scraper + Normalizer + Dedup Engine + AI Summarizer，通过 APScheduler 定时调度
3. **Notification Service** — FCM 主题推送，用户订阅话题时自动加入 FCM 主题
4. **PostgreSQL + JSONB** — 结构化数据 + 非结构化元数据存储

**Key patterns:**
- FastAPI lifespan + APScheduler 集成（进程内调度，无需消息队列）
- RSS 优先 + 爬虫补充的双通道采集
- 分层去重：GUID/URL → 内容哈希(SHA-256) → SimHash(后期)
- AI 摘要异步队列：先入库标记 pending_summary，后台批量调用 AI
- FCM 主题推送：按话题推送，非逐用户推送

**Scaling path:** 0-100 用户单进程足够 → 100-1K 持久化 APScheduler → 1K-10K 拆分独立 worker → 10K+ CDN + 读写分离

详见: [ARCHITECTURE.md](./ARCHITECTURE.md)

### Critical Pitfalls

研究识别了 10 个关键陷阱，按严重程度排序：

1. **AI API 成本失控** — 每篇文章都调 API，$50 预算几天耗尽。预防：token 预算系统 + 先去重再摘要 + prompt caching + 成本监控 dashboard。必须在 Phase 1 就建立。
2. **内容去重失败** — 同一新闻被 10 家媒体报道，用户看到 10 条重复摘要。预防：多层去重（URL → 内容哈希 → SimHash）+ 事件聚类。MVP 至少实现前两层。
3. **爬虫被反爬封锁** — Cloudflare 等反爬系统几天内全面封锁。预防：RSS 优先策略（已采用），爬虫仅作兜底，尊重 robots.txt。
4. **RSS 源可靠性衰减** — feed URL 静默变更，3-6 个月后大量源失效。预防：feed 健康监控 + 自动降级 + 告警机制。
5. **版权纠纷** — AI 摘要"过于详细"等同于复制。预防：摘要不超过 2-3 句话 + 不复制原文 + 来源归属 + DMCA 响应流程。
6. **推送通知疲劳** — 每天 50+ 推送导致用户卸载。预防：频率上限（默认 3-5 条/天）+ 智能聚合 + 分级推送策略。
7. **GDPR 合规疏忽** — 未实施"隐私设计"。预防：数据最小化 + 用户数据删除功能 + DPA 签署。
8. **应用商店审核被拒** — Apple 以"功能不足"拒绝。预防：突出 AI 独特价值 + 内容过滤 + 预留 2-4 周审核缓冲。
9. **数据库设计缺陷** — 通用 CRUD 模式不适应信息聚合的特殊查询。预防：articles/events/summaries 分表 + 时间序列索引 + JSONB GIN 索引。
10. **免费增值转化陷阱** — 免费用户成本远超预期。预防：精确计算每用户成本 + 免费层硬性成本上限 + 功能差异化。

详见: [PITFALLS.md](./PITFALLS.md)

## Implications for Roadmap

基于研究发现，建议分 5 个阶段推进：

### Phase 1: Foundation + Ingestion Core
**Rationale:** 所有后续功能依赖数据采集管道和基础架构。这是最关键也最危险的阶段——AI 成本控制、去重、RSS 监控三个核心陷阱都在此阶段预防。
**Delivers:** 可运行的后端服务，能从 RSS 源采集、去重、生成 AI 摘要并存储
**Addresses:** Content aggregation, AI-generated summaries, Source attribution
**Avoids:** AI API 成本失控（建立 token 预算）、去重失败（多层去重）、RSS 衰减（健康监控）、版权风险（摘要 prompt 设计）
**Key work:**
- PostgreSQL schema 设计（users, topics, items, sources, events）
- FastAPI app skeleton + config + Supabase 连接
- Auth（邮箱注册登录 + Supabase Auth）
- RSS Fetcher (feedparser + httpx async)
- Normalizer + Dedup Engine (GUID/URL + SHA-256)
- AI Summarizer (GPT-4o-mini, 异步队列)
- APScheduler 集成（FastAPI lifespan）
- Feed 健康监控
- 成本监控 dashboard

### Phase 2: User System + Subscription
**Rationale:** 用户系统是个性化、订阅、推送的前提。去重和采集管道稳定后，可以开始构建用户交互层。
**Delivers:** 完整的用户账户系统和话题订阅功能
**Addresses:** User accounts (OAuth), Topic/interest subscription, Article save/bookmark
**Avoids:** GDPR 合规疏忽（数据删除功能）、免费增值转化陷阱（成本计算）
**Key work:**
- Google/Apple OAuth 集成（Supabase Auth）
- 话题 CRUD API + 用户订阅管理
- 书签/收藏功能
- 用户设置页面
- 免费/付费层基础架构
- 数据导出/删除功能（GDPR）

### Phase 3: Flutter Mobile App
**Rationale:** API 定义好后可独立开发移动端。Phase 1-2 提供了稳定的后端 API，Phase 3 专注于前端体验。
**Delivers:** 可在 iOS/Android 上运行的完整移动应用
**Addresses:** Cross-platform, Personalized feed, Search, Offline reading
**Avoids:** 应用商店审核被拒（突出 AI 价值 + 内容过滤）
**Key work:**
- Flutter app skeleton + Riverpod 状态管理 + go_router 路由
- 话题订阅 UI
- 信息流浏览 UI（卡片式布局）
- 搜索功能
- 个人设置页面
- 离线缓存（最近摘要）
- 内容过滤机制（敏感内容检测）
- App Store / Google Play 审核准备

### Phase 4: Push Notifications + Daily Briefing
**Rationale:** 推送是留存的关键，但必须在用户系统和内容管道都稳定后实施。推送策略设计直接影响用户留存。
**Delivers:** 智能推送通知系统 + 每日综合摘要
**Addresses:** Push notifications, Daily briefing, Smart notification filtering, Share to external
**Avoids:** 推送通知疲劳（频率控制 + 聚合推送）
**Key work:**
- FCM 集成（Flutter 端 + 后端 firebase-admin）
- 推送频率控制系统（每用户每天上限）
- 智能聚合推送（同一话题合并）
- 每日摘要生成 + 定时推送
- 分享功能（原生 share sheet）
- 推送效果监控

### Phase 5: Polish + Launch Prep
**Rationale:** 功能完整后的打磨阶段，准备正式上线。
**Delivers:** 生产就绪的应用，通过应用商店审核
**Addresses:** 应用商店审核、性能优化、用户体验打磨
**Key work:**
- 性能优化（信息流查询 < 200ms）
- 错误处理和边界情况完善
- 应用商店审核材料准备
- 隐私政策和服务条款
- DMCA 响应流程文档
- 监控和告警系统

### Phase Ordering Rationale

- **Phase 1 必须最先：** 数据采集管道是所有内容的来源，AI 成本控制和去重是"不可事后补救"的架构决策。PITFALLS.md 明确指出 5 个 critical pitfalls 中有 4 个需要在 Phase 1 预防。
- **Phase 2 紧随其后：** 用户系统是个性化的前提，但依赖 Phase 1 的数据模型设计。
- **Phase 3 可与 Phase 2 部分并行：** API 定义好后移动端可独立开发，但建议 Phase 2 完成核心 API 后再开始。
- **Phase 4 放在最后功能阶段：** 推送依赖用户系统（订阅关系）和内容管道（新内容检测），且推送策略设计直接影响留存。
- **Phase 5 是收尾：** 性能优化、审核准备、文档完善。

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Supabase Auth + SQLAlchemy async 集成的具体模式、feedparser 对非标准 feed 的容错处理、AI prompt engineering for summaries
- **Phase 3:** Flutter Riverpod 3.x 最佳实践、go_router ShellRoute 实现、离线缓存策略
- **Phase 4:** FCM topic subscription 与后端同步机制、推送频率控制的具体实现

Phases with standard patterns (skip research-phase):
- **Phase 2:** CRUD + OAuth 是标准模式，Supabase Auth 文档完善
- **Phase 5:** 性能优化、审核准备是通用流程

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 基于 Context7 官方文档验证，版本号和 API 均已确认。成本估算基于官方定价。 |
| Features | MEDIUM | 竞品分析覆盖 9 款产品，功能分类可靠。但用户对 NewsFlow 具体功能的需求未验证，Tier 2/3 功能的市场接受度不确定。 |
| Architecture | HIGH | 单体 FastAPI + APScheduler 是独立开发者的成熟模式。架构模式（异步摘要队列、分层去重、FCM 主题推送）有充分的技术文档支撑。 |
| Pitfalls | MEDIUM | 基于行业案例（AP v. Meltwater、Artifact 关停）和已知模式。部分陷阱（如反爬封锁程度、RSS 衰减速率）需要实际运营数据验证。 |

**Overall confidence:** MEDIUM-HIGH

技术栈和架构的置信度高（官方文档验证），功能优先级和陷阱识别的置信度中等（竞品分析 + 行业案例，但缺少本项目的用户验证数据）。

### Gaps to Address

- **用户验证:** 功能优先级基于竞品分析推断，未经目标用户验证。建议 Phase 3 前通过小规模用户访谈确认 MVP 功能优先级。
- **AI 摘要质量:** GPT-4o-mini 的摘要质量是否满足用户期望需要实际测试。建议 Phase 1 建立摘要质量评分机制。
- **RSS 源覆盖率:** 未调研目标用户关注的信息源是否有良好的 RSS 支持。建议 Phase 1 建立 "已验证 RSS 源" 数据库。
- **国内用户支持:** 如需支持国内用户，后端部署、AI API、推送服务全部需要替换（详见 STACK.md 的国内方案）。当前方案面向海外市场。
- **事件聚类:** Multi-source synthesis 依赖的事件聚类技术复杂度高，Phase 1 不实现但数据模型需预留扩展空间。

## Sources

### Primary (HIGH confidence)
- Context7: /websites/flutter_dev — Flutter 状态管理、Firebase 集成
- Context7: /fastapi/fastapi — FastAPI 0.128.x API、lifespan、BackgroundTasks
- Context7: /anthropics/anthropic-sdk-python — Claude API、Haiku 4.5 定价
- Context7: /openai/openai-python — GPT-4o-mini API、streaming
- Context7: /firebase/firebase-admin-python — FCM 推送、topic 订阅
- Context7: /websites/sqlalchemy_en_20 — async session、asyncpg
- Context7: /kurtmckee/feedparser — RSS 解析 API
- Context7: /websites/alembic_sqlalchemy — async 迁移模板
- Context7: /supabase/supabase-flutter — Flutter SDK 集成
- Anthropic Models Page — Claude Haiku 4.5 定价确认
- Supabase Pricing — Free tier 详情

### Secondary (MEDIUM confidence)
- Inoreader Features — 竞品功能分析
- SmartNews — 多视角报道模式
- Artifact (Wikipedia) — AI 新闻应用失败案例分析
- Apple App Store Review Guidelines 4.2 — 审核要求

### Tertiary (LOW confidence)
- AP v. Meltwater (2013) — 新闻聚合版权判例（法律边界仍有不确定性）
- EU Copyright Directive Article 15 — 欧盟"链接税"（实施细节因国家而异）
- hiQ v. LinkedIn (2022) — 公开数据爬取法律边界

---
*Research completed: 2026-05-08*
*Ready for roadmap: yes*
