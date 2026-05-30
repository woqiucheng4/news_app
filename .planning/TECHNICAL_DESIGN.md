# NewsFlow 技术设计文档

**版本：** v1.0
**日期：** 2026-05-27
**状态：** Draft

---

## 1. 系统架构

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层                                  │
│  Flutter App (iOS / Android / Web)                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼──────────────────────────────────┐
│                      接入层 (Nginx)                              │
│  负载均衡 · SSL 终止 · 限流 · 静态资源                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     应用层 (FastAPI)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Articles │ │  Users   │ │   Subs   │ │  Notifs  │  API v1  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       └────────────┼───────────┼──────────────┘                │
│              ┌─────▼───────────▼─────┐                         │
│              │    Service Layer      │  业务逻辑                 │
│              └─────┬───────────┬─────┘                         │
│              ┌─────▼───────────▼─────┐                         │
│              │  Repository Layer     │  数据访问                 │
│              └───────────────────────┘                         │
└──────────────────────┬──────────────────────────────────────────┘
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │PostgreSQL│ │  Redis   │ │ AI APIs  │
    │ (主+从)  │ │ (缓存)   │ │(OpenAI/  │
    │          │ │          │ │Anthropic)│
    └──────────┘ └──────────┘ └──────────┘
```

### 1.2 分层架构

| 层 | 职责 | 关键类 |
|---|---|---|
| **API 层** | 请求路由、参数校验、响应序列化 | `api/v1/*.py` |
| **Service 层** | 业务逻辑、缓存策略、跨域协调 | `services/*.py` |
| **Repository 层** | 数据访问、查询构建、ORM 映射 | `repositories/sqlalchemy/*.py` |
| **Core 层** | 基础设施（DB、Cache、AI、Tasks、Storage） | `core/*.py` |

### 1.3 核心设计模式

| 模式 | 应用场景 | 实现方式 |
|---|---|---|
| **Repository** | 数据访问抽象 | `IRepository` 接口 + SQLAlchemy 实现 |
| **Strategy** | 可替换后端 | 抽象基类 + 具体实现（Cache/Storage/AI/Tasks） |
| **Cache-Aside** | 读取缓存 | Service 层先查缓存，miss 后查 DB 并回填 |
| **Dependency Injection** | 服务解耦 | FastAPI `Depends()` + `ServiceContainer` |
| **Unit of Work** | 事务管理 | SQLAlchemy `AsyncSession` context manager |

### 1.4 可扩展性设计

所有基础设施组件均通过抽象接口解耦，支持运行时切换：

```
CacheBackend          → LocalCache / RedisCache / MultiLevelCache
StorageBackend        → LocalStorage / S3Storage
AIServiceBackend      → OpenAIBackend / AnthropicBackend
TaskQueue             → SimpleTaskQueue / CeleryTaskQueue
```

切换方式：仅修改环境变量，无需改动业务代码。

---

## 2. 数据库设计

### 2.1 ER 图

```
User ──1:N── Subscription ──N:1── Topic
  │                                     │
  ├──1:N── Bookmark ──N:1── Article ──N:1── Source
  │                        │
  │                        └──N:1── Event ──1:N── Article
  │
  ├──1:1── UserSettings
  │
  ├──1:N── Notification ──N:0..1── Article / Event
  │
  ├──1:N── PushToken
  │
  └──1:N── UserFeed
```

### 2.2 核心表结构

#### Article（文章）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `title` | VARCHAR(500) | 标题 |
| `url` | TEXT | 原文链接 |
| `url_hash` | VARCHAR(64) UNIQUE | URL SHA-256 哈希，用于去重 |
| `content` | TEXT | 原文内容（可为空，仅摘要场景） |
| `excerpt` | VARCHAR(1000) | 原文摘录 |
| `source_id` | UUID FK → Source | 来源 |
| `author` | VARCHAR(200) | 作者 |
| `published_at` | DATETIME | 发布时间 |
| `category` | VARCHAR(100) | 分类 |
| `tags` | TEXT[] | 标签数组 |
| `title_hash` | VARCHAR(64) | 标题 MinHash，用于相似度去重 |
| `content_hash` | VARCHAR(64) | 内容 SimHash，用于语义去重 |
| `simhash` | BIGINT | 64 位 SimHash 值 |
| `summary` | TEXT | AI 生成摘要 |
| `summary_model` | VARCHAR(50) | 生成摘要的模型 |
| `summary_generated_at` | DATETIME | 摘要生成时间 |
| `relevance_score` | DECIMAL(3,1) | AI 推送价值评分 (1-10)，低于阈值不触发推送 |
| `event_id` | UUID FK → Event | 事件聚类 |
| `view_count` | INTEGER | 浏览次数 |
| `bookmark_count` | INTEGER | 收藏次数 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | BOOLEAN | 软删除标记 |

**索引：**
- `ix_article_url_hash` — UNIQUE，去重查询
- `ix_article_source_published` — (source_id, published_at)，信息流查询
- `ix_article_category_published` — (category, published_at)，分类浏览
- `ix_article_event_id` — 事件聚类查询
- `ix_article_title_hash` — 相似度去重

#### Source（信息源）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `name` | VARCHAR(200) | 来源名称 |
| `url` | TEXT | 来源 URL |
| `source_type` | VARCHAR(20) | rss / web / api |
| `feed_url` | TEXT | RSS Feed 地址 |
| `is_active` | BOOLEAN | 是否启用 |
| `last_fetched_at` | DATETIME | 上次抓取时间 |
| `error_count` | INTEGER | 连续错误次数 |
| `category` | VARCHAR(100) | 分类 |
| `language` | VARCHAR(10) | 语言 |
| `fetch_interval_minutes` | INTEGER | 抓取间隔（分钟），默认 30，动态调整 |
| `heat_score` | DECIMAL(10,2) | 热度分数，用于自适应抓取频率 |
| `last_article_count` | INTEGER | 近 24h 新文章数，用于热度计算 |

#### Event（事件聚类）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `title` | VARCHAR(500) | 事件标题 |
| `summary` | TEXT | 事件摘要 |
| `category` | VARCHAR(100) | 分类 |
| `representative_article_id` | UUID FK | 代表文章 |
| `representative_hash` | VARCHAR(64) | 代表文章内容哈希 |
| `article_count` | INTEGER | 关联文章数 |
| `source_count` | INTEGER | 不同来源数 |

#### User（用户）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `email` | VARCHAR(255) UNIQUE | 邮箱 |
| `username` | VARCHAR(100) UNIQUE | 用户名 |
| `display_name` | VARCHAR(200) | 显示名 |
| `avatar_url` | TEXT | 头像 URL |
| `hashed_password` | VARCHAR(255) | 密码哈希 |
| `supabase_uid` | VARCHAR(255) | Supabase Auth UID |
| `google_id` | VARCHAR(255) | Google OAuth ID |
| `apple_id` | VARCHAR(255) | Apple OAuth ID |
| `is_active` | BOOLEAN | 是否激活 |
| `is_verified` | BOOLEAN | 是否验证邮箱 |
| `is_premium` | BOOLEAN | 是否付费用户 |
| `premium_expires_at` | DATETIME | 付费到期时间 |

#### Topic（话题）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `name` | VARCHAR(200) UNIQUE | 话题名称 |
| `slug` | VARCHAR(200) UNIQUE | URL 友好标识 |
| `description` | TEXT | 描述 |
| `category` | VARCHAR(100) | 分类 |
| `subscriber_count` | INTEGER | 订阅数 |
| `article_count` | INTEGER | 文章数 |

#### Subscription（订阅）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `user_id` | UUID FK → User | 用户 |
| `topic_id` | UUID FK → Topic | 话题 |
| `is_active` | BOOLEAN | 是否激活 |
| `priority` | INTEGER | 优先级 (0-5) |
| `push_enabled` | BOOLEAN | 是否推送 |

**约束：** UNIQUE(user_id, topic_id)

### 2.3 成本追踪表

#### APIUsageLog（AI 使用日志）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `model` | VARCHAR(50) | 模型名称 |
| `request_type` | VARCHAR(50) | 请求类型（summary/analysis） |
| `input_tokens` | INTEGER | 输入 token 数 |
| `output_tokens` | INTEGER | 输出 token 数 |
| `cost_usd` | DECIMAL(10,6) | 本次费用 (USD) |
| `cached` | BOOLEAN | 是否命中缓存 |
| `article_id` | UUID FK | 关联文章 |
| `error` | TEXT | 错误信息 |

#### DailyCostSummary（每日成本汇总）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID PK | 主键 |
| `date` | DATE UNIQUE | 日期 |
| `total_requests` | INTEGER | 总请求数 |
| `total_tokens` | INTEGER | 总 token 数 |
| `total_cost_usd` | DECIMAL(10,2) | 总费用 |
| `by_model` | JSONB | 按模型分拆 |
| `by_type` | JSONB | 按类型分拆 |
| `cache_hit_rate` | DECIMAL(5,4) | 缓存命中率 |

### 2.4 迁移策略

使用 Alembic 管理 schema 版本：

```
alembic/
├── env.py                    # 异步迁移环境
├── script.py.mako            # 迁移模板
└── versions/
    └── 001_initial_schema.py # 初始 schema
```

- 所有表结构变更通过 `alembic revision --autogenerate` 生成
- 生产环境部署前必须执行 `alembic upgrade head`
- 支持回滚 `alembic downgrade -1`

---

## 3. API 设计

### 3.1 API 规范

| 项目 | 规范 |
|---|---|
| 协议 | HTTPS |
| 风格 | RESTful |
| 版本 | URL 路径版本 `/api/v1` |
| 格式 | JSON (`Content-Type: application/json`) |
| 认证 | Bearer Token (JWT) |
| 分页 | `page` + `page_size` 参数 |
| 错误 | HTTP 状态码 + JSON 错误体 |

### 3.2 认证流程

```
客户端                         服务端
  │                              │
  │  POST /auth/login            │
  │  {email, password}           │
  │ ─────────────────────────►   │
  │                              │  验证凭据
  │  {access_token, refresh_token}│
  │ ◄─────────────────────────   │
  │                              │
  │  GET /api/v1/users/me        │
  │  Authorization: Bearer <token>│
  │ ─────────────────────────►   │
  │                              │  验证 JWT
  │  {user data}                 │
  │ ◄─────────────────────────   │
  │                              │
  │  POST /auth/refresh          │
  │  {refresh_token}             │
  │ ─────────────────────────►   │
  │                              │  验证 refresh token
  │  {new access_token}          │
  │ ◄─────────────────────────   │
```

**JWT Payload：**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "is_premium": false,
  "exp": 1716844800,
  "iat": 1716842400
}
```

### 3.3 端点详细规格

#### Articles `/api/v1/articles`

**GET /feed** — 信息流

```
Query: page=1, page_size=20, category=optional
Auth: Required

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "title": "Apple 发布新 iPhone 17",
      "source": {"name": "TechCrunch", "icon_url": "..."},
      "published_at": "2026-05-27T10:00:00Z",
      "summary": "Apple 今日发布了新一代 iPhone 17...",
      "category": "tech",
      "event_id": "uuid-or-null"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

**GET /search** — 全文搜索

```
Query: q="keyword", limit=20
Auth: Required
Rate Limit: 30/min

Response 200:
{
  "items": [...],
  "total": 42,
  "query": "keyword"
}
```

**GET /trending** — 热门文章

```
Query: limit=10
Auth: Required
Rate Limit: 50/min

Response 200:
{
  "items": [...]
}
```

**GET /{article_id}** — 文章详情

```
Auth: Required

Response 200:
{
  "id": "uuid",
  "title": "...",
  "url": "https://...",
  "source": {...},
  "published_at": "...",
  "summary": "AI 摘要...",
  "content_excerpt": "原文摘录...",
  "tags": ["ai", "apple"],
  "event": {
    "id": "uuid",
    "title": "...",
    "article_count": 5
  },
  "is_bookmarked": false,
  "view_count": 1234
}
```

**POST /{article_id}/summary** — 触发摘要生成

```
Auth: Required

Response 200:
{
  "summary": "生成的摘要...",
  "model": "gpt-4o-mini",
  "cached": false,
  "cost_usd": 0.0003
}
```

#### Users `/api/v1/users`

**GET /me** — 当前用户

```
Auth: Required

Response 200:
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "John",
  "avatar_url": "...",
  "is_premium": false,
  "subscription_count": 5,
  "created_at": "..."
}
```

**PUT /me/settings** — 更新设置

```
Auth: Required
Body:
{
  "push_enabled": true,
  "language": "en",
  "theme": "dark",
  "summary_length": "medium"
}

Response 200: {updated settings object}
```

**GET /me/export** — GDPR 数据导出

```
Auth: Required

Response 200: (application/json)
{
  "user": {...},
  "subscriptions": [...],
  "bookmarks": [...],
  "notifications": [...],
  "exported_at": "..."
}
```

**DELETE /me** — GDPR 账号删除

```
Auth: Required

Response 200:
{
  "message": "Account scheduled for deletion",
  "deletion_date": "2026-06-03T..."
}
```

#### Subscriptions `/api/v1/subscriptions`

**GET /topics** — 话题列表

```
Query: category=optional, q=optional, sort=popular|newest, limit=20
Auth: Required

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "name": "Artificial Intelligence",
      "slug": "ai",
      "category": "tech",
      "subscriber_count": 1520,
      "is_subscribed": true
    }
  ]
}
```

**POST /subscribe** — 订阅话题

```
Auth: Required
Body: {"topic_id": "uuid"}

Response 200:
{
  "subscription_id": "uuid",
  "topic_name": "AI",
  "subscribed_at": "..."
}
```

**DELETE /unsubscribe/{topic_id}** — 取消订阅

```
Auth: Required

Response 200: {"message": "Unsubscribed successfully"}
```

#### Notifications `/api/v1/notifications`

**GET /** — 通知列表

```
Query: limit=20, is_read=optional
Auth: Required

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "title": "AI 领域重大更新",
      "body": "...",
      "type": "breaking",
      "is_read": false,
      "created_at": "..."
    }
  ]
}
```

**GET /unread-count** — 未读数

```
Response 200: {"count": 3}
```

**PUT /{notification_id}/read** — 标记已读

```
Response 200: {"success": true}
```

**PUT /read-all** — 全部已读

```
Response 200: {"marked_count": 5}
```

**GET /preferences** — 获取通知偏好

```
Auth: Required

Response 200:
{
  "push_enabled": true,
  "push_channel": "fcm",
  "email_notifications": true,
  "telegram_chat_id": null,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "quiet_hours_timezone": "America/New_York"
}
```

**PUT /preferences** — 更新通知偏好

```
Auth: Required
Body:
{
  "push_enabled": true,
  "email_notifications": false,
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00"
}

Response 200: {updated preferences object}
```

**POST /telegram/link** — 绑定 Telegram (P1)

```
Auth: Required
Body: {"chat_id": "123456789"}

Response 200: {"linked": true}
```

### 3.6 通知渠道架构

参考 TrendRadar 的多渠道通知设计，NewsFlow 支持多通知渠道，用户可按偏好配置。

**渠道优先级：**

| 优先级 | 渠道 | 实现方式 | MVP |
|---|---|---|---|
| P0 | FCM Push | Firebase Cloud Messaging | ✅ |
| P0 | Email | SMTP (FastAPI-Mail) | ✅ |
| P1 | Telegram | Telegram Bot API | ❌ |
| P2 | Webhook | 用户自定义 URL | ❌ |

**渠道抽象接口：**

```python
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    """通知渠道抽象基类"""

    @abstractmethod
    async def send(
        self,
        recipient: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> bool:
        """发送通知，返回是否成功"""
        ...

    @abstractmethod
    def get_channel_type(self) -> str:
        """返回渠道类型标识"""
        ...


class FCMChannel(NotificationChannel):
    """Firebase Cloud Messaging 渠道"""

    async def send(self, recipient: str, title: str, body: str, data: dict | None = None) -> bool:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=recipient,
        )
        try:
            messaging.send(message)
            return True
        except Exception:
            return False

    def get_channel_type(self) -> str:
        return "fcm"


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""

    async def send(self, recipient: str, title: str, body: str, data: dict | None = None) -> bool:
        # 使用 FastAPI-Mail 发送
        ...

    def get_channel_type(self) -> str:
        return "email"


class TelegramChannel(NotificationChannel):
    """Telegram Bot 渠道 (P1)"""

    async def send(self, recipient: str, title: str, body: str, data: dict | None = None) -> bool:
        # Telegram Bot API 发送
        ...

    def get_channel_type(self) -> str:
        return "telegram"
```

**通知调度器：**

```python
class NotificationDispatcher:
    """通知调度器 — 根据用户偏好选择渠道发送"""

    def __init__(self):
        self.channels: dict[str, NotificationChannel] = {}

    def register(self, channel: NotificationChannel):
        self.channels[channel.get_channel_type()] = channel

    async def dispatch(
        self,
        user: User,
        title: str,
        body: str,
        data: dict | None = None,
    ):
        """根据用户设置的渠道偏好发送通知"""
        preferences = await self.get_user_preferences(user.id)

        for channel_type, is_enabled in preferences.items():
            if not is_enabled or channel_type not in self.channels:
                continue

            recipient = self.get_recipient(user, channel_type)
            if recipient:
                await self.channels[channel_type].send(
                    recipient=recipient,
                    title=title,
                    body=body,
                    data=data,
                )
```

**用户通知偏好数据模型（UserSettings 扩展）：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `push_enabled` | BOOLEAN | FCM 推送开关 |
| `push_channel` | VARCHAR(20) | 推送渠道: fcm / telegram |
| `email_notifications` | BOOLEAN | 邮件通知开关 |
| `telegram_chat_id` | VARCHAR(100) | Telegram Chat ID |
| `webhook_url` | TEXT | 自定义 Webhook URL (P2) |
| `quiet_hours_start` | TIME | 免打扰开始时间 |
| `quiet_hours_end` | TIME | 免打扰结束时间 |
| `quiet_hours_timezone` | VARCHAR(50) | 时区 (如 "America/New_York") |

**推送价值过滤逻辑：**

```python
async def should_push(article: Article, user: User) -> bool:
    """判断是否应该向用户推送该文章"""
    # 1. 检查用户是否订阅了相关话题
    if not await is_user_subscribed(user.id, article.topics):
        return False

    # 2. 检查推送价值评分
    if article.relevance_score and article.relevance_score < 6.0:
        return False  # 低于 6 分不推送

    # 3. 检查免打扰时段
    if is_quiet_hours(user.settings):
        return False

    # 4. 检查推送频率（避免轰炸）
    recent_push_count = await count_recent_pushes(user.id, hours=1)
    if recent_push_count >= 5:
        return False  # 每小时最多 5 条推送

    return True
```

#### Dashboard `/api/v1/dashboard`

**GET /cost/summary** — 成本概览

```
Response 200:
{
  "date": "2026-05-27",
  "total_requests": 850,
  "total_tokens": 125000,
  "total_cost_usd": 3.42,
  "budget_remaining_usd": 1.58,
  "cache_hit_rate": 0.65,
  "by_model": {
    "gpt-4o-mini": {"requests": 800, "cost_usd": 3.10},
    "claude-haiku": {"requests": 50, "cost_usd": 0.32}
  }
}
```

**GET /health** — 系统健康

```
Response 200:
{
  "status": "healthy",
  "database": {"status": "ok", "write": true, "reads": 2},
  "redis": {"status": "ok"},
  "ai": {"status": "ok", "openai": true, "anthropic": true},
  "tasks": {"status": "ok", "pending": 5}
}
```

### 3.4 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

| HTTP 状态码 | 场景 |
|---|---|
| 400 | 请求参数校验失败 |
| 401 | 未认证 / Token 过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 冲突（如重复订阅） |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

### 3.5 限流策略

基于 Redis 滑动窗口，按端点配置：

| 端点 | 限制 |
|---|---|
| `POST /summary` | 10/min |
| `GET /search` | 30/min |
| `GET /trending` | 50/min |
| 默认 | 100/min |

响应头：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
```

---

## 4. AI 摘要系统

### 4.1 摘要生成流程

```
新文章入库
    │
    ▼
检查缓存 (url_hash → summary)
    │
    ├─ 命中 → 直接返回
    │
    └─ 未命中
         │
         ▼
    检查预算 (CostTracker)
         │
         ├─ 超预算 → 降级模型 / 返回空
         │
         └─ 正常
              │
              ▼
         调用 AI API
              │
              ▼
         记录成本 (APIUsageLog)
              │
              ▼
         缓存结果 (7天 TTL)
              │
              ▼
         更新 Article.summary
```

### 4.2 Prompt 设计

**System Prompt（摘要生成 + 推送评分）：**

```
你是一位专业的新闻摘要编辑。

要求：
1. 长度：2-3 句话，总计 50-100 字
2. 内容：仅包含核心事实，不添加评论或推测
3. 语言：与原文语言一致
4. 推送价值评分：1-10 分，评估该新闻对订阅用户的推送价值
   - 9-10: 重大突发新闻（产品发布、重大政策变化、市场剧变）
   - 7-8: 重要更新（行业动态、公司财报、技术突破）
   - 5-6: 一般新闻（常规报道、小型更新）
   - 1-4: 低价值（花边新闻、旧闻重发、广告软文）

输出格式（JSON）：
{
  "summary": "摘要内容",
  "relevance_score": 8.5
}

禁止：
- 不要复制原文句子
- 不要添加引导词（"根据报道"、"据悉"）
- 不要猜测未明确说明的信息
```

**User Prompt 模板：**

```
标题：{title}
来源：{source}
内容：{content}
```

### 4.3 成本控制

**模型定价：**

| 模型 | 输入 ($/MTok) | 输出 ($/MTok) | 单篇摘要成本 |
|---|---|---|---|
| GPT-4o-mini | $0.15 | $0.60 | ~$0.0003 |
| Claude Haiku 4.5 | $1.00 | $5.00 | ~$0.002 |

**预算控制策略：**

```python
class CostTracker:
    daily_budget = 5.0    # $5/天
    monthly_budget = 100.0  # $100/月

    def check_budget(estimated_cost) -> bool:
        if daily_cost + estimated_cost > daily_budget:
            return False  # 触发降级
        return True
```

**降级策略：**

| 预算使用率 | 动作 |
|---|---|
| < 80% | 正常使用 GPT-4o-mini |
| 80-95% | 降低生成频率，仅处理高优先级 |
| 95-100% | 停止新摘要生成，仅返回缓存 |
| > 100% | 降级到更便宜的模型或暂停 |

### 4.4 去重系统

**三层去重架构：**

```
新文章
    │
    ▼
第 1 层：URL 去重
    url_hash = SHA256(normalize_url(url))
    查询 Article.url_hash 是否存在
    │
    ├─ 命中 → 丢弃
    │
    └─ 未命中 ↓
    │
    ▼
第 2 层：标题相似度 (MinHash)
    title_shingles = generate_shingles(title, k=3)
    title_hash = minhash(title_shingles)
    查询相似度 > 70% 的文章
    │
    ├─ 命中 → 标记为重复，关联到已有 Event
    │
    └─ 未命中 ↓
    │
    ▼
第 3 层：内容指纹 (SimHash)
    content_hash = simhash(content)
    计算 Hamming 距离
    │
    ├─ 距离 ≤ 3 (相似度 > 85%) → 标记为重复
    │
    └─ 未命中 → 新文章，可能创建新 Event
```

**SimHash 实现要点：**

```python
def simhash(text: str, hashbits: int = 64) -> int:
    # 1. 分词 (jieba / nltk)
    # 2. 生成 shingles (k=3)
    # 3. 每个 shingle 做 hash
    # 4. 加权叠加
    # 5. 二值化得到最终指纹
```

**Event 聚类规则：**
- 新文章与已有 Event 的 `representative_hash` 比较
- Hamming 距离 ≤ 3 → 归入该 Event
- 否则 → 创建新 Event，该文章为代表文章

---

## 5. 内容采集系统

### 5.1 采集流程

```
APScheduler (每 15-60 分钟)
    │
    ▼
获取活跃 Source 列表
    │
    ▼
并发抓取 (asyncio.Semaphore 控制并发)
    │
    ├─ RSS 源 → feedparser 解析
    │
    └─ 网页 URL → httpx + selectolax 提取
    │
    ▼
数据清洗 (标题规范化、时间解析、语言检测)
    │
    ▼
三层去重
    │
    ▼
入库 (Article + Source 关联)
    │
    ▼
触发 AI 摘要生成 (后台任务)
    │
    ▼
推送通知 (如有新文章匹配用户订阅)
```

### 5.2 RSS 解析

```python
import feedparser

async def fetch_feed(source: Source) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(source.feed_url, timeout=30)
        feed = feedparser.parse(response.text)

    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "content": entry.get("summary", ""),
            "published_at": parse_date(entry.get("published")),
            "author": entry.get("author", ""),
        })
    return articles
```

### 5.3 网页内容提取

```python
from selectolax.parser import HTMLParser

async def extract_content(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        tree = HTMLParser(response.text)

    # 提取标题
    title = tree.css_first("h1").text() if tree.css_first("h1") else ""

    # 提取正文 (启发式：最长的 <p> 集合)
    paragraphs = [p.text() for p in tree.css("p")]
    content = "\n".join(paragraphs)

    return {"title": title, "content": content}
```

### 5.4 自适应抓取频率

参考 NewsNow 的自适应策略，根据源的热度动态调整抓取间隔：

**热度计算公式：**
```
heat_score = (近24h新文章数 × 0.6) + (订阅该源的用户数 × 0.4)
```

**抓取频率映射：**

| 热度分数 | 抓取间隔 | 示例 |
|---|---|---|
| ≥ 50 | 5 分钟 | 热门科技媒体（TechCrunch、The Verge） |
| 20-49 | 15 分钟 | 主流新闻源 |
| 5-19 | 30 分钟 | 中等活跃源 |
| 1-4 | 2 小时 | 低频更新源 |
| 0 | 6 小时 | 休眠源 |

**实现方式：**
```python
class AdaptiveFetchScheduler:
    """自适应抓取调度器"""

    def calculate_interval(self, source: Source) -> int:
        """根据热度计算抓取间隔（分钟）"""
        heat = source.heat_score
        if heat >= 50:
            return 5
        elif heat >= 20:
            return 15
        elif heat >= 5:
            return 30
        elif heat >= 1:
            return 120
        else:
            return 360

    async def update_heat_scores(self):
        """定时更新所有源的热度分数（每小时执行一次）"""
        sources = await self.source_repo.get_active_sources()
        for source in sources:
            recent_count = await self.article_repo.count_recent(
                source_id=source.id,
                hours=24
            )
            subscriber_count = await self.sub_repo.count_source_subscribers(
                source_id=source.id
            )
            source.heat_score = (recent_count * 0.6) + (subscriber_count * 0.4)
            source.fetch_interval_minutes = self.calculate_interval(source)
            await self.source_repo.update(source)
```

### 5.5 源健康监控

| 指标 | 阈值 | 动作 |
|---|---|---|
| 连续失败次数 | ≥ 5 | 标记 `is_active = False` |
| 最后抓取时间 | > 2 小时 | 告警 |
| 响应时间 | > 30 秒 | 超时重试 |
| 内容变化率 | < 5% | 可能是静态页，降级频率 |

---

## 6. 缓存架构

### 6.1 多级缓存

```
请求 → L1 (本地 LRU) → L2 (Redis) → DB
                │              │
                └──────────────┘
                 L2 命中时回填 L1
```

| 层级 | 介质 | TTL | 容量 | 访问延迟 |
|---|---|---|---|---|
| L1 | 进程内存 (LRU) | 60s | 1000 条 | ~1μs |
| L2 | Redis | 3600s | 无限制 | ~1ms |

### 6.2 缓存键规范

| 数据 | 缓存键 | TTL |
|---|---|---|
| 文章详情 | `article:{id}` | 1 小时 |
| 信息流 | `feed:{user_id}:page:{n}` | 5 分钟 |
| 热门文章 | `trending:{limit}` | 10 分钟 |
| 用户信息 | `user:{id}` | 5 分钟 |
| AI 摘要 | `summary:{url_hash}` | 7 天 |
| 话题列表 | `topics:{category}` | 30 分钟 |

### 6.3 缓存失效策略

- **写穿 (Write-Through)：** 数据更新时同时更新缓存和 DB
- **主动失效：** 数据变更时调用 `cache.delete(key)`
- **模式失效：** 用户数据变更时 `invalidate_pattern("user:{id}:*")`
- **TTL 自动过期：** 所有缓存项都有 TTL

---

## 7. 部署架构

### 7.1 开发环境

```bash
# Docker Compose 一键启动
docker-compose up -d

# 服务端口
# API:       http://localhost:8000
# Swagger:   http://localhost:8000/docs
# PostgreSQL: localhost:5432
# Redis:     localhost:6379
```

### 7.2 生产部署 (Fly.io)

```yaml
# fly.toml
app = "newflow-api"

[build]
  dockerfile = "Dockerfile"

[env]
  ENVIRONMENT = "production"
  WORKERS = "4"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 2048
```

**外部依赖：**
- Supabase (PostgreSQL + Auth)
- Upstash (Redis)
- OpenAI API
- Firebase (FCM)

### 7.3 资源规格

| 组件 | MVP (0-100 用户) | 增长期 (100-1K) | 规模期 (1K-10K) |
|---|---|---|---|
| API 实例 | 1 × 1C/1G | 2 × 2C/2G | 4 × 2C/2G |
| PostgreSQL | Supabase Free | Supabase Pro ($25) | 自托管 2C/4G |
| Redis | Upstash Free | Upstash Pro | 自托管 1C/1G |
| Workers | 2 | 4 | 8 |
| DB Pool | 10 | 20 | 50 |

### 7.4 CI/CD 流程

```
Push to main
    │
    ▼
GitHub Actions
    │
    ├─ Lint (ruff)
    ├─ Type Check (mypy)
    ├─ Tests (pytest)
    ├─ Build Docker Image
    │
    ▼
Deploy to Fly.io
    │
    ├─ Run Alembic migrations
    ├─ Health check
    │
    ▼
Post-deploy verification
```

---

## 8. 安全设计

### 8.1 认证与授权

| 机制 | 实现 |
|---|---|
| 密码存储 | bcrypt 哈希 |
| Token 签发 | JWT (HS256) |
| Token 有效期 | Access: 30min, Refresh: 7天 |
| OAuth | Google + Apple via Supabase Auth |

### 8.2 数据安全

| 措施 | 说明 |
|---|---|
| 传输加密 | HTTPS (TLS 1.3) |
| 存储加密 | PostgreSQL TDE (Supabase 提供) |
| 敏感字段 | `hashed_password` 不可读，API 响应不包含 |
| SQL 注入 | SQLAlchemy 参数化查询 |
| XSS | 前端输出转义 |
| CSRF | SameSite Cookie + CORS |

### 8.3 GDPR 合规

| 要求 | 实现 |
|---|---|
| 数据最小化 | 仅收集必要字段 |
| 用户知情 | 隐私政策页面 |
| 数据导出 | `GET /users/me/export` (JSON) |
| 数据删除 | `DELETE /users/me` (软删除 + 30天后硬删除) |
| 数据处理协议 | Supabase DPA 签署 |

### 8.4 API 安全

| 措施 | 实现 |
|---|---|
| 限流 | Redis 滑动窗口 (100/min 默认) |
| 认证 | JWT Bearer Token |
| CORS | 配置允许的 origins |
| 输入校验 | Pydantic 模型校验 |
| 错误处理 | 不暴露内部错误栈 |

---

## 9. 监控与可观测性

### 9.1 健康检查

```json
// GET /health
{
  "status": "healthy",
  "services": {
    "database": {"status": "ok", "write": true, "reads": 2},
    "redis": {"status": "ok"},
    "ai": {"status": "ok", "openai": true, "anthropic": true},
    "tasks": {"status": "ok", "pending": 5}
  }
}
```

### 9.2 关键指标

| 分类 | 指标 | 报警阈值 |
|---|---|---|
| **API** | 响应时间 P95 | > 500ms |
| **API** | 错误率 | > 1% |
| **API** | 请求量 | > 1000/min |
| **AI** | 每日成本 | > $4.50 (90% 预算) |
| **AI** | 生成延迟 | > 10s |
| **DB** | 连接池使用率 | > 80% |
| **DB** | 查询延迟 P95 | > 200ms |
| **Redis** | 内存使用率 | > 80% |
| **采集** | 源失败率 | > 20% |
| **采集** | 队列积压 | > 1000 |

### 9.3 日志规范

使用 `structlog` 结构化日志：

```json
{
  "timestamp": "2026-05-27T10:00:00Z",
  "level": "info",
  "event": "article_created",
  "article_id": "uuid",
  "source_id": "uuid",
  "has_summary": false,
  "dedup_layer": "none",
  "duration_ms": 45
}
```

### 9.4 成本仪表板

`GET /api/v1/dashboard/cost/summary` 提供实时成本数据：
- 当日/当月 AI 调用次数和费用
- 按模型分拆（GPT-4o-mini vs Claude Haiku）
- 缓存命中率
- 预算剩余

---

## 10. 技术栈清单

### 10.1 后端依赖

| 包 | 版本 | 用途 |
|---|---|---|
| fastapi | ≥0.109.0 | Web 框架 |
| uvicorn | ≥0.27.0 | ASGI 服务器 |
| pydantic | ≥2.5.0 | 数据校验 |
| pydantic-settings | ≥2.1.0 | 配置管理 |
| sqlalchemy[asyncio] | ≥2.0.0 | ORM |
| asyncpg | ≥0.29.0 | PostgreSQL 异步驱动 |
| alembic | ≥1.13.0 | 数据库迁移 |
| redis[hiredis] | ≥5.0.0 | 缓存 |
| openai | ≥1.12.0 | GPT API |
| anthropic | ≥0.18.0 | Claude API |
| feedparser | ≥6.0.0 | RSS 解析 |
| selectolax | ≥0.3.0 | HTML 解析 |
| httpx | ≥0.26.0 | HTTP 客户端 |
| firebase-admin | latest | FCM 推送 |
| structlog | ≥24.1.0 | 结构化日志 |
| python-jose | ≥3.3.0 | JWT |
| tenacity | ≥9.0.0 | 重试逻辑 |

### 10.2 前端依赖 (Flutter)

| 包 | 版本 | 用途 |
|---|---|---|
| flutter_riverpod | 3.3.x | 状态管理 |
| go_router | 17.x | 路由 |
| dio | 5.x | HTTP 客户端 |
| freezed | 2.x | 不可变数据类 |
| cached_network_image | 3.x | 图片缓存 |
| flutter_local_notifications | 18.x | 本地通知 |

---

## 11. 未来扩展路径

### 11.1 水平扩展

```
Phase 1 (MVP)
  单进程 + SimpleTaskQueue
      │
      ▼
Phase 2 (增长)
  Gunicorn 多 worker + 读写分离
      │
      ▼
Phase 3 (规模)
  多实例 + Nginx 负载均衡 + Celery
      │
      ▼
Phase 4 (大规模)
  Kubernetes + Redis Sentinel + PG 主从
```

### 11.2 功能扩展点

| 功能 | 扩展方式 |
|---|---|
| 新 AI 模型 | 实现 `AIServiceBackend` 接口 |
| 新存储后端 | 实现 `StorageBackend` 接口 |
| 新任务队列 | 实现 `TaskQueue` 接口 |
| 新信息源 | 在 `Source` 表添加记录 |
| 新通知渠道 | 实现 `NotificationChannel` 接口 |
| MCP Server | 实现 MCP 协议接口 (P2) |

### 11.3 MCP Server 扩展 (P2)

参考 NewsNow 的 MCP Server 支持，为 AI Agent 提供标准化的数据访问接口。

**用途：** 用户在 Claude / Cursor 等 AI 工具中直接查询 NewsFlow 数据。

```
用户: "帮我查一下今天 AI 行业有什么大新闻"
→ Claude 调用 NewsFlow MCP Server
→ 返回该用户订阅的 AI 相关新闻摘要
```

**MCP Tool 定义：**

| Tool 名称 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `search_articles` | `query`, `category`, `limit` | 文章列表 | 全文搜索 |
| `get_feed` | `category`, `limit` | 信息流 | 获取用户信息流 |
| `get_article_detail` | `article_id` | 文章详情 | 含 AI 摘要 |
| `get_trending` | `limit` | 热门文章 | 当前热门 |
| `get_subscriptions` | - | 订阅列表 | 用户订阅的话题 |

**实现方式：** 使用 Python MCP SDK (`mcp` 包)，作为 FastAPI 的独立路由或独立服务运行。

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("newflow")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_articles",
            description="Search news articles by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"},
                    "category": {"type": "string", "description": "Category filter"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search_articles":
        results = await article_service.search(**arguments)
        return [TextContent(type="text", text=json.dumps(results))]
```

**优先级：** P2（MVP 之后），架构设计时预留 `MCPService` 接口。

---

*文档版本：v1.0*
*最后更新：2026-05-27*
