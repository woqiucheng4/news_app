# NewsFlow — App Store / Google Play 上架配置

Phase 1 UAT 签收后再执行本目录步骤。代码侧 IAP、隐私政策、Freemium 已就绪；以下为 **商店后台与发布构建** 配置清单。

## 应用标识（提交前请统一）

| 平台 | 当前工程值 | 建议 |
|------|------------|------|
| iOS Bundle ID | `com.newsflow.newsflowFrontend` | 在 Apple Developer 创建同名 App ID |
| Android applicationId | `com.newsflow.newsflow_frontend` | Play Console 包名需一致；可与 iOS 不同，但建议长期统一为 `com.newsflow.app` |

> 若更改 Bundle ID / applicationId，需同步 Apple Developer、Play Console、Firebase、`google-services.json`、APNs。

## 文档索引

| 文件 | 用途 |
|------|------|
| [APP_STORE_CONNECT.md](./APP_STORE_CONNECT.md) | iOS 账号、IAP、TestFlight、提审 |
| [GOOGLE_PLAY_CONSOLE.md](./GOOGLE_PLAY_CONSOLE.md) | Android 签名、订阅、内测轨道 |
| [listing.en.md](./listing.en.md) | 商店文案（英文，可复制到后台） |
| [listing.zh-CN.md](./listing.zh-CN.md) | 商店文案（简体中文备选） |
| [IAP_PRODUCTS.md](./IAP_PRODUCTS.md) | 订阅 SKU 与后端环境变量 |
| [SCREENSHOTS.md](./SCREENSHOTS.md) | 截图尺寸与必拍画面 |
| [../PRIVACY_POLICY.md](../PRIVACY_POLICY.md) | 隐私政策（上架必填 URL） |

## 工程模板

| 文件 | 用途 |
|------|------|
| `frontend/android/key.properties.example` | Release 签名配置模板 |
| `frontend/ios/ExportOptions.plist.example` | `flutter build ipa` 导出选项 |

## 发布前环境（生产）

```env
ALLOW_DEV_PURCHASE_VERIFY=false
DEBUG=false
ENVIRONMENT=production
PREMIUM_PRODUCT_ID=newsflow_premium_monthly
```

## 建议顺序

1. 完成 [Phase 1 UAT](../../.planning/phases/01-foundation-ingestion/01-UAT.md)（`./scripts/verify_phase1_uat.sh`）
2. 部署后端生产 API + 配置 `NEWSFLOW_API_BASE_URL`（Flutter）
3. Apple / Google 开发者账号 + 创建应用
4. 配置订阅商品 `newsflow_premium_monthly`（见 IAP_PRODUCTS.md）
5. 上传截图与商店文案
6. TestFlight / Play 内部测试 → 正式提审

## 关联 checklist

- [05-03-LAUNCH_CHECKLIST.md](../../.planning/phases/05-freemium/05-03-LAUNCH_CHECKLIST.md)
- [03-03-SMOKE_CHECKLIST.md](../../.planning/phases/03-flutter-mobile/03-03-SMOKE_CHECKLIST.md)
