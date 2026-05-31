# 本地开发跑通指南

最短路径：**Docker 起数据库 + API**，可选 **demo 数据**，再 **Flutter 连本机**。

## 0. 前置

- Docker Desktop（或 OrbStack）已启动
- Python 3.12+（仅在不走 Docker API、本地 `make run` 时需要）
- Flutter 3.x（跑客户端时需要）

## 0. 一键初始化（首次推荐）

```bash
./scripts/local-bootstrap.sh --demo
cd backend && set -a && source .env && set +a && make run
```

## 1. 后端（推荐：Docker 一键）

```bash
cd backend
cp .env.example .env   # 若尚无 .env
```

在 `.env` 中填入 **`OPENAI_API_KEY`**（摘要功能需要；不填也能启动，但新摘要会失败）。

**DeepSeek（OpenAI 兼容）示例：**

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

```bash
make docker-up
# 或带演示数据（登录/Feed 更省事）：
ENABLE_DEMO_SEED=true make docker-up
```

验收：

```bash
curl http://localhost:8000/health
open http://localhost:8000/docs
open http://localhost:8000/feed
```

| 检查项 | 期望 |
|--------|------|
| `/health` | `"status":"healthy"` |
| `/docs` | Swagger 可打开 |
| `/feed` | Web 信息流有卡片 |

查看日志：`make docker-logs`

停止：`make docker-down`

### 仅数据库用 Docker、API 本机跑（可选）

```bash
docker compose up -d postgres redis
make install && make migrate && make seed
make demo-seed    # 演示用户 + 文章
make run          # http://localhost:8000
```

## 2. 演示账号（未开 ENABLE_DEMO_SEED 时）

```bash
cd backend
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/newflow
.venv/bin/python scripts/seed_demo_all.py
```

查询 demo 用户 ID（Flutter / curl 用 `x-user-id` 头）：

```bash
docker compose exec -T postgres psql -U postgres -d newflow \
  -c "SELECT id, email FROM users WHERE email='demo@newsflow.app';"
```

用该 UUID 测 Feed：

```bash
curl -H "x-user-id: <UUID>" "http://localhost:8000/api/v1/articles/feed?page_size=5"
```

## 3. Flutter 客户端

```bash
cd frontend
flutter pub get
flutter gen-l10n
flutter run
```

默认 API：`http://localhost:8000/api/v1`（iOS 模拟器 / macOS 桌面）。

| 运行目标 | 命令 |
|----------|------|
| Android 模拟器 | `flutter run --dart-define=NEWSFLOW_API_BASE_URL=http://10.0.2.2:8000/api/v1` |
| 真机（同 Wi‑Fi） | `flutter run --dart-define=NEWSFLOW_API_BASE_URL=http://<你电脑局域网IP>:8000/api/v1` |
| 已有 access token | 加 `--dart-define=NEWSFLOW_ACCESS_TOKEN=<token>` 可跳过登录 |

邮箱登录使用后端 JWT（无需 Supabase）：在 App 登录页注册/登录，或：

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpass12","display_name":"You"}'
```

OAuth（Google/Apple）需配置 Supabase，见 `frontend/README.md`。

## 4. 常见问题

| 现象 | 处理 |
|------|------|
| `docker compose` 拉镜像超时 | 配置镜像加速或重试；或只起 `postgres redis` + `make run` |
| `OPENAI_API_KEY` 未设置警告 | 在 `backend/.env` 填写 key 后 `docker compose up -d --force-recreate api` |
| Feed 401 | 登录拿 token（先 `alembic upgrade head` 确保库结构最新） |
| 注册 500 / `is_admin` 不存在 | `cd backend && alembic upgrade head` |
| 端口 8000 占用 | `lsof -i :8000` 后停掉旧进程或改端口 |
| Flutter 连不上 localhost | 模拟器/真机用上一节对应 `NEWSFLOW_API_BASE_URL` |

## 5. 一键自检

```bash
./scripts/verify_phase1_uat.sh
```
