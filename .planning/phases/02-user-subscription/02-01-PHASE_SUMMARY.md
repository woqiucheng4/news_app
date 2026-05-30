# 02-01 Phase Summary（收尾索引页）

> Phase: 02 用户系统 + 订阅管理
> Plan item: 02-01 — 用户认证（邮箱/Google/Apple）+ GDPR 数据导出/删除
> 状态：✅ 后端接口已落地、文档链路成型、UAT 已清零（17/17 pass）；Flutter Auth 接入文档已就绪。

---

## 1. 范围与目标

| 项 | 内容 |
|---|---|
| Phase Goal | 让用户可以用邮箱 / Google / Apple 注册登录，并在符合 GDPR 的前提下导出与注销账户 |
| Requirements 覆盖 | USER-01（邮箱）、USER-02（Google）、USER-03（Apple）、USER-09（GDPR） |
| 上游契约 | `.planning/REQUIREMENTS.md`、`.planning/PRD.md`、`.planning/TECHNICAL_DESIGN.md`、`.planning/FLUTTER_DESIGN.md` |
| 下游消费方 | 02-02 订阅系统（共享 `get_current_user_id` 鉴权依赖）、Flutter 客户端（替换 02-02 中的 `InMemoryAuthTokenReader`） |

> 注：USER-07（内容搜索）属于 02-03，不在本 plan 范围。

---

## 2. 后端接口产物（Single Source of Truth）

接口契约统一登记于 [`02-01-API_CONTRACT.md`](./02-01-API_CONTRACT.md)，对应实现位于 `backend/api/v1/{auth,users}.py` + `backend/services/{auth,user}.py`。

### Auth

| # | Method & Path | Auth | 用途 | 关联需求 |
|---|---|---|---|---|
| 1 | `POST /api/v1/auth/register` | No | 邮箱注册（含密码哈希 + 默认 settings） | USER-01 |
| 2 | `POST /api/v1/auth/login` | No | 邮箱密码登录 | USER-01 |
| 3 | `POST /api/v1/auth/oauth/{provider}` | No | Google / Apple OAuth 登录（自动建账号或合并） | USER-02 / USER-03 |
| 4 | `POST /api/v1/auth/refresh` | No | 用 refresh token 换发新 access | USER-01 |

### User Profile + GDPR

| # | Method & Path | Auth | 用途 | 关联需求 |
|---|---|---|---|---|
| 5 | `GET /api/v1/users/me` | Yes | 当前用户资料 | USER-01 |
| 6 | `PUT /api/v1/users/me/settings` | Yes | 更新推送 / 语言 / 主题偏好 | USER-08 后端能力 |
| 7 | `GET /api/v1/users/me/export` | Yes | GDPR 数据导出（user + settings） | **USER-09** |
| 8 | `DELETE /api/v1/users/me` | Yes | GDPR 注销账户（软删除） | **USER-09** |

### Token 体系

- `access_token` claims：`sub` / `email` / `is_premium` / `type=access` / `exp`
- `refresh_token` claims：`sub` / `type=refresh` / `exp`
- 签名算法：HS256（SECRET_KEY 来自 `.env`）
- 鉴权依赖统一：`core/dependencies.py::get_current_user_id`（与 02-02 共享）

---

## 3. Flutter 接入文档

| 文档 | 作用 |
|---|---|
| [`02-01-FLUTTER_AUTH_SCAFFOLD.md`](./02-01-FLUTTER_AUTH_SCAFFOLD.md) | 完整 Auth 接入骨架：Secure Storage Token Reader + 401 自动刷新 + Google/Apple SDK + GDPR 操作 |

**关键升级路径（从 02-02 临时方案 → 02-01 正式实现）**：

| 02-02 (临时) | 02-01 (正式) |
|---|---|
| `InMemoryAuthTokenReader` | `SecureStorageTokenReader`（Keychain / EncryptedSharedPrefs） |
| Dio 单实例 + 静态 token | 双 Dio（业务 + refresh）+ 401 自动刷新 |
| 无登录页 | `LoginPage` + `RegisterPage` + OAuth 按钮 |
| 启动直接拉数据 | `authNotifierProvider.build()` 判定登录态再路由 |

详见 [`02-01-FLUTTER_AUTH_SCAFFOLD.md`](./02-01-FLUTTER_AUTH_SCAFFOLD.md) §9 Migration 章节。

---

## 4. 验证证据（Validation Evidence）

详见 [`02-01-VALIDATION.md`](./02-01-VALIDATION.md)。关键摘要：

### 自动化测试（已纳入 CI 全量 pytest）

| 测试文件 | 覆盖范围 |
|---|---|
| `backend/tests/test_auth_api.py` | 4 个 auth 端点端到端 |
| `backend/tests/test_auth_service.py` | `AuthService` 业务逻辑（重复注册、登录失败、OAuth 三段式、refresh 校验） |
| `backend/tests/test_user_service.py` | `UserService` get/update/export/delete |
| `backend/tests/test_auth_user_uat_flow.py` | OAuth 合并账号 + `/users/me` 鉴权 + GDPR 注销链路 |
| `backend/tests/test_api_endpoints.py` | 跨接口鉴权 / 401 / `x-user-id` 兜底 |

### 本地命令

```bash
.venv/bin/pytest -q tests/test_auth_api.py tests/test_auth_service.py tests/test_user_service.py tests/test_auth_user_uat_flow.py
```

### UAT（17/17 pass）

[`02-01-UAT.md`](./02-01-UAT.md) — 17 项用户视角测试场景，覆盖：
- Tests 1-5：邮箱注册/登录/refresh 主链路
- Tests 6-9：OAuth Google/Apple + 合并账号边界（后端契约自动化已覆盖）
- Tests 10-12：用户资料 + 设置
- Tests 13-14：GDPR 导出 + 注销
- Tests 15-17：边界与 schema 校验

---

## 5. GDPR 合规现状与 Open Hardening

| 维度 | 当前实现 | 待硬化 |
|---|---|---|
| Right to Access | ✅ `GET /users/me/export` 返回 user + settings | 扩展含订阅历史 / 推送日志 |
| Right to Erasure | ⚠️ 软删除（`is_active=false`） | 补订阅清空、token 撤销、PII 匿名化、30天后硬删 |
| Data Minimization | ✅ 注册仅强制 email + password | — |
| Data Storage | ✅ 海外 PostgreSQL（Supabase） / bcrypt 密码 / 客户端 Keychain | — |
| OAuth ID Token 验证 | ❌ 当前未校验 Google/Apple ID Token 签名 | 后续硬化 plan |
| Refresh Token 旋转 / 撤销 | ❌ 未旋转、未黑名单 | 同上 |
| 邮箱验证流程 | ❌ 当前 `is_verified=True` 直发 | 跨 phase（依赖邮件服务） |
| 密码重置 | ❌ 未实现 | 同上 |
| 登录速率限制 | ✅ 已启用 Redis 限流（登录失败尝试）；注册/刷新端点也已启用基础限流 | 后续增强策略仍在安全硬化 plan |

> 详见 [`02-01-VALIDATION.md`](./02-01-VALIDATION.md) §Open Hardening。

---

## 6. 文档地图（02-01 全部产物索引）

```
.planning/phases/02-user-subscription/
├── 02-01-API_CONTRACT.md             # 接口契约（前后端共识）
├── 02-01-VALIDATION.md               # 验证证据 + GDPR 合规说明
├── 02-01-UAT.md                      # 17 项用户视角验收场景
├── 02-01-FLUTTER_AUTH_SCAFFOLD.md    # Flutter Auth 接入完整骨架
└── 02-01-PHASE_SUMMARY.md            # ← 本文（收尾索引页）

backend/
├── api/v1/auth.py                    # 4 个 auth 端点
├── api/v1/users.py                   # 4 个 user 端点（含 GDPR）
├── services/auth.py                  # AuthService 业务逻辑
├── services/user.py                  # UserService（含 export / delete）
├── core/security.py                  # JWT + bcrypt
├── core/dependencies.py              # get_current_user_id（与 02-02 共享）
├── tests/test_auth_api.py
├── tests/test_auth_service.py
├── tests/test_user_service.py
└── tests/test_auth_user_uat_flow.py
```

---

## 7. Definition of Done（02-01 收尾判定）

- [x] 4 个 auth 接口 + 4 个 user 接口全部交付并通过测试
- [x] JWT access/refresh token 体系实现，HS256 签名
- [x] 鉴权依赖统一到 `get_current_user_id`，与 02-02 共享
- [x] OAuth 三段式查找（provider_id → email → 创建）防止重复账号
- [x] GDPR 导出（user + settings JSON）+ 注销（软删除）
- [x] API 契约文档（`02-01-API_CONTRACT.md`）与代码字段一一对齐
- [x] Flutter Auth 接入文档（`02-01-FLUTTER_AUTH_SCAFFOLD.md`）覆盖：Secure Storage、401 刷新、OAuth、GDPR
- [x] UAT 文件（`02-01-UAT.md`）17 项场景成 SDK 可识别格式
- [x] CI 已隐含覆盖（02-02 backend-ci 全量 pytest 包含 auth 测试）
- [x] CODEOWNERS 已绑定 auth.py / security.py / dependencies.py
- [x] 本文（PHASE_SUMMARY.md）作为收尾索引页发布
- [ ] **OAuth ID Token 签名验证**（移交 Open Hardening）
- [ ] **Refresh Token 旋转 + 撤销**（移交 Open Hardening）
- [ ] **GDPR 硬删除策略 + 关联清理**（移交 Open Hardening）
- [ ] **邮箱验证 / 密码重置流程**（跨 phase，依赖邮件服务）

---

## 8. 已知 Follow-up（移交后续 plan / phase）

| 项 | 类型 | 建议归属 |
|---|---|---|
| OAuth ID Token 签名校验 | Security | 02-01 后续硬化 plan |
| Refresh Token 旋转 + 撤销黑名单 | Security | 同上 |
| GDPR 硬删除（30 天延迟）+ 关联订阅/推送 token 清理 | Compliance | 独立 plan |
| 邮箱验证 + 密码重置流程 | Feature | 跨 phase（需邮件服务，可在 04 phase 推送基础设施落地后合并） |
| 细粒度限流策略（设备指纹/用户维度/动态阈值） | Security | 安全硬化 plan |
| GDPR 导出扩展（订阅历史 + 推送日志） | Compliance | 03 / 04 phase 增量补 |
| Flutter Auth UI 实际实现（`LoginPage` 等） | Frontend | Phase 3 Flutter 实施 |

---

## 9. 快速参考（Cheat Sheet）

```bash
# Backend 联调
cd backend && make demo-up
.venv/bin/pytest -q tests/test_auth_api.py tests/test_auth_service.py tests/test_user_service.py tests/test_auth_user_uat_flow.py

# 端点冒烟测试
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@test.com","password":"abcdef","display_name":"Alice"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@test.com","password":"abcdef"}'

# GDPR 导出（需先获取 access token）
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/users/me/export

# CI 等价
pytest -q tests/test_auth_api.py tests/test_auth_service.py tests/test_user_service.py
pytest -q  # 全量
```

---

> 本文为 **02-01 plan item 的最终聚合页**，建议在所有 02-01 相关 PR/任务的描述中引用本文，作为前后端、CI 与文档链路的单一索引入口。
