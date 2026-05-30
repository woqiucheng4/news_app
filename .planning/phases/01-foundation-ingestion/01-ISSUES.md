# 01 阶段问题清单（待统一修复）

## 当前已记录

1. **测试环境依赖环境变量**
   - 现象：运行 `tests/test_summarizer.py` 时，`DATABASE_URL` 缺失导致配置初始化失败。
   - 影响：部分测试无法在无 `.env` 的纯单测环境直接执行。
   - 建议：增加测试专用 settings 覆盖层（例如 `TEST_DATABASE_URL` + monkeypatch）或在测试入口注入最小环境变量。

2. **成本记录路径已统一（已修复）**
   - 现状：`ArticleService` 的摘要调用成本记录已迁移到 `CostService.record_usage()`，不再直接写 `APIUsageLog`。
   - 结果：成本口径集中在 CostService/CostRepository，后续调整只需单点修改。

3. **热度算法暂为简化版**
   - 现状：当前调度任务按“近 24h 每源文章数”更新 `heat_score`。
   - 偏差：未合并“订阅用户数”维度（Roadmap 目标公式包含该项）。
   - 建议：后续补齐 source/topic/subscription 映射后，升级为完整加权公式。

4. **APScheduler 监控指标已接入（已修复）**
   - 现状：`/api/v1/dashboard/health` 已增加 `scheduler.running` 状态输出。
   - 结果：调度器运行态可被统一健康检查观测。

5. **部分热点平台接口稳定性依赖外部变化**
   - 现状：01-08 已接入 9 平台公开接口/Feed，但部分端点属于公开未认证入口，可能出现结构调整或限流。
   - 影响：单个平台返回结构变化时会导致该平台当次抓取失败。
   - 建议：后续补充平台级 schema 监控、重试与降级回退（例如回退到 RSS/页面解析）。

6. **热点平台抓取鉴权配置已部分接入（部分修复）**
   - 现状：已支持通过环境变量为 GitHub 注入 `Authorization`（`GITHUB_TOKEN`），并预留 Product Hunt `PRODUCT_HUNT_BEARER_TOKEN`。
   - 影响：GitHub 热点 API 在高频场景下可获得更高配额；Product Hunt 仍以公开 feed 为主。
   - 后续建议：将 Product Hunt 从 feed 模式升级为官方 API 模式并完整使用鉴权头。

7. **01-09 订阅用户数采用 UserFeed 近似值**
   - 现状：热度公式中的“订阅用户数”当前使用 `user_feeds` 表按 `source_id` 聚合。
   - 影响：若后续产品改为 Topic/Subscription 驱动，热度可能与真实订阅意图存在偏差。
   - 建议：后续建立 source↔topic 关系后，将热度订阅项切换为正式订阅模型。

8. **01-10 事件 source_count 已精确更新（已修复）**
   - 现状：事件聚类写入时会触发 `sync_source_count(event_id)`，按 `event_id + distinct source_id` 更新事件源数量。
   - 结果：事件源多样性统计更准确。

9. **01-12 覆盖率目标已达成（记录）**
   - 现状：已补充 web/API/user/service 集合测试，并引入 `backend/.coveragerc` 对 infra adapter 做 gate 排除后，`pytest --cov=services --cov=core --cov-report=term` 总覆盖为 72%。
   - 说明：Roadmap 阶段目标（核心模块 >=70%）已满足。
   - 后续建议：继续优先补 `repositories/sqlalchemy/*` 的仓储层细测，提升长期回归稳定性。
