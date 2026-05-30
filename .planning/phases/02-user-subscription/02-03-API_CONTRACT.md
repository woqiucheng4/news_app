# 02-03 API Contract — 内容搜索

> **Index:** 本文是 02-03 接口的 Single Source of Truth。完整产物索引见 [`02-03-PHASE_SUMMARY.md`](./02-03-PHASE_SUMMARY.md)；验证证据见 [`02-03-VALIDATION.md`](./02-03-VALIDATION.md)。

## Base

- Base URL: `/api/v1`
- Content-Type: `application/json`

## Authentication

| 端点 | 鉴权要求 |
|---|---|
| `GET /articles/search` | **No**（公开端点，与 `/articles/trending`、`/articles/{id}` 一致） |

> ⚠️ **设计决策**：当前 search 端点**无需鉴权**，与 `/feed`（需鉴权，个性化）的设计区分。理由：
> - 搜索结果**不依赖用户上下文**（无 `is_subscribed` 字段、无个性化排序）
> - 与公开的 `/trending` 一致，让爬虫/外部聚合工具可访问（产品策略后续可调整）
> - 客户端如需"限制未登录用户搜索"，可在 UI 层加 gate
>
> 如需改为鉴权访问，仅需在 `backend/api/v1/articles.py::search_articles` 添加 `user_id: str = Depends(get_current_user_id)`。

## Endpoint

### 1) 搜索文章

- **GET** `/articles/search`
- **Auth**: No
- **Query**

| 字段 | 类型 | 必填 | 默认 | 约束 | 含义 |
|---|---|---|---|---|---|
| `q` | string | Yes | — | length 1-200 | 搜索关键词（同时匹配 title / content / summary） |
| `limit` | int | No | 20 | 1-100 | 返回结果数上限（无分页） |

- **Response 200**

```json
[
  {
    "id": "uuid",
    "title": "OpenAI releases new model GPT-4o-mini",
    "url": "https://openai.com/blog/...",
    "excerpt": "Short excerpt extracted from content...",
    "summary": "GPT-4o-mini is a cost-efficient small model...",
    "author": "OpenAI Team",
    "source": {
      "id": "uuid",
      "name": "OpenAI Blog",
      "url": "https://openai.com/blog",
      "category": "tech"
    },
    "category": "tech",
    "tags": ["ai", "llm"],
    "published_at": "2026-05-28T10:00:00",
    "created_at": "2026-05-28T10:05:00",
    "view_count": 100,
    "bookmark_count": 5
  }
]
```

- **Response 422**（请求校验失败）

```json
{
  "detail": [
    {
      "loc": ["query", "q"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

## Search Semantics

### 匹配范围

后端 SQL（`ArticleRepository.search`）：

```sql
SELECT *
FROM articles
WHERE is_deleted = false
  AND (
    title   ILIKE '%' || :q || '%' OR
    content ILIKE '%' || :q || '%' OR
    summary ILIKE '%' || :q || '%'
  )
ORDER BY published_at DESC
LIMIT :limit;
```

| 字段 | 是否参与匹配 | 备注 |
|---|---|---|
| `title` | ✅ | 文章标题 |
| `content` | ✅ | 摘要片段（不缓存全文，符合版权约束） |
| `summary` | ✅ | AI 摘要（GPT-4o-mini 生成的 2-3 句话） |
| `excerpt` | ❌ | 不参与匹配（与 `content` 重叠，避免双计） |
| `tags` | ❌ | 当前未参与匹配（Open Hardening） |
| `category` | ❌ | 未支持按分类筛选（Open Hardening） |

### 匹配特性

| 维度 | 当前行为 |
|---|---|
| 大小写 | **不敏感**（PostgreSQL `ILIKE`） |
| 中英文 | 都支持，但中文未做分词（直接子串匹配） |
| 通配符 | 不支持用户传入 `%` / `_`（被 SQL 参数转义保护） |
| 多关键词 | **AND 不支持**（视为单一字符串子串匹配，"AI Apple" 只匹配出现 "AI Apple" 连续子串的文章） |
| 短语精确匹配 | 不支持引号 |
| 排序 | 按 `published_at` 倒序，**不按相关度** |
| 分页 | **无分页**，仅 `limit` 截断（建议客户端限制 `limit ≤ 50` 以保证性能） |

### 不参与搜索的内容

- `is_deleted = true` 的文章
- 当前未引入"用户屏蔽源/分类"过滤（Open Hardening）

## Error Contract

| Status | 触发场景 | Body |
|---|---|---|
| 200 | 正常搜索（含 0 结果，返回 `[]`） | `[ ... ]` |
| 422 | `q` 为空字符串 / 超过 200 字符 / `limit` 越界 | Pydantic 标准错误结构 |
| 500 | 数据库异常 | `{ "detail": "..." }` |

## Cross-Reference with 02-02

> 注意区分两个 search 端点：

| 端点 | Plan | 用途 | Auth |
|---|---|---|---|
| `GET /articles/search?q=...` | **02-03** | 按关键词搜索文章 | No |
| `GET /subscriptions/topics?q=...` | **02-02** | 按关键词搜索话题 | Yes |

前者搜内容，后者搜订阅话题，配合使用：用户先用 `/subscriptions/topics?q=` 找话题订阅，再用 `/articles/search?q=` 在历史聚合内容里找具体文章。

## Frontend Suggested Flow

### 标准搜索

1. 用户在搜索栏输入 `q`
2. 客户端做 **防抖**（300-500ms 推荐）后调 `GET /articles/search?q=<keyword>&limit=20`
3. 渲染结果列表（标题 + 来源 + 时间 + 摘要）
4. 点击单条进入 `GET /articles/{id}` 详情页

### 与 02-02 话题搜索结合

1. 搜索栏可分两 Tab：「话题」「文章」
2. 「话题」Tab 调 `/subscriptions/topics?q=`（已订阅态可见）
3. 「文章」Tab 调 `/articles/search?q=`
4. 两边并行调用，实现"全局搜索"体验

### 空态处理

- `q.length === 0` → 客户端拦截不发请求（避免 422）
- 后端返回 `[]` → UI 展示"无相关文章"
- 用户清空输入 → 取消未完成的请求（推荐 `CancelToken`）

## Suggested Performance Budget

| 项 | 目标 | 备注 |
|---|---|---|
| P95 响应时间 | < 500ms（10 万文章规模） | 当前 `ILIKE` 无索引，超过此规模需引入全文索引 |
| 客户端防抖 | 300-500ms | 避免每次按键都发请求 |
| 客户端 limit | 20-50 | 列表初屏够用，不浪费带宽 |

## Cross-Reference

- 关联实现：`backend/api/v1/articles.py::search_articles`、`backend/services/article.py::search_articles`、`backend/repositories/sqlalchemy/article.py::ArticleRepository.search`
- 共享 ArticleResponse schema：[`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md) §11 Personalized Feed
- Flutter 接入：[`02-03-FLUTTER_SEARCH_SCAFFOLD.md`](./02-03-FLUTTER_SEARCH_SCAFFOLD.md)
