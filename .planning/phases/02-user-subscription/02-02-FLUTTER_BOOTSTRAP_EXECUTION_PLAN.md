# 02-02 Flutter Bootstrap Execution Plan (Half-day)

> Phase index: [`02-02-PHASE_SUMMARY.md`](./02-02-PHASE_SUMMARY.md) · API SoT: [`02-02-API_CONTRACT.md`](./02-02-API_CONTRACT.md)

## Goal

- 在没有现成 Flutter 工程的前提下，半天内完成可运行的最小联调闭环：
  - 登录后带 token 调用后端
  - 话题目录列表可见
  - 关键词订阅可创建
  - 我的订阅可展示
  - Feed 可拉取第一页

## Timebox (4-6 hours)

- **Hour 1:** 项目初始化 + 依赖安装 + 目录骨架
- **Hour 2:** 网络层（Dio + AuthInterceptor）与 DTO 生成
- **Hour 3:** API Datasource + Repository 接线
- **Hour 4:** Riverpod Notifier + 最小页面联调
- **Hour 5-6 (buffer):** 错误处理、空态、基础 polish

## Step-by-step Checklist

## Step 0: Create Project

- 命令：
  - `flutter create newsflow_app`
- 进入工程并校验：
  - `flutter pub get`
  - `flutter run -d <device>`

## Step 1: Add Dependencies

- 在 `pubspec.yaml` 增加：
  - `dio`
  - `flutter_riverpod`
  - `riverpod_annotation`
  - `freezed_annotation`
  - `json_annotation`
- `dev_dependencies` 增加：
  - `build_runner`
  - `freezed`
  - `json_serializable`
  - `riverpod_generator`

## Step 2: Create Folder Skeleton

- 创建以下目录：
  - `lib/core/network/`
  - `lib/features/subscription/data/datasources/`
  - `lib/features/subscription/data/models/`
  - `lib/features/subscription/data/repositories/`
  - `lib/features/subscription/presentation/providers/`
  - `lib/features/subscription/presentation/pages/`
  - `lib/features/feed/data/datasources/`
  - `lib/features/feed/data/models/`
  - `lib/features/feed/data/repositories/`
  - `lib/features/feed/presentation/providers/`
  - `lib/features/feed/presentation/pages/`

## Step 3: Paste Core Network Files

- 来源文档：`02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md`
- 先创建：
  - `api_client.dart`
  - `auth_interceptor.dart`
- 临时 token 方案：
  - 先写一个 `InMemoryAuthTokenReader` 返回固定 token（或 mock token），后续替换真实登录存储。

## Step 4: Paste Freezed DTO Files

- 来源文档：`02-02-FLUTTER_FREEZED_MODELS.md`
- 先落地：
  - `topic_category_dto.dart`
  - `topic_dto.dart`
  - `subscription_dto.dart`
  - `article_dto.dart`
  - `feed_response_dto.dart`
- 运行生成：
  - `dart run build_runner build --delete-conflicting-outputs`

## Step 5: Paste Datasource + Repository

- 来源文档：
  - `02-02-FLUTTER_DIO_RIVERPOD_SCAFFOLD.md`
  - `02-02-FLUTTER_REPOSITORY_RIVERPOD_NOTIFIERS.md`
- 优先落地最小接口：
  - `getCategories`
  - `getTopics`
  - `subscribeKeyword`
  - `getMySubscriptions`
  - `getFeed`

## Step 6: Paste Riverpod Notifiers

- 来源文档：`02-02-FLUTTER_REPOSITORY_RIVERPOD_NOTIFIERS.md`
- 最小保留：
  - `TopicsNotifier`
  - `MySubscriptionsNotifier`
  - `FeedNotifier`

## Step 7: Build Minimal Pages

- 页面建议（先不用复杂路由）：
  - `SubscriptionPage`：
    - 分类/话题列表
    - 关键词输入框 + 订阅按钮
    - 我的订阅列表
  - `FeedPage`：
    - 文章列表（标题 + 摘要）
- `main.dart` 用 `DefaultTabController` 或 `BottomNavigationBar` 先串两页。
- 页面模板可直接参考：`02-02-FLUTTER_MINIMAL_UI_TEMPLATES.md`。

## Step 8: Wire Environment

- 新增常量：
  - `const apiBaseUrl = 'http://<your-host>:8000';`
- Android 模拟器常用：
  - `http://10.0.2.2:8000`
- iOS 模拟器常用：
  - `http://127.0.0.1:8000`

## Step 9: Smoke Test Script

- 验证顺序：
  0. 后端先执行话题种子（如本地非 docker 自动链路）：
     - `python backend/scripts/seed_topics.py`
     - （可选）插入演示用户与默认订阅：
       - `python backend/scripts/seed_demo_user_and_subscriptions.py`
     - （可选）插入演示 Feed 内容：
       - `python backend/scripts/seed_demo_articles.py`
     - （推荐）一键执行全部演示数据：
       - `python backend/scripts/seed_demo_all.py`
      - Docker 链路可通过环境变量自动执行 demo seed：
        - `ENABLE_DEMO_SEED=true docker compose up --build -d`
        - 或写入 `backend/.env`：`ENABLE_DEMO_SEED=true`
      - 也可使用 Makefile 快捷命令：
        - 本地：`make demo-seed`
        - Docker：`make demo-up`
  1. 打开 Subscription 页，分类加载成功
  2. 话题列表加载成功，能看到 `is_subscribed`
  3. 输入关键词，点订阅，列表刷新
  4. 我的订阅显示新增项
  5. 打开 Feed 页，第一页加载成功

## First-file Creation Order (Exact)

1. `lib/core/network/auth_interceptor.dart`
2. `lib/core/network/api_client.dart`
3. `lib/features/subscription/data/models/topic_category_dto.dart`
4. `lib/features/subscription/data/models/topic_dto.dart`
5. `lib/features/subscription/data/models/subscription_dto.dart`
6. `lib/features/feed/data/models/article_dto.dart`
7. `lib/features/feed/data/models/feed_response_dto.dart`
8. `lib/features/subscription/data/datasources/subscription_api.dart`
9. `lib/features/feed/data/datasources/feed_api.dart`
10. `lib/features/subscription/data/repositories/subscription_repository.dart`
11. `lib/features/feed/data/repositories/feed_repository.dart`
12. `lib/features/subscription/presentation/providers/subscription_providers.dart`
13. `lib/features/feed/presentation/providers/feed_providers.dart`
14. `lib/features/subscription/presentation/pages/subscription_page.dart`
15. `lib/features/feed/presentation/pages/feed_page.dart`
16. `lib/main.dart`

## Risk Controls

- `401` 频发：先检查 token 是否注入到 `Authorization`。
- `CORS`/网络失败：先用同网段真机或模拟器 localhost 映射。
- DTO 解析异常：优先核对 `snake_case` -> `@JsonKey`。
- 重排失败：保留乐观更新回滚逻辑，避免 UI 与后端状态不一致。

## Definition of Done

- App 可启动并展示两个页面（订阅、Feed）
- Subscription 主链路可用（目录、关键词订阅、我的订阅）
- Feed 首屏可加载
- 全链路不依赖手工改接口返回字段
