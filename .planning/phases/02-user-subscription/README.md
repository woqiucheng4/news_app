# Phase 02 — 用户系统 + 订阅管理

> 本目录是 Phase 02 的全部产物入口。Plan items 以 `02-XX-` 前缀编号，每个 plan item 完结时配 `02-XX-PHASE_SUMMARY.md` 作为收尾索引。

## Phase Overview

| 字段 | 内容 |
|---|---|
| Goal | 建立完整的用户账户系统和话题订阅功能，支持个性化信息获取 |
| Depends on | Phase 01（基础架构 + 内容采集管道） |
| Requirements 覆盖 | USER-01 ~ USER-07, USER-09 |
| Success Criteria | 用户可注册登录、浏览/订阅话题、管理订阅列表、搜索内容、导出/删除数据（GDPR） |
| 上游契约 | [`/.planning/PRD.md`](../../PRD.md), [`TECHNICAL_DESIGN.md`](../../TECHNICAL_DESIGN.md), [`FLUTTER_DESIGN.md`](../../FLUTTER_DESIGN.md) |

## Plan Items 状态

| Plan | 标题 | 需求 | 状态 | 收尾索引 |
|---|---|---|---|---|
| **02-01** | **用户认证（邮箱/Google/Apple）+ GDPR 数据导出/删除** | USER-01/02/03/09 | ✅ Done | [`02-01-PHASE_SUMMARY.md`](./02-01-PHASE_SUMMARY.md) |
| **02-02** | **话题目录 + 关键词订阅 + 订阅管理细化** | USER-04/05/06 | ✅ Done | [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) |
| **02-03** | **内容搜索** | USER-07 | ✅ Done | [`02-03-PHASE_SUMMARY.md`](./02-03-PHASE_SUMMARY.md) |

> ✅ **Phase 2 三个 plan items 全部交付**。USER-08（个人偏好设置）后端在 02-01 已交付（`PUT /users/me/settings`），UI 落地在 Phase 3。

## 文档矩阵

```
02-user-subscription/
├── README.md                                       # 本文：phase 入口
│
├── 02-01-PHASE_SUMMARY.md                          # 02-01 收尾索引页
├── 02-01-API_CONTRACT.md                           # Auth + GDPR 接口 SoT
├── 02-01-VALIDATION.md                             # 验证证据 + GDPR 合规说明
├── 02-01-UAT.md                                    # USER-01/02/03/09 UAT 场景（17 项）
├── 02-01-FLUTTER_AUTH_SCAFFOLD.md                  # Flutter Auth 接入 + Token 存储
│
├── 02-02-PHASE_SUMMARY.md                          # 02-02 收尾索引页
├── 02-02-API_CONTRACT.md                           # 订阅接口 SoT
├── 02-02-VALIDATION.md                             # 验证证据
├── 02-02-UAT.md                                    # USER-04/05/06 UAT 场景（15 项）
├── 02-02-FLUTTER_BOOTSTRAP_EXECUTION_PLAN.md       # Flutter 半天最小联调执行序
├── 02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md          # 网络层骨架
├── 02-02-FLUTTER_FREEZED_MODELS.md                 # DTO 模板
├── 02-02-FLUTTER_REPOSITORY_RIVERPOD_NOTIFIERS.md  # Repository + Notifier
├── 02-02-FLUTTER_MINIMAL_UI_TEMPLATES.md           # 最小 UI 模板
│
├── 02-03-PHASE_SUMMARY.md                          # 02-03 收尾索引页
├── 02-03-API_CONTRACT.md                           # 内容搜索接口 SoT
├── 02-03-VALIDATION.md                             # 验证证据 + Open Hardening
├── 02-03-UAT.md                                    # USER-07 UAT 场景（15 项）
└── 02-03-FLUTTER_SEARCH_SCAFFOLD.md                # Flutter 防抖搜索 + 双 Tab UI
```

## 跨 Phase 工程基础设施（02-02 落地后通用）

这些工件部署在仓库根，不属于本 phase 目录但由 02-02 引入：

| 工件 | 路径 | 作用 |
|---|---|---|
| Backend CI | `.github/workflows/backend-ci.yml` | seed 语法检查 + 订阅回归 + 全量 pytest |
| Flutter CI | `.github/workflows/flutter-ci.yml` | 检测到 `frontend/pubspec.yaml` 自动启用 |
| PR 模板 | `.github/PULL_REQUEST_TEMPLATE.md` | 含订阅/Feed surface checklist |
| CODEOWNERS | `.github/CODEOWNERS` | 订阅/Feed/Auth/Schema 关键路径绑定 reviewer |
| Demo seed | `backend/scripts/seed_demo_*.py` + `make demo-seed` / `make demo-up` | 一键演示数据 |

## 推荐进入路径

| 角色 / 场景 | 推荐入口 |
|---|---|
| 第一次了解 02-02 | [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) |
| 前后端字段对接 | [`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md) |
| 启动 Flutter 联调 | [`02-02-FLUTTER_BOOTSTRAP_EXECUTION_PLAN.md`](./02-02-FLUTTER_BOOTSTRAP_EXECUTION_PLAN.md) |
| 提交 PR 前自检 | [`02-02-VALIDATION.md`](./02-02-VALIDATION.md) + `.github/PULL_REQUEST_TEMPLATE.md` |
| 接 02-01 / 02-03 | 等待 `/gsd-plan-phase` 拆分；以本表为索引 |

## Open Items

- ✅ ~~02-03 收尾~~ Done（2026-05-29）
- `CODEOWNERS` 中 `@OWNER` 占位需在首个真实 PR 前替换
- Flutter 工程实际初始化（`flutter create newsflow_app`）尚未执行
- USER-08（个人偏好设置）跨 Phase：后端在 02-01 已交付（`PUT /users/me/settings`），UI 落地在 Phase 3
- Open Hardening 项移交后续 plan：
  - **02-01**：OAuth ID Token 验证、Refresh Token 旋转、GDPR 硬删除、邮箱验证、密码重置
  - **02-03**：PostgreSQL 全文索引（`tsvector` + GIN）、多关键词 AND、相关度排序、分页
