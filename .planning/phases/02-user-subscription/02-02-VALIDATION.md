# 02-02 Validation: 话题目录 + 关键词订阅 + 订阅管理细化

## Scope

- Phase: 02 用户系统 + 订阅管理
- Plan item: 02-02
- Target requirements:
  - USER-04: 用户可浏览分类目录并订阅感兴趣的话题
  - USER-05: 用户可通过关键词添加订阅
  - USER-06: 用户可管理订阅列表（添加、删除、排序）

## Delivered API Capabilities

### USER-04: 话题目录 + 浏览订阅状态

- `GET /api/v1/subscriptions/topics/categories`
  - 返回分类目录及每类话题数量。
- `GET /api/v1/subscriptions/topics`
  - 支持 `category`、`q`、`limit`、`offset`。
  - 每条话题附带 `is_subscribed`，可直接展示“已订阅”态。
- `GET /api/v1/subscriptions/topics/{topic_id}`
  - 返回单个话题详情与当前用户订阅态。

### USER-05: 关键词订阅

- `POST /api/v1/subscriptions/subscribe/keyword`
  - 输入关键词自动生成 slug（`keyword-*`）。
  - 关键词对应话题不存在时自动创建。
  - 自动为当前用户创建/恢复订阅。

### USER-06: 订阅管理细化

- `POST /api/v1/subscriptions/subscribe`
  - 支持新订阅与历史订阅恢复（避免唯一约束冲突）。
- `PATCH /api/v1/subscriptions/me/{topic_id}`
  - 支持更新优先级、启停、推送开关、仅突发推送。
- `PUT /api/v1/subscriptions/me/reorder`
  - 批量更新多条订阅优先级。
- `DELETE /api/v1/subscriptions/unsubscribe/{topic_id}`
  - 取消订阅（订阅标记为非激活）。

## Authentication Contract

- 所有订阅相关端点需要用户身份。
- 用户相关端点和 `GET /api/v1/articles/feed` 已统一使用同一鉴权依赖。
- 当前支持两种方式：
  - 标准 Bearer JWT（`Authorization: Bearer <token>`，`type=access`）。
  - 测试兜底头（`x-user-id`）用于集成测试和本地调试。

## Validation Evidence

- Test file: `backend/tests/test_user_subscription_api.py`
  - 覆盖分类目录、话题查询、关键词订阅、订阅设置更新、批量排序、取消订阅。
- Regression file: `backend/tests/test_api_endpoints.py`
- Local run:
  - `.venv/bin/pytest -q tests/test_user_subscription_api.py` -> pass
  - `.venv/bin/pytest -q tests/test_api_endpoints.py` -> pass

## Notes for Frontend Integration

- 话题列表页建议优先拉取分类目录，再按分类/关键词请求 `topics` 列表。
- 订阅管理页可使用：
  - `GET /subscriptions/me` 拉取当前订阅；
  - `PATCH /subscriptions/me/{topic_id}` 更新单项设置；
  - `PUT /subscriptions/me/reorder` 批量提交排序结果。
- 前后端对接字段和示例请求见：`02-02-API_CONTRACT.md`。
- Flutter 接入代码骨架见：`02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md`。
- Freezed DTO 模板见：`02-02-FLUTTER_FREEZED_MODELS.md`。
- Repository + Notifier 模板见：`02-02-FLUTTER_REPOSITORY_RIVERPOD_NOTIFIERS.md`。
- Flutter 初始化与执行顺序见：`02-02-FLUTTER_BOOTSTRAP_EXECUTION_PLAN.md`。
- Flutter 最小 UI 页面模板见：`02-02-FLUTTER_MINIMAL_UI_TEMPLATES.md`。
- 前端联调演示数据可用脚本：`backend/scripts/seed_topics.py`、`backend/scripts/seed_demo_user_and_subscriptions.py`、`backend/scripts/seed_demo_articles.py`、`backend/scripts/seed_demo_all.py`。
- CI 工作流：
  - 后端：`.github/workflows/backend-ci.yml`（PR/Push 触发：seed 脚本语法检查 + 关键回归 + 全量 pytest）。
  - 前端：`.github/workflows/flutter-ci.yml`（占位 + 自动检测：检测到 `frontend/pubspec.yaml` 时跑 `flutter pub get / build_runner / analyze / test`）。
- PR 模板：`.github/PULL_REQUEST_TEMPLATE.md`，含订阅/Feed 接口改动专属 checklist，强制同步 02-02 文档链路。
- Code owners：`.github/CODEOWNERS`，为订阅/Feed 关键文件与 02-02 文档绑定 reviewer（默认占位 `@OWNER`，推送到真实远端前需替换为实际 GitHub handle）。

## Phase Summary（02-02 收尾索引）

- 完整聚合页：[`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md)
- 用途：作为本 plan item 全部产物（接口、文档、CI、模板、CODEOWNERS、Demo seed）的最终索引入口，PR 描述与跨文档跳转建议直接引用此文。
