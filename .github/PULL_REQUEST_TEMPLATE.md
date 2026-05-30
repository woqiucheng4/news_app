<!--
NewsFlow Pull Request Template

Keep PRs small and focused. If this PR touches multiple areas, consider splitting it.
-->

## Summary

<!-- 1-3 句话说明这次改动的目的与范围 -->

## Scope

- [ ] Backend (`backend/**`)
- [ ] Frontend (`frontend/**`)
- [ ] Planning / Docs (`.planning/**`, `*.md`)
- [ ] Infra (`docker-compose.yml`, `Makefile`, `.github/**`)

## Linked Requirements / Plans

<!-- 列出涉及的需求 ID（USER-XX / CONT-XX / AI-XX 等）和 phase plan（如 02-02） -->

- Requirements:
- Phase plan:

## Changes

<!-- 简明列出关键改动点 -->

-

## Verification

- [ ] `pytest -q tests/test_user_subscription_api.py tests/test_api_endpoints.py` 通过
- [ ] `pytest -q` 全量通过（如改动较大）
- [ ] 涉及 seed 脚本时已 `python -m py_compile scripts/<file>.py`
- [ ] 涉及 docker compose / Makefile 时手工跑过 `make demo-up` 或同等命令
- [ ] Flutter 改动：本地 `flutter analyze` + `flutter test` 通过

## Subscription / Feed Surface Checklist

> 仅在改动 `subscriptions` / `articles/feed` / `users/me` 等接口时勾选，
> 用于保持 02-02 文档链路同步。

- [ ] 已更新 `.planning/phases/02-user-subscription/02-02-API_CONTRACT.md`
- [ ] 已更新 `.planning/phases/02-user-subscription/02-02-VALIDATION.md`
- [ ] 字段命名前后端一致（snake_case ↔ Freezed `@JsonKey`）
- [ ] 不破坏现有 `x-user-id` 测试兜底（除非显式声明 breaking）
- [ ] 鉴权依赖统一走 `get_current_user_id`

## Risk & Rollback

<!-- 主要风险点 + 回滚方式（如 `git revert <sha>` / 关闭某 feature flag） -->

-

## Screenshots / Logs (Optional)

<!-- UI 改动可附图；后端可附关键日志/curl 验证 -->
