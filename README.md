# NewsFlow

AI 驱动的全源信息聚合 App — Flutter 客户端 + FastAPI 后端 + PostgreSQL。

用户订阅话题，系统从全网采集信息并通过 AI 生成摘要推送。

## Repository layout

| Path | Description |
|------|-------------|
| [`frontend/`](frontend/) | Flutter app (Riverpod, go_router, Dio) |
| [`backend/`](backend/) | FastAPI API, ingestion, AI summarization |
| [`.planning/`](.planning/) | PRD, roadmap, phase plans, design docs |
| [`.github/workflows/`](.github/workflows/) | CI: backend pytest + Flutter analyze/test |

## Quick start

**Full local guide:** [`docs/LOCAL_DEV.md`](docs/LOCAL_DEV.md)

**Backend**

```bash
cd backend
cp .env.example .env   # set OPENAI_API_KEY in .env
make docker-up
curl http://localhost:8000/health
```

**Frontend**

```bash
cd frontend
flutter pub get && flutter gen-l10n && flutter run
```

See [`frontend/README.md`](frontend/README.md) and [`backend/README.md`](backend/README.md) for auth, OAuth, analytics, and deployment details.

## Testing

```bash
# Backend (71 tests)
cd backend && .venv/bin/python -m pytest -q

# Frontend
cd frontend && flutter gen-l10n && flutter analyze && flutter test
flutter test integration_test/related_articles_flow_test.dart
```

CI runs on push/PR when `backend/**` or `frontend/**` changes.

## Key design documents

- [`.planning/REQUIREMENTS.md`](.planning/REQUIREMENTS.md) — product requirements
- [`.planning/ROADMAP.md`](.planning/ROADMAP.md) — development phases
- [`.planning/TECHNICAL_DESIGN.md`](.planning/TECHNICAL_DESIGN.md) — backend architecture
- [`.planning/FLUTTER_DESIGN.md`](.planning/FLUTTER_DESIGN.md) — frontend architecture
- [`.planning/UI_DESIGN.md`](.planning/UI_DESIGN.md) — UI components & tokens

## License

Private / not yet licensed.
