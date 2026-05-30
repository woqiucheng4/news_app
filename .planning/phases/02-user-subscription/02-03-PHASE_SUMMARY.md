# 02-03 Phase Summary（收尾索引页）

> Phase: 02 用户系统 + 订阅管理
> Plan item: 02-03 — 内容搜索（Article Search）
> 状态：✅ 接口已落地、文档链路成型；自动化测试已补齐核心搜索语义，UAT 已清零（15/15 pass）；性能与功能强化项移交后续硬化 plan。

---

## 1. 范围与目标

| 项 | 内容 |
|---|---|
| Phase Goal | 让用户可以按关键词搜索已聚合的文章内容 |
| Requirement 覆盖 | **USER-07**：用户可搜索已聚合的内容 |
| 上游契约 | `.planning/REQUIREMENTS.md`、`.planning/PRD.md`、`.planning/TECHNICAL_DESIGN.md` |
| 下游消费方 | Flutter 客户端搜索页（双 Tab：文章 + 话题） |

> 注：本 plan **仅**覆盖 USER-07。话题搜索（02-02 `GET /subscriptions/topics?q=`）与本 plan 协作但不在范围内。

---

## 2. 后端接口产物（Single Source of Truth）

接口契约统一登记于 [`02-03-API_CONTRACT.md`](./02-03-API_CONTRACT.md)，对应实现位于 `backend/api/v1/articles.py::search_articles` + `backend/services/article.py::search_articles` + `backend/repositories/sqlalchemy/article.py::ArticleRepository.search`。

| # | Method & Path | Auth | 用途 | 关联需求 |
|---|---|---|---|---|
| 1 | `GET /api/v1/articles/search` | **No** | 关键词搜文章（title + content + summary） | USER-07 |

### 关键参数

| 字段 | 类型 | 默认 | 约束 |
|---|---|---|---|
| `q` | string (query) | required | length 1-200 |
| `limit` | int (query) | 20 | 1-100 |

### 搜索语义

- 三字段 ILIKE 子串匹配：`title` / `content` / `summary`
- 排除已删除文章（`is_deleted = false`）
- 按 `published_at` DESC 排序，limit 截断
- 大小写不敏感（PostgreSQL `ILIKE`）
- 中英文均支持子串匹配，**不做分词、不支持 AND、不支持相关度排序**（Open Hardening）

### 设计决策

- **公开端点**（无鉴权）：与 `/articles/trending`、`/articles/{id}` 一致；与个性化的 `/feed`（需鉴权）形成对照
- **不分页**：仅 `limit` 截断，无 `offset` / `cursor`（Open Hardening）

---

## 3. Flutter 接入文档

| 文档 | 作用 |
|---|---|
| [`02-03-FLUTTER_SEARCH_SCAFFOLD.md`](./02-03-FLUTTER_SEARCH_SCAFFOLD.md) | 搜索接入完整骨架：DTO 复用 / 防抖 + 取消的 Notifier / 双 Tab 搜索页 UI |

### 关键技术点

| 点 | 实现要点 |
|---|---|
| DTO 复用 | 复用 02-02 已生成的 `ArticleDto`，无需重复定义 |
| 防抖 | `Timer` 350ms，避免每次按键发请求 |
| 取消 | `CancelToken` 链，输入变化时取消 in-flight 请求 |
| 双 Tab | 同一搜索栏并行调 `/articles/search` 和 `/subscriptions/topics?q=` |
| 空态 | `q=''` 时不发请求，UI 显示提示文案 |

---

## 4. 验证证据（Validation Evidence）

详见 [`02-03-VALIDATION.md`](./02-03-VALIDATION.md)。关键摘要：

### 现存自动化测试（已补齐核心语义）

| 测试文件 | 覆盖 |
|---|---|
| `backend/tests/test_api_endpoints.py` | smoke：`q=ai` 返回 200（仅 1 项） |
| `backend/tests/test_article_search.py` | 搜索语义回归：命中 / 大小写 / 中文 / 0 结果 / 删除排除 / 排序 / limit / 注入防护 |

### UAT（15/15 pass）

[`02-03-UAT.md`](./02-03-UAT.md) 覆盖：
- Tests 1-4：基础功能（标题/正文/大小写/中文命中）
- Tests 5-8：结果集行为（0 结果、删除排除、排序、limit 截断）
- Tests 9-12：请求校验（422 边界：空查询、超长、limit 越界、缺失必填）
- Test 13：SQL injection 防护回归
- Tests 14-15：契约确认（无鉴权、schema 完整性）

### 自动化补齐结果（批次 4）

已新增 `backend/tests/test_article_search.py`，覆盖：
- 关键词命中 title / content / summary 各场景
- `is_deleted` 过滤
- 排序与 limit 行为
- 大小写不敏感与中文匹配
- 0 结果返回 `[]`
- SQL injection 防护（参数化 SQL）

---

## 5. Open Hardening（USER-07 完整性强化）

| 项 | 严重度 | 描述 | 建议归属 |
|---|---|---|---|
| **全文索引** | 🔴 性能 | `ILIKE '%q%'` 在 >10万 articles 下性能崩盘；改 PostgreSQL `tsvector` + GIN | 02-03 后续硬化 plan |
| **多关键词 AND** | 🟡 体验 | 当前仅子串匹配，"AI Apple" ≠ "AI" + "Apple" | 同上 |
| **相关度排序** | 🟡 体验 | 当前按 `published_at` 排，应支持 `ts_rank` 按相关度排 | 同上 |
| **分页支持** | 🟡 体验 | 仅 `limit` 截断，无 `offset` / `cursor` | 同上 |
| **分类筛选** | 🟡 体验 | `q + category` 组合搜索未支持 | 同上 |
| **tags 参与匹配** | 🟢 增强 | 当前 tags 字段未参与 | 同上 |
| **rate limiting** | 🟡 安全 | 公开端点未限流，刷接口风险 | 安全硬化 plan |
| **搜索历史 / 推荐查询** | 🟢 增强 | 客户端体验项 | Phase 3 |
| **拼写纠正** | 🟢 增强 | "did you mean..." | 同上 |

> 详见 [`02-03-VALIDATION.md`](./02-03-VALIDATION.md) §Open Hardening。

---

## 6. 文档地图（02-03 全部产物索引）

```
.planning/phases/02-user-subscription/
├── 02-03-API_CONTRACT.md             # search 接口契约
├── 02-03-VALIDATION.md               # 验证证据 + Open Hardening
├── 02-03-UAT.md                      # 15 项用户视角验收场景
├── 02-03-FLUTTER_SEARCH_SCAFFOLD.md  # Flutter 双 Tab 搜索完整骨架
└── 02-03-PHASE_SUMMARY.md            # ← 本文（收尾索引页）

backend/
├── api/v1/articles.py                # search_articles 路由
├── services/article.py               # ArticleService.search_articles
├── repositories/sqlalchemy/article.py # ArticleRepository.search (ILIKE 三字段)
├── tests/test_api_endpoints.py       # search smoke 测试
└── tests/test_article_search.py      # search 语义回归测试
```

---

## 7. Definition of Done（02-03 收尾判定）

- [x] `GET /articles/search` 接口已交付并通过 smoke 测试
- [x] 三字段 ILIKE 匹配 + 已删除排除 + published_at 排序 + limit 截断
- [x] 大小写不敏感、中英文子串匹配
- [x] 公开端点设计决策已显式记录（与 `/feed` 鉴权语义对照）
- [x] API 契约文档（`02-03-API_CONTRACT.md`）与代码字段一一对齐
- [x] Flutter 搜索接入文档（含防抖 + 取消 + 双 Tab 模板）
- [x] UAT 文件（`02-03-UAT.md`）15 项场景成 SDK 可识别格式
- [x] CI 已隐含覆盖（02-02 backend-ci 全量 pytest 包含 smoke）
- [x] CODEOWNERS 已绑定 `articles.py` / `services/article.py`
- [x] 本文（PHASE_SUMMARY.md）作为收尾索引页发布
- [x] 专门测试套件 `test_article_search.py`
- [ ] **PostgreSQL 全文索引**（移交 Open Hardening）
- [ ] **多关键词 AND / 相关度排序 / 分页**（移交 Open Hardening）

---

## 8. 已知 Follow-up（移交后续 plan / phase）

| 项 | 类型 | 建议归属 |
|---|---|---|
| 引入 PostgreSQL `tsvector` + GIN 全文索引 | Performance | 02-03 后续硬化 plan |
| 多关键词 AND + 相关度排序 + 分页 | Feature | 同上 |
| 公开搜索端点速率限制 | Security | 安全硬化 plan |
| Flutter 搜索页实际实现 + 历史/推荐查询 | Frontend | Phase 3 |

---

## 9. 快速参考（Cheat Sheet）

```bash
# Backend 联调
cd backend && make demo-up

# 端点冒烟测试
curl "http://localhost:8000/api/v1/articles/search?q=AI&limit=20"

# 中文测试
curl "http://localhost:8000/api/v1/articles/search?q=人工智能"

# 边界测试
curl -i "http://localhost:8000/api/v1/articles/search?q="          # 422
curl -i "http://localhost:8000/api/v1/articles/search?q=AI&limit=0" # 422

# CI 等价
pytest -q tests/test_article_search.py
pytest -q tests/test_api_endpoints.py -k search
pytest -q  # 全量
```

---

## 10. Phase 2 闭环达成

✅ **02-03 收尾完成后，Phase 2（用户系统 + 订阅管理）三个 plan items 全部交付**：

| Plan | 需求 | 状态 | 收尾索引 |
|---|---|---|---|
| 02-01 | USER-01/02/03/09 | ✅ Done | [`02-01-PHASE_SUMMARY.md`](./02-01-PHASE_SUMMARY.md) |
| 02-02 | USER-04/05/06 | ✅ Done | [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) |
| 02-03 | USER-07 | ✅ Done | [`02-03-PHASE_SUMMARY.md`](./02-03-PHASE_SUMMARY.md)（本文） |

剩余项：USER-08（个人偏好设置）后端能力在 02-01 已交付（`PUT /users/me/settings`），UI 落地在 Phase 3。

---

> 本文为 **02-03 plan item 的最终聚合页**，建议在所有 02-03 相关 PR/任务的描述中引用本文，作为前后端、CI 与文档链路的单一索引入口。
