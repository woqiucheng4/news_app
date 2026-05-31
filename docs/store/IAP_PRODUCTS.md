# In-App Purchase 商品配置

## 统一 Product ID

```
newsflow_premium_monthly
```

| 系统 | 配置位置 |
|------|----------|
| Backend | `PREMIUM_PRODUCT_ID` in `.env` |
| Flutter | 从 `GET /billing/entitlements` 的 `premium_product_id` 动态加载 |
| App Store Connect | Auto-Renewable Subscription |
| Google Play Console | Subscription |

## 权益（与 05-01 freemium 一致）

| 层级 | 话题订阅 | 每日文章阅读 | 深度分析 | 推送 |
|------|----------|--------------|----------|------|
| Free | ≤ `FREE_MAX_TOPIC_SUBSCRIPTIONS` (5) | ≤ `FREE_DAILY_ARTICLE_VIEWS` (20) | 否 | 标准 |
| Premium | 无限 | 无限 | 是 | 优先 |

## 本地开发

```env
ALLOW_DEV_PURCHASE_VERIFY=true
DEBUG=true
```

Flutter 升级页可使用 **Dev activate premium**（仅 DEBUG）。

## 生产清单

- [ ] 两店商品 ID 均为 `newsflow_premium_monthly`
- [ ] 价格档位在后台设定（建议先低价内测）
- [ ] `ALLOW_DEV_PURCHASE_VERIFY=false`
- [ ] 真实收据校验已上线（当前生产可能 501，提审前必须完成）
