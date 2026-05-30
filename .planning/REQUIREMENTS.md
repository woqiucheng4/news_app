# Requirements: NewsFlow

**Defined:** 2026-05-08
**Core Value:** 用户只需订阅感兴趣的话题，就能高效获取全网最新信息的 AI 摘要——无需自己逐个网站浏览。

## v1 Requirements

### Content Aggregation (内容聚合)

- [ ] **CONT-01**: 系统可自动解析和抓取预置 RSS 订阅源
- [ ] **CONT-02**: 用户可添加自定义 RSS 订阅地址
- [ ] **CONT-03**: 用户可添加任意网页 URL，系统定期爬取更新
- [ ] **CONT-04**: 系统按用户关键词从多个源搜索并聚合相关内容
- [ ] **CONT-05**: 系统自动检测并合并重复内容（URL 去重 → 标题相似度 → 内容指纹）
- [ ] **CONT-06**: RSS 源健康监控，失效源自动告警
- [ ] **CONT-07**: 内容采集高频更新（热门话题 15-60 分钟）
- [ ] **CONT-08**: 系统每 15-30 分钟从各大平台（Hacker News、Reddit、GitHub、微博、知乎、百度等）抓取热点/热搜数据，跨平台聚合同一事件，生成 AI 摘要展示；采集遵守法律合规清单（尊重 robots.txt、不突破技术防护、仅取元数据、不存储个人信息、保留访问日志）

### AI Features (AI 功能)

- [ ] **AI-01**: 每条聚合信息自动生成简短 AI 摘要
- [ ] **AI-02**: AI 摘要使用低成本模型（GPT-4o-mini）控制预算
- [ ] **AI-03**: AI 摘要结果缓存，避免重复调用
- [ ] **AI-04**: 按订阅主题生成每日信息概览（每日简报）
- [ ] **AI-05**: 付费用户可获得趋势分析、情感判断、关联事件等深度洞察
- [ ] **AI-06**: 付费用户可获得多源报道的综合摘要（事件聚类）
- [ ] **AI-07**: AI 内容审核，自动过滤敏感/违规内容
- [ ] **AI-08**: 版权合规的摘要 prompt 设计（摘要 + 链接跳转，不缓存全文）

### User System (用户系统)

- [ ] **USER-01**: 用户可通过邮箱注册和登录
- [ ] **USER-02**: 用户可通过 Google 账号登录
- [ ] **USER-03**: 用户可通过 Apple 账号登录
- [ ] **USER-04**: 用户可浏览分类目录并订阅感兴趣的话题
- [ ] **USER-05**: 用户可通过关键词添加订阅
- [ ] **USER-06**: 用户可管理订阅列表（添加、删除、排序）
- [ ] **USER-07**: 用户可搜索已聚合的内容
- [ ] **USER-08**: 用户可设置个人偏好（通知频率、显示设置等）
- [ ] **USER-09**: 用户数据符合 GDPR 规范，支持数据导出和删除

### Distribution & Push (分发与推送)

- [ ] **DIST-01**: 综合信息流展示所有订阅的最新信息
- [ ] **DIST-02**: 可切换到单个主题的独立视图
- [ ] **DIST-03**: 卡片式低密度信息展示（标题 + 来源 + 时间）
- [ ] **DIST-04**: 重大更新即时推送通知
- [ ] **DIST-05**: 每日定时推送今日摘要
- [ ] **DIST-06**: 异常/突发事件即时推送
- [ ] **DIST-07**: 推送频率控制，防止通知疲劳

### Freemium (免费增值)

- [ ] **FREE-01**: 免费用户可订阅有限数量的话题（上限待定）
- [ ] **FREE-02**: 免费用户可查看基础摘要
- [ ] **FREE-03**: 免费用户有每日查看次数限制
- [ ] **FREE-04**: 付费用户可无限订阅话题
- [ ] **FREE-05**: 付费用户可使用深度 AI 分析功能
- [ ] **FREE-06**: 付费用户享有优先推送
- [ ] **FREE-07**: 订阅付费流程（应用内购买）

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### AI Conversation (AI 对话)

- **AIC-01**: 用户可就某条信息跟 AI 对话追问细节
- **AIC-02**: 用户可对比不同来源对同一事件的报道
- **AIC-03**: AI 可根据用户追问生成定制化分析报告

### Advanced Features (高级功能)

- **ADV-01**: 离线阅读模式（缓存最近摘要）
- **ADV-02**: 音频播报（TTS 朗读摘要）
- **ADV-03**: 多视角分析（同一事件的不同立场解读）
- **ADV-04**: 智能推荐订阅（基于用户行为推荐新话题）

## Out of Scope

| Feature | Reason |
|---------|--------|
| 社交功能（评论、分享、关注用户） | Artifact 失败警示：社交化偏离核心价值，增加复杂度 |
| 全文缓存 | 版权风险，仅展示摘要 + 链接跳转 |
| 国内市场 | 合规成本高（ICP 备案、数据本地化），先海外验证 |
| 实时聊天 | 高复杂度，非核心信息聚合价值 |
| 视频内容 | 存储/带宽成本高，v1 聚焦文本 |
| 广告模式 | 采用免费增值 + 订阅制 |
| 自建 AI 模型 | 云 API 成本可控且质量有保障 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONT-01 | Phase 1 | Pending |
| CONT-02 | Phase 1 | Pending |
| CONT-03 | Phase 1 | Pending |
| CONT-04 | Phase 1 | Pending |
| CONT-05 | Phase 1 | Pending |
| CONT-06 | Phase 1 | Pending |
| CONT-07 | Phase 1 | Pending |
| CONT-08 | Phase 1 | Pending |
| AI-01 | Phase 1 | Pending |
| AI-02 | Phase 1 | Pending |
| AI-03 | Phase 1 | Pending |
| AI-04 | Phase 4 | Pending |
| AI-05 | Phase 5 | Pending |
| AI-06 | Phase 5 | Pending |
| AI-07 | Phase 1 | Pending |
| AI-08 | Phase 1 | Pending |
| USER-01 | Phase 2 | Pending |
| USER-02 | Phase 2 | Pending |
| USER-03 | Phase 2 | Pending |
| USER-04 | Phase 2 | Pending |
| USER-05 | Phase 2 | Pending |
| USER-06 | Phase 2 | Pending |
| USER-07 | Phase 2 | Pending |
| USER-08 | Phase 3 | Pending |
| USER-09 | Phase 2 | Pending |
| DIST-01 | Phase 3 | Pending |
| DIST-02 | Phase 3 | Pending |
| DIST-03 | Phase 3 | Pending |
| DIST-04 | Phase 4 | Pending |
| DIST-05 | Phase 4 | Pending |
| DIST-06 | Phase 4 | Pending |
| DIST-07 | Phase 4 | Pending |
| FREE-01 | Phase 5 | Pending |
| FREE-02 | Phase 5 | Pending |
| FREE-03 | Phase 5 | Pending |
| FREE-04 | Phase 5 | Pending |
| FREE-05 | Phase 5 | Pending |
| FREE-06 | Phase 5 | Pending |
| FREE-07 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0

---
*Requirements defined: 2026-05-08*
*Last updated: 2026-05-08 after roadmap creation*
