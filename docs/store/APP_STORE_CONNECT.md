# App Store Connect（iOS）

## 1. 前置条件

- [ ] [Apple Developer Program](https://developer.apple.com/programs/) 已付费激活
- [ ] 在 Certificates, Identifiers & Profiles 创建 App ID：`com.newsflow.newsflowFrontend`
- [ ] 启用 Capabilities：**Push Notifications**、**Sign in with Apple**（若使用）
- [ ] Firebase 项目已添加 iOS 应用，下载 `GoogleService-Info.plist` 到 `frontend/ios/Runner/`

## 2. App Store Connect 应用记录

1. **My Apps** → **+** → New App  
2. Platform: iOS  
3. Name: `NewsFlow`  
4. Primary Language: English (U.S.)  
5. Bundle ID: 选择 `com.newsflow.newsflowFrontend`  
6. SKU: `newsflow-ios-001`（任意唯一字符串）

## 3. 订阅（Auto-Renewable Subscription）

与后端 `PREMIUM_PRODUCT_ID` 一致：

| 字段 | 值 |
|------|-----|
| Product ID | `newsflow_premium_monthly` |
| Reference Name | NewsFlow Premium Monthly |
| Subscription Group | `newsflow_premium` |
| Duration | 1 month |

在 App Store Connect → 该 App → **Subscriptions** 中创建上述商品，状态需为 **Ready to Submit** 后再随 App 版本提审。

## 4. 商店元数据

文案见 [listing.en.md](./listing.en.md)。必填项：

- [ ] 副标题（Subtitle，≤ 30 字符）
- [ ] 描述（Description）
- [ ] 关键词（Keywords，≤ 100 字符）
- [ ] 支持 URL：`https://newsflow.app`（替换为你的官网）
- [ ] 隐私政策 URL：托管 [PRIVACY_POLICY.md](../PRIVACY_POLICY.md) 后的 HTTPS 地址
- [ ] 截图：见 [SCREENSHOTS.md](./SCREENSHOTS.md)

## 5. 构建与 TestFlight

```bash
cd frontend
flutter build ipa --release
# 或使用 ios/ExportOptions.plist.example 配置后:
# xcodebuild -exportArchive ...
```

- [ ] Xcode → **Product → Archive** → Distribute → App Store Connect  
- [ ] TestFlight 内部测试 ≥ 1 轮（登录、Feed、订阅、升级页、推送）  
- [ ] 填写 **App Privacy** 问卷（与隐私政策一致：账号、订阅状态、分析可选）

## 6. 审核注意（Guideline 4.2）

- 强调 **AI 摘要 + 话题订阅**，非空壳 RSS 阅读器  
- 付费功能需在审核备注中提供 **Sandbox 测试账号** 或说明免费层可用路径  
- 深度分析为 Premium；确保未订阅用户仍可浏览有限 Feed

## 7. 生产 IAP 验证

当前生产环境 `POST /billing/verify-purchase` 对真实收据可能返回 501，提审前需：

- [ ] 实现 App Store Server API / StoreKit 2 服务端校验  
- [ ] `ALLOW_DEV_PURCHASE_VERIFY=false`

## 8. 推送

- [ ] Firebase APNs Auth Key (.p8) 上传到 Firebase Console  
- [ ] Xcode Capabilities 中 Push Notifications 已开启
