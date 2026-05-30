# 02-03 Validation — 内容搜索

## Scope

- Phase: 02 用户系统 + 订阅管理
- Plan item: 02-03
- Target requirement:
  - **USER-07**：用户可搜索已聚合的内容

## Delivered API Capability

### USER-07：内容搜索

- `GET /api/v1/articles/search?q=&limit=`
  - 三字段 ILIKE 模糊匹配（`title` / `content` / `summary`）
  - 排除已删除文章（`is_deleted = false`）
  - 按 `published_at` 倒序，limit 截断
  - 大小写不敏感
  - 公开端点（无需鉴权）

### 与 02-02 话题搜索的协作

| 端点 | Plan | 职责 |
|---|---|---|
| `GET /articles/search?q=` | 02-03 | 搜文章内容（title + content + summary） |
| `GET /subscriptions/topics?q=` | 02-02 | 搜话题（订阅入口） |

两者在前端可组合为"全局搜索"双 Tab 体验，详见 [`02-03-FLUTTER_SEARCH_SCAFFOLD.md`](./02-03-FLUTTER_SEARCH_SCAFFOLD.md)。

## Authentication Contract

- 当前**无需鉴权**（与 `/articles/trending`、`/articles/{id}` 一致）
- 决策依据：搜索结果不包含用户上下文字段，与个性化 `/feed` 端点形成对照
- 详见 [`02-03-API_CONTRACT.md`](./02-03-API_CONTRACT.md) §Authentication

## Validation Evidence

### 现存测试覆盖

| 测试文件 | 覆盖 |
|---|---|
| `backend/tests/test_api_endpoints.py` (line 102-103) | smoke 测试：`GET /articles/search?q=ai` 返回 200 |
| `backend/tests/test_article_search.py` | 搜索语义回归：title/content/summary 命中、大小写不敏感、中文匹配、0 结果、`is_deleted` 排除、排序、limit、SQL injection 防护 |

### 现存测试缺口（Open）

⚠️ 搜索语义自动化已补齐；剩余主要是性能与能力增强项，建议在后续硬化 plan 补：

- PostgreSQL 全文索引与性能压测（`tsvector` + GIN 或 pg_trgm）
- 多关键词 AND、相关度排序、分页能力
- 公开端点限流策略与压测阈值

### 本地命令（已跑通）

```bash
cd backend
.venv/bin/pytest -q tests/test_article_search.py
.venv/bin/pytest -q tests/test_api_endpoints.py -k "articles or search"
```

### CI 等价命令（已纳入 backend-ci.yml）

```bash
pytest -q  # 全量包含 search smoke
```

## Open Hardening（USER-07 完整性强化）

| 项 | 描述 | 严重度 | 建议归属 |
|---|---|---|---|
| **全文索引** | 当前 `ILIKE '%q%'` 在大数据量（>10万 articles）下性能急剧退化；应改用 PostgreSQL `tsvector` + GIN index 或 pg_trgm | 🔴 性能阻塞 | 02-03 后续硬化 plan |
| **多关键词 AND** | 当前 "AI Apple" 仅匹配连续子串；应支持空格分隔的 AND 语义 | 🟡 体验 | 同上 |
| **相关度排序** | 当前按 `published_at` 排序，应支持 `ts_rank` 相关度排序（可加 `sort` 参数） | 🟡 体验 | 同上 |
| **分页支持** | 当前仅 `limit`，无 `offset` / `cursor` | 🟡 体验 | 同上 |
| **分类筛选** | `q + category=tech` 组合搜索未支持 | 🟡 体验 | 同上 |
| **tags 参与匹配** | 当前 tags 字段未参与搜索 | 🟢 增强 | 同上 |
| **搜索历史** | 客户端搜索历史 / 推荐查询未实现 | 🟢 增强 | Phase 3 客户端 |
| **拼写纠正** | "did you mean..." 类提示未实现 | 🟢 增强 | 同上 |
| **rate limiting** | 公开端点未限流，存在被刷风险 | 🟡 安全 | 安全硬化 plan |

### Performance Budget

| 项 | 当前 | 目标 |
|---|---|---|
| P95 响应时间（10K articles） | 待测 | < 200ms |
| P95 响应时间（100K articles） | ❌ ILIKE 不可用 | 引入全文索引后 < 500ms |

## GDPR / Compliance Notes

- 搜索结果**不包含**用户私有数据（不查询 `users` / `subscriptions` / `notifications` 表）
- 搜索行为**不记录**到用户日志（暂未引入搜索行为追踪；如后续要做"搜索历史"，需写 PRD 评估隐私影响）
- 已删除文章（`is_deleted=true`）严格排除，符合"删除请求即时生效"语义

## Notes for Frontend Integration

- Flutter 接入完整骨架：[`02-03-FLUTTER_SEARCH_SCAFFOLD.md`](./02-03-FLUTTER_SEARCH_SCAFFOLD.md)
- 客户端建议：
  - 输入防抖 350ms（balance UX 与 QPS）
  - 使用 `CancelToken` 取消旧请求
  - `q.length === 0` 时**不发请求**，避免 422
  - 客户端 `limit` 不超过 50（性能预算）
- 与 02-02 话题搜索结合做双 Tab UI

## CI / Repo Infrastructure

复用 02-01 / 02-02 已落地的工程基础设施：

| 工件 | 路径 | 02-03 相关 |
|---|---|---|
| Backend CI | `.github/workflows/backend-ci.yml` | 全量 pytest 已覆盖现有 search smoke |
| PR 模板 | `.github/PULL_REQUEST_TEMPLATE.md` | 改动 search 时建议勾选订阅/Feed surface checklist 中的字段一致性项 |
| CODEOWNERS | `.github/CODEOWNERS` | `/backend/api/v1/articles.py`、`/backend/services/article.py` 已绑定 |

## Phase Summary（02-03 收尾索引）

- 完整聚合页：[`02-03-PHASE_SUMMARY.md`](./02-03-PHASE_SUMMARY.md)
- 用途：作为本 plan item 全部产物（接口、文档、UAT）的最终索引入口。
