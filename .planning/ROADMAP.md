# Roadmap: NewsFlow

## Overview

NewsFlow 是一款 AI 驱动的信息聚合 App，核心价值是让用户只需订阅话题，就能高效获取全网最新信息的 AI 摘要。本路线图采用垂直 MVP 模式，5 个阶段从后端数据管道到前端应用再到商业化，每个阶段交付完整的端到端用户能力。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: 基础架构 + 内容采集管道** - 后端数据采集、去重、AI 摘要生成的完整管道
- [ ] **Phase 2: 用户系统 + 订阅管理** - 用户认证、话题订阅、GDPR 合规的完整用户能力
- [ ] **Phase 3: Flutter 移动应用** - iOS/Android 可运行的信息浏览客户端
- [ ] **Phase 4: 推送通知 + 每日简报** - 智能推送系统和每日综合摘要
- [ ] **Phase 5: 免费增值 + 上线准备** - 订阅付费体系和应用商店上线

## Phase Details

### Phase 1: 基础架构 + 内容采集管道
**Goal**: 建立可运行的后端服务，能从 RSS 源和网页自动采集、去重、生成 AI 摘要并存储
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: CONT-01, CONT-02, CONT-03, CONT-04, CONT-05, CONT-06, CONT-07, AI-01, AI-02, AI-03, AI-07, AI-08
**Success Criteria** (what must be TRUE):
  1. 用户可通过 API 添加自定义 RSS 订阅地址和任意网页 URL，系统自动定期抓取更新
  2. 系统自动检测并合并重复内容（URL 去重 + 内容哈希），用户不会看到重复信息
  3. 每条聚合信息自动生成简洁 AI 摘要，且月度 AI 成本控制在 $50 以内
  4. 系统自动监控 RSS 源健康状态，失效源产生告警
  5. 摘要仅包含 2-3 句话 + 来源链接跳转，不缓存全文，符合版权合规要求
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD
- [ ] 01-03: TBD

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
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD

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
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

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
| 1. 基础架构 + 内容采集管道 | 0/TBD | Not started | - |
| 2. 用户系统 + 订阅管理 | 0/TBD | Not started | - |
| 3. Flutter 移动应用 | 0/TBD | Not started | - |
| 4. 推送通知 + 每日简报 | 0/TBD | Not started | - |
| 5. 免费增值 + 上线准备 | 0/TBD | Not started | - |
