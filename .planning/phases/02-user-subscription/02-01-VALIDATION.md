# 02-01 Validation — 用户认证（邮箱/Google/Apple）+ GDPR

## Scope

- Phase: 02 用户系统 + 订阅管理
- Plan item: 02-01
- Target requirements:
  - **USER-01**：用户可通过邮箱注册和登录
  - **USER-02**：用户可通过 Google 账号登录
  - **USER-03**：用户可通过 Apple 账号登录
  - **USER-09**：用户数据符合 GDPR 规范，支持数据导出和删除

## Delivered API Capabilities

### USER-01：邮箱注册 + 登录

- `POST /api/v1/auth/register`
  - 邮箱去重，自动哈希密码（bcrypt via `passlib`）。
  - 自动创建 `UserSettings` 默认行。
  - 注册即登录态：返回 `access_token` + `refresh_token` + `user`。
- `POST /api/v1/auth/login`
  - 邮箱 + 密码校验，密码错误统一返回 401（无信息泄漏）。
  - 与注册返回结构一致。
- `POST /api/v1/auth/refresh`
  - 校验 `type=refresh` claim，签发新的 access token。
  - **不旋转 refresh token**（待硬化）。

### USER-02 / USER-03：OAuth（Google / Apple）

- `POST /api/v1/auth/oauth/{provider}`（provider ∈ {google, apple}）
  - 三段式查找：`provider_id` → `email` → 创建新用户。
  - 已存在用户的 `email` 路径会自动补绑 `provider_id`，避免重复账号。
  - 非 google/apple 的 provider 返回 400 `Unsupported provider`。

### USER-09：GDPR 数据导出 / 注销

- `GET /api/v1/users/me/export`
  - 返回 `{user, settings, exported_at}` JSON。
  - 客户端可落盘为本地文件供用户下载。
- `DELETE /api/v1/users/me`
  - 当前为软删除（`UserRepository.delete()`）。
  - **Open Hardening**：待补订阅清空、推送 token 撤销、关联日志匿名化。

### 周边能力

- `GET /api/v1/users/me`：当前用户资料。
- `PUT /api/v1/users/me/settings`：推送 / 语言 / 主题偏好（USER-08 后端能力，UI 由 Phase 3 落地）。

## Authentication Contract

- **JWT**：HS256 签名，`SECRET_KEY` 来自 `.env`。
- **Access Token claims**：`sub`、`email`、`is_premium`、`type=access`、`exp`。
- **Refresh Token claims**：`sub`、`type=refresh`、`exp`。
- **携带方式**：
  - 生产：`Authorization: Bearer <access_token>`
  - 测试兜底：`x-user-id: <uuid>`（与 02-02 共享同一鉴权依赖 `get_current_user_id`）
- **接口对接点**：所有受保护端点的鉴权依赖统一到 `core/dependencies.py::get_current_user_id`。

## Validation Evidence

### 单元 / 集成测试

| 测试文件 | 覆盖 |
|---|---|
| `backend/tests/test_auth_api.py` | `/auth/register`、`/auth/login`、`/auth/oauth/{provider}`、`/auth/refresh` 端点级 |
| `backend/tests/test_auth_service.py` | `AuthService` 业务逻辑（注册重复、登录失败、OAuth 三段式查找、refresh token 校验） |
| `backend/tests/test_user_service.py` | `UserService.get_user/update_settings/export_user_data/delete_user` |
| `backend/tests/test_api_endpoints.py` | 跨接口的鉴权 / 401 / 兜底头集成 |
| `backend/tests/test_auth_user_uat_flow.py` | UAT 合同回归：OAuth(google/apple)+同邮箱合并、`/users/me` 鉴权、settings、GDPR 导出/注销、注销后再注册边界 |

### 本地命令（已跑通）

```bash
cd backend
.venv/bin/pytest -q tests/test_auth_api.py
.venv/bin/pytest -q tests/test_auth_service.py
.venv/bin/pytest -q tests/test_user_service.py
.venv/bin/pytest -q tests/test_auth_user_uat_flow.py
.venv/bin/pytest -q tests/test_api_endpoints.py
```

### CI 等价命令（已纳入 `.github/workflows/backend-ci.yml`）

```bash
pytest -q tests/test_auth_api.py tests/test_auth_service.py tests/test_user_service.py
pytest -q  # 全量
```

> 02-02 CI 工作流的"全量 pytest"步骤已隐含覆盖 02-01 测试，本 plan 不需要新增独立 workflow。

## GDPR Compliance Notes

### Right to Access（数据访问权）

- ✅ `GET /users/me/export` 提供基础用户 + 设置数据的 JSON 导出
- ⚠️ **Open Hardening**：当前导出**不包含**：
  - 用户订阅历史与设置（建议在 02-03 / 03-XX 拆解时合并）
  - 推送通知历史（待 04 phase 引入推送后补）
  - 登录 / 操作审计日志（如启用）

### Right to Erasure（数据删除权）

- ✅ `DELETE /users/me` 触发软删除（`is_active=false` 等）
- ⚠️ **Open Hardening**：严格 GDPR 语义需要：
  - 关联订阅清空 / 标记为已注销用户
  - 推送 token / OAuth provider_id 解绑或清除
  - PII 匿名化（保留事件统计但去除可识别字段）
  - 实际硬删除策略（如 30 天留存期后真正擦除）

### Data Minimization

- 注册仅强制 `email` + `password`，`display_name` 可选
- OAuth 仅消费 SDK 返回的最小字段（provider_id + email + 可选 displayName/avatar）
- 后端不存储 OAuth ID Token / Access Token（仅记录 provider_id）

### Data Storage Location

- PostgreSQL（Supabase）— 海外数据中心（与 PROJECT.md 约束一致）
- 密码：bcrypt 哈希存储，不存明文
- JWT：服务端不存（无状态），客户端存储在 Flutter Secure Storage（iOS Keychain / Android EncryptedSharedPreferences）

## Notes for Frontend Integration

- Flutter Auth 接入完整骨架：[`02-01-FLUTTER_AUTH_SCAFFOLD.md`](./02-01-FLUTTER_AUTH_SCAFFOLD.md)
- Token 持久化使用 `flutter_secure_storage`（替换 02-02 中的 `InMemoryAuthTokenReader`）
- 401 自动刷新由 `AuthInterceptor.onError` 处理，业务代码无感知
- GDPR 导出 / 注销 UI 入口建议放在"设置"页面下的"账户与隐私"分组

## CI / Repo Infrastructure

复用 02-02 已落地的工程基础设施：

| 工件 | 路径 | 02-01 相关 |
|---|---|---|
| Backend CI | `.github/workflows/backend-ci.yml` | 全量 pytest 已覆盖 auth 测试 |
| PR 模板 | `.github/PULL_REQUEST_TEMPLATE.md` | 改动 auth/users 时勾选 "鉴权依赖统一走 get_current_user_id" |
| CODEOWNERS | `.github/CODEOWNERS` | 已绑定 `/auth.py`、`/services/auth.py`、`/core/security.py`、`/core/dependencies.py` |

## Open Hardening（移交后续 plan）

| 项 | 描述 | 建议归属 |
|---|---|---|
| OAuth ID Token 验证 | 当前未校验 Google/Apple 返回的 ID Token 签名，存在伪造 provider_id 风险 | 02-01 后续硬化 plan |
| Refresh Token 旋转 | 当前 `/refresh` 不签发新 refresh，长期有效 token 风险 | 同上 |
| Refresh Token 撤销 | 用户登出 / 注销时未将 refresh token 加入黑名单 | 同上 |
| 邮箱验证流程 | 当前 `is_verified=True` 直发，未实现邮件验证链路 | 跨 phase（依赖邮件服务） |
| 密码重置 | 暂未实现 forgot-password 流程 | 同上 |
| GDPR 导出扩展 | 包含订阅历史 + 推送日志 | 03 / 04 phase 增量补 |
| GDPR 硬删除 | 软删 → 30 天后真正擦除 | 独立 plan |
| 速率限制（已落地基础版） | `auth` 关键端点已启用 Redis 限流（`/auth/login` 失败尝试限流 + `/auth/register`、`/auth/refresh` 请求限流）；后续可扩展为分层策略（设备指纹/用户维度） | 安全硬化 plan |

## Phase Summary（02-01 收尾索引）

- 完整聚合页：[`02-01-PHASE_SUMMARY.md`](./02-01-PHASE_SUMMARY.md)
- 用途：作为本 plan item 全部产物（接口、文档、UAT）的最终索引入口。
