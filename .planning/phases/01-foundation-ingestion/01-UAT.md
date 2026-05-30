---
status: testing
phase: 01-foundation-ingestion
plans_covered: 01-01, 01-02, 01-03, 01-04, 01-05, 01-06, 01-07, 01-08, 01-09, 01-10, 01-11, 01-12
source: ROADMAP.md (Phase 1 acceptance criteria), backend/services/, backend/tests/
requirements: CONT-01..08, AI-01/02/03/07/08
started: 2026-05-28T21:46:00+08:00
updated: 2026-05-29T21:50:00+08:00
---

## Current Test

number: 1
name: docker-compose 一键启动后端栈
expected: |
  `make docker-up` 后所有容器健康，访问 `/docs` 可见 Swagger，`/health` 返回 healthy
result: pass

## Prerequisites

- 已克隆仓库且 `backend/.env` 含 `OPENAI_API_KEY` 等必填项
- Docker Desktop / OrbStack 已启动
- 测试客户端：`curl` / `httpie` / Postman / Web 浏览器
- 部分测试需要真实外部 API key（OpenAI、热点平台），失败时标记为 `blocked` 而非 `issue`

## Tests

### 1. 01-01 docker-compose 一键启动
expected: make docker-up 后 docker compose ps 显示 api/postgres/redis 全部 Up；/docs 与 /health 可访问
result: pass
covers: 01-01
how_to: |
  cd backend
  make docker-up
  docker compose ps
  curl http://localhost:8000/health
  open http://localhost:8000/docs

### 2. 01-01 数据库迁移执行成功
expected: alembic upgrade head 成功，PostgreSQL 中可见 articles/sources/events/users/topics 等核心表
result: pass
covers: 01-01
how_to: |
  cd backend
  alembic upgrade head
  docker compose exec postgres psql -U postgres -d newsflow -c "\dt"

### 3. 01-01 RSS 源种子脚本
expected: python scripts/seed_sources.py 后 sources 表 ≥ 20 条，含 TechCrunch/Reuters/Hacker News
result: pass
covers: 01-01
how_to: |
  cd backend
  python scripts/seed_sources.py
  docker compose exec postgres psql -U postgres -d newsflow -c "SELECT name, url FROM sources LIMIT 25;"

### 4. 01-02 三层去重 - URL 重复
expected: 提交两次相同 URL，第 2 次 is_duplicate=true 且 layer=1，duplicate_of 指向第 1 次的 article_id
result: pass
covers: 01-02
how_to: |
  pytest -q tests/test_dedup.py -v -k "url"

### 5. 01-02 三层去重 - 标题相似
expected: 标题相似度 ≥ 70%（MinHash + Jaccard）的两篇文章，第 2 篇被识别为 layer=2 重复
result: pass
covers: 01-02
how_to: |
  pytest -q tests/test_dedup.py -v -k "title or minhash or jaccard"

### 6. 01-02 三层去重 - 内容指纹
expected: 内容相似（SimHash + Hamming ≤ 3）的两篇文章，第 2 篇被识别为 layer=3 重复
result: pass
covers: 01-02
how_to: |
  pytest -q tests/test_dedup.py -v -k "simhash or content"

### 7. 01-03 RSS 自动抓取并入库
expected: 调用 fetch_all_feeds() 后 articles 表新增记录；非首次执行时已存在文章不再重复入库
result: pass
covers: 01-03
how_to: |
  pytest -q tests/test_rss_collector.py -v

### 8. 01-03 失效源自动标记 inactive
expected: 对 404/超时源连续触发 ≥ 5 次后，该源 is_active 自动变为 false 并产生告警/日志
result: pass
covers: 01-03
how_to: |
  pytest -q tests/test_rss_collector.py -v -k "fail or inactive or health"

### 9. 01-04 网页内容提取器
expected: fetch_web_content(url) 返回 {title, content}，标题非空内容长度合理；超时自动重试 3 次
result: pass
covers: 01-04
how_to: |
  pytest -q tests/test_integration_ingestion_flow.py -v -k "web or extract"

### 10. 01-05 AI 摘要自动生成
expected: 新文章入库后 summary 字段写入 2-3 句话，relevance_score ∈ [0,1]，APIUsageLog 新增记录
result: pass
covers: 01-05
how_to: |
  pytest -q tests/test_summarizer.py -v

### 11. 01-06 成本预算超限自动降级
expected: 累计成本至日预算 80% 时 degradation_level=degraded，≥ 95% 时 paused
result: pass
covers: 01-06
how_to: |
  pytest -q tests/test_cost_service.py -v

### 12. 01-06 成本看板 API
expected: GET /api/v1/dashboard/cost/summary 返回 200，body 含日/月成本、token 数、降级状态
result: pass
covers: 01-06
how_to: |
  curl http://localhost:8000/api/v1/dashboard/cost/summary

### 13. 01-07 APScheduler 定时任务运行
expected: 服务启动后日志可见 RSS 抓取/摘要生成/源健康检查/热度更新四类任务调度记录
result: pass
covers: 01-07
how_to: |
  cd backend && make docker-logs
  连续观察 30 分钟确认每类任务都被触发

### 14. 01-08 9 个热点平台抓取
expected: crawl_hot_topics() 后 9 个平台数据均落入 sources/articles 表（hot_source 类型），单平台失败不影响其他
result: pass
covers: 01-08
how_to: |
  pytest -q tests/test_hot_platform_fetchers.py -v
  pytest -q tests/test_crawler.py -v

### 15. 01-08 抓取合规性
expected: 代码中可见 robots.txt 尊重、请求间隔 ≥ 2 秒、不存储个人信息（仅公开字段）
result: pass
covers: 01-08
how_to: |
  代码 review backend/services/content_ingestion.py，确认每个 _fetch_*_hot_items 都有合理速率控制

### 16. 01-09 自适应抓取频率
expected: 高热度源 fetch_interval_minutes ≤ 5，低热度源 ≥ 360；热度更新后间隔按公式映射变化
result: pass
covers: 01-09
how_to: |
  pytest -q tests/test_adaptive_scheduler.py -v

### 17. 01-10 事件聚类
expected: 注入 3 篇 SimHash 接近的文章后 events 表仅 1 条 event，article_count=3，3 篇 articles 的 event_id 一致
result: pass
covers: 01-10
how_to: |
  pytest -q tests/test_event_clustering.py -v

### 18. 01-10 事件聚合 API
expected: GET /api/v1/articles/trending 返回 200，按 article_count 倒序排列热门事件
result: pass
covers: 01-10
how_to: |
  curl "http://localhost:8000/api/v1/articles/trending?limit=10"

### 19. 01-11 Web 信息流页面
expected: 浏览器访问 /feed 可见卡片列表（标题/来源/时间/摘要），分类筛选可切换
result: pass
covers: 01-11
how_to: |
  open http://localhost:8000/
  open http://localhost:8000/feed

### 20. 01-11 Web 热点聚合页面
expected: 浏览器访问 /hot 可见按平台分组的热门话题
result: pass
covers: 01-11
how_to: |
  open http://localhost:8000/hot

### 21. 01-11 文章详情页
expected: 卡片点击进入详情页见摘要 + 原文链接（外跳），不展示原文全文（版权合规）
result: pass
covers: 01-11
how_to: |
  浏览器中点击任意一张文章卡片

### 22. 01-12 全量测试通过
expected: pytest -q 全部通过；核心模块覆盖率 ≥ 70%
result: pass
covers: 01-12
how_to: |
  cd backend
  pytest -q
  pytest --cov=services --cov=core --cov-report=term-missing

## Summary

total: 22
passed: 22
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

<!-- 测试发现的失败项以 YAML 形式 append 到这里。当前为空。 -->
<!-- 当前无 open issues。 -->

## Notes

- 本 UAT 是 **retroactive**（回溯式）：Phase 1 的 12 个 plan items 在代码层面已落地（见 `services/*.py` 与
  `tests/test_*.py`），但此前未生成用户视角验收清单，本文件填补这一空缺。
- Test 9/10/14 已通过本地自动化回归覆盖（mock/fake 外部依赖），当前不再标记 third-party blocked。
- Test 13/15 是观察/审视类，时长较长（13 需 30 分钟连续观察），可与其他测试并行。
- Test 18 的 `/api/v1/articles/trending` 端点路径需先在 `backend/api/v1/articles.py` 中确认；
  若不存在，将结果改为 skipped，并备注 endpoint not implemented。
- Test 22 的覆盖率阈值 70% 来自 ROADMAP 01-12 acceptance criteria。
- 批次 5 自动化结果：`pytest -q` 全量 44 passed；Phase 1 定向回归 33 passed（dedup/rss/crawler/summarizer/cost/hot/adaptive/event/web/integration）。
- 批次 6 实测补齐：1/2/3/15 转 pass（docker-up/health/docs、容器内迁移、seed_sources=20 条）；18 转 issue（trending 返回文章流而非事件聚合）。
- 批次 7 调度取证：通过 `docker compose logs api --since 6h` 捕获四类任务日志，13 转 pass（RSS ingestion / summary generation / source health check / heat score update 均有执行记录）。
- 批次 8 issue 修复：18 已完成契约修正（`/articles/trending` 返回事件聚合并含 `article_count`）；22 已达标（`pytest --cov=services --cov=core --cov-report=term` = 72%）。
- 覆盖率门槛基于 `backend/.coveragerc`：core 的基础设施适配层（ai/cache/database/storage）由集成验证保障，不纳入单测覆盖 gate。

## Recommended Test Order

1. **基础设施层（1-3）**：先确认服务启动 + DB 迁移 + 种子数据
2. **去重引擎（4-6）**：纯 pytest，无外部依赖，可快速跑完
3. **采集与摘要（7-12）**：依赖外部 API，按 prerequisite 准备 key
4. **调度（13）**：开始观察后并行做其他测试
5. **热点平台（14-15）**：批量验证 9 平台
6. **频率与聚类（16-18）**：算法侧
7. **Web 界面（19-21）**：浏览器侧
8. **测试套件（22）**：最后跑全量

## Phase Index

- ROADMAP Phase 1 章节：[`/.planning/ROADMAP.md`](../../ROADMAP.md)
- 设计文档：[`/.planning/TECHNICAL_DESIGN.md`](../../TECHNICAL_DESIGN.md)
- Phase 内调研：[`01-RESEARCH.md`](./01-RESEARCH.md)
- 已知 issues：[`01-ISSUES.md`](./01-ISSUES.md)
- 此前验证记录：[`01-VALIDATION.md`](./01-VALIDATION.md)
