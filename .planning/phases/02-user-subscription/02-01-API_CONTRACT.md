# 02-01 API Contract — 用户认证 + GDPR

> **Index:** 本文是 02-01 接口的 Single Source of Truth。完整产物索引见 [`02-01-PHASE_SUMMARY.md`](./02-01-PHASE_SUMMARY.md)；验证证据见 [`02-01-VALIDATION.md`](./02-01-VALIDATION.md)。

## Base

- Base URL: `/api/v1`
- Content-Type: `application/json`

## Authentication Model

### Token 体系

| Token | 内容 (claims) | 用途 | 过期 |
|---|---|---|---|
| `access_token` | `sub` (user_id), `email`, `is_premium`, `type=access`, `exp` | 调用受保护接口 | 由 settings 控制（默认短期） |
| `refresh_token` | `sub` (user_id), `type=refresh`, `exp` | 换发新 access token | 由 settings 控制（默认长期） |

- **签名算法**：HS256（`SECRET_KEY` 来自后端 `.env`）
- **携带方式**：`Authorization: Bearer <access_token>`
- **测试兜底**：本地/集成测试可使用 `x-user-id: <uuid>` 头部（与 02-02 共享同一鉴权依赖 `get_current_user_id`）

## Endpoints

### Auth

#### 1) 注册（邮箱密码）

- **POST** `/auth/register`
- **Auth**: No
- **Request**

```json
{
  "email": "user@example.com",
  "password": "abcdef",
  "display_name": "Alice"
}
```

- 字段约束：
  - `email`: 合法邮箱（Pydantic `EmailStr`）
  - `password`: 长度 6-128
  - `display_name`: 可选；缺省时取邮箱本地部分

- **Response 200**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Alice",
    "is_premium": false
  }
}
```

- **Response 400**

```json
{ "detail": "Email already registered" }
```

#### 2) 登录（邮箱密码）

- **POST** `/auth/login`
- **Auth**: No
- **Request**

```json
{ "email": "user@example.com", "password": "abcdef" }
```

- **Response 200**：同 `register` 的成功响应
- **Response 401**

```json
{ "detail": "Invalid email or password" }
```

#### 3) OAuth 登录（Google / Apple）

- **POST** `/auth/oauth/{provider}`
- **Auth**: No
- **Path**：`provider` ∈ `{ "google", "apple" }`
- **Request**

```json
{
  "provider_id": "108273...",
  "email": "user@example.com",
  "display_name": "Alice",
  "avatar_url": "https://lh3.googleusercontent.com/..."
}
```

- 服务端行为：
  1. 优先按 `provider_id` 查找用户（`google_id` / `apple_id`）
  2. 否则按 `email` 查找并补绑 `provider_id`
  3. 否则创建新用户
- **Response 200**：同 `register` 成功响应
- **Response 400**

```json
{ "detail": "Unsupported provider" }
```

> ⚠️ 当前合约约束：客户端需自行完成 Google/Apple SDK 流程并把 `provider_id` 传后端。后端不验证 ID Token 签名（待后续硬化，见 [`02-01-VALIDATION.md`](./02-01-VALIDATION.md) 的 Open Hardening）。

#### 4) 刷新 Access Token

- **POST** `/auth/refresh`
- **Auth**: No（携带 refresh_token）
- **Request**

```json
{ "refresh_token": "<jwt>" }
```

- **Response 200**

```json
{ "access_token": "<new-jwt>", "token_type": "bearer" }
```

- **Response 401**

```json
{ "detail": "Invalid refresh token" }
```

> 注意 `/refresh` **不返回新的 refresh_token**；refresh token 在过期前持续可用。

### User Profile + Settings

#### 5) 获取当前用户

- **GET** `/users/me`
- **Auth**: Yes
- **Response 200**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": null,
  "display_name": "Alice",
  "avatar_url": null,
  "is_active": true,
  "is_verified": true,
  "is_premium": false,
  "created_at": "2026-05-28T12:00:00"
}
```

- **Response 404**

```json
{ "detail": "User not found" }
```

#### 6) 更新用户设置

- **PUT** `/users/me/settings`
- **Auth**: Yes
- **Request**（所有字段可选，仅传需要修改的字段）

```json
{
  "push_enabled": true,
  "push_daily_briefing": true,
  "push_breaking_news": true,
  "push_max_per_day": 10,
  "language": "zh-CN",
  "theme": "dark"
}
```

- 字段语义：
  - `push_enabled`：推送总开关
  - `push_daily_briefing`：每日简报推送
  - `push_breaking_news`：突发新闻推送
  - `push_max_per_day`：每日推送上限（防通知疲劳）
  - `language`：UI / 摘要语言偏好（如 `zh-CN`, `en`）
  - `theme`：UI 主题（如 `light`, `dark`, `system`）
- **Response 200**

```json
{ "success": true }
```

### GDPR

#### 7) 导出用户数据

- **GET** `/users/me/export`
- **Auth**: Yes
- **Response 200**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": null,
    "display_name": "Alice",
    "avatar_url": null,
    "is_active": true,
    "is_verified": true,
    "is_premium": false,
    "created_at": "2026-05-28T12:00:00"
  },
  "settings": {
    "push_enabled": true,
    "push_daily_briefing": true,
    "push_breaking_news": true,
    "push_max_per_day": 10,
    "language": "zh-CN",
    "theme": "dark"
  },
  "exported_at": "2026-05-29T02:00:00"
}
```

- **Compliance Notes:**
  - 当前导出范围：用户基本信息 + 设置偏好
  - **不包含**：订阅历史、订阅设置、原始登录日志（如有需要按 GDPR Right to Access 扩展）
  - 客户端可将该 JSON 落盘为本地文件供用户下载

#### 8) 注销账户

- **DELETE** `/users/me`
- **Auth**: Yes
- **Response 200**

```json
{ "success": true }
```

- **Compliance Notes:**
  - 当前为**软删除**（`is_active=false` 等）
  - GDPR Right to Erasure 严格语义需要硬删除关联数据，建议在 follow-up plan 中补齐：
    - 用户订阅清空 / 解绑
    - 推送 token 撤销
    - 历史日志匿名化（保留事件审计但去除 PII）

## Common Error Contract

| Status | 触发场景 | Body |
|---|---|---|
| 400 | 注册时邮箱已存在 / OAuth provider 非 google/apple / 请求体校验失败 | `{ "detail": "..." }` |
| 401 | 密码错误 / refresh token 失效 / 受保护接口未携带鉴权 | `{ "detail": "..." }` |
| 404 | `GET /users/me` 用户不存在 | `{ "detail": "User not found" }` |
| 422 | Pydantic 校验失败（FastAPI 默认） | `{ "detail": [{ "loc": [...], "msg": "...", "type": "..." }] }` |

## Frontend Suggested Flow

### 邮箱注册

1. UI 收集 `email` + `password` + `display_name`
2. `POST /auth/register` → 拿到 `access_token` + `refresh_token` + `user`
3. 客户端持久化 token（见 `02-01-FLUTTER_AUTH_SCAFFOLD.md`）
4. 后续请求由 `AuthInterceptor` 自动注入 `Authorization` 头

### Google / Apple 登录

1. 客户端调用 `google_sign_in` / `sign_in_with_apple` SDK，拿到 `provider_id` + `email` + `display_name`
2. `POST /auth/oauth/{provider}` 携带这些字段
3. 拿到 token 后流程同上

### Token 刷新

1. `AuthInterceptor` 收到 401（access_token 过期）
2. 自动 `POST /auth/refresh` 携带 `refresh_token`
3. 拿到新的 `access_token`，重放原请求
4. 若 refresh token 也过期 → 引导用户重新登录

### GDPR 导出

1. UI 设置页提供 "导出我的数据" 按钮
2. `GET /users/me/export` → 拿到 JSON
3. 客户端落盘为 `newsflow-export-<userid>-<date>.json`

### GDPR 注销

1. UI 设置页提供 "删除账户" 按钮 + 二次确认弹窗
2. `DELETE /users/me`
3. 客户端清空本地 token + 跳转到登录页

## Cross-Reference

- 关联实现：`backend/api/v1/auth.py`、`backend/api/v1/users.py`、`backend/services/auth.py`、`backend/services/user.py`、`backend/core/security.py`、`backend/core/dependencies.py`
- 与 02-02 共享：`get_current_user_id` 鉴权依赖、`x-user-id` 测试兜底
- Flutter 接入：[`02-01-FLUTTER_AUTH_SCAFFOLD.md`](./02-01-FLUTTER_AUTH_SCAFFOLD.md)
