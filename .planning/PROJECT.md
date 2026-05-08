# NewsFlow

## What This Is

一款 AI 驱动的全源信息聚合 App。用户订阅感兴趣的话题（新闻、股票、演唱会等），系统从全网爬取信息并通过 AI 汇总为简洁摘要推送给用户。面向全球通用信息消费者，先海外后国内。

## Core Value

用户只需订阅感兴趣的话题，就能高效获取全网最新信息的 AI 摘要——无需自己逐个网站浏览。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 用户可通过分类浏览、关键词、自定义 RSS/URL、AI 推荐四种方式添加订阅
- [ ] 系统从全网爬取信息（RSS 优先 + 爬虫补充），高频更新（15-60 分钟）
- [ ] AI 自动生成每条信息的简洁摘要
- [ ] 综合信息流 + 可切换单主题视图的混合浏览模式
- [ ] 卡片式低密度信息展示（标题 + 来源 + 时间）
- [ ] 用户注册支持邮箱 + Google/Apple 登录
- [ ] 免费用户：有限订阅数（如 5 个）、基础摘要、每日查看限制
- [ ] 付费用户：无限订阅、深度 AI 分析、优先推送
- [ ] 推送通知：话题重大更新、每日定时摘要、异常/突发事件
- [ ] AI 内容审核 + 人工兜底
- [ ] 摘要 + 链接跳转（不缓存全文），尊重版权

### Out of Scope

- AI 对话追问 — v1 只做摘要，v2 扩展
- 国内上架 — 先海外，国内版后续独立规划
- 广告模式 — 采用免费增值 + 订阅制
- 全文缓存 — 只展示摘要和链接，避免版权风险

## Context

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Flutter |
| 后端 | Python FastAPI |
| AI | 云 API (Claude Haiku / GPT-4o-mini 用于摘要，大模型留给付费深度分析) |
| 数据库 | PostgreSQL（结构化数据 + JSONB 存非结构化内容） |
| 推送 | Firebase Cloud Messaging |
| 爬虫 | RSS 优先 + 传统爬虫（Scrapy/BeautifulSoup）补充 |

### 信息源覆盖

- 主流媒体和社交平台（新闻网站、微博、Twitter/X、Reddit）
- 垂直数据源（股票行情 API、票务平台、政府公告）
- 用户自定义 RSS/URL

### UI 设计风格

极简克制，类似 Notion/Linear。卡片式低密度信息流，每条信息展示标题 + 来源 + 时间，让用户专注于内容本身。

### 推送策略

- 话题重大更新时推送
- 每日定时摘要（如早上 8 点）
- 异常/突发事件即时推送
- 无默认静默时段，用户可自行关闭

## Constraints

- **预算**: 月支出 < $50，优先使用免费层和低成本方案
- **合规**: GDPR 优先，数据存海外服务器
- **版权**: 仅展示摘要 + 链接跳转，不缓存全文
- **独立开发**: 一人全栈，需控制复杂度，优先核心功能
- **市场**: 先海外再国内，国内版需独立合规方案（ICP 备案等）

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RSS 优先 + 爬虫补充 | RSS 标准化程度高、稳定性好，爬虫覆盖无 RSS 的源 | — Pending |
| 摘要用小模型、深度分析用大模型 | 控制成本，$50/月预算下平衡质量和费用 | — Pending |
| PostgreSQL + JSONB | 一套数据库兼顾结构化和非结构化数据，减少运维复杂度 | — Pending |
| 先海外再国内 | 国内合规成本高（ICP 备案、数据本地化），先验证产品 | — Pending |
| 摘要 + 链接跳转 | 避免版权纠纷，降低存储成本 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-08 after initialization*
