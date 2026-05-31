# Google Play Console（Android）

## 1. 前置条件

- [ ] [Google Play Console](https://play.google.com/console) 开发者账号（一次性注册费）
- [ ] 创建应用，包名 **`com.newsflow.newsflow_frontend`**（与 `frontend/android/app/build.gradle.kts` 一致）
- [ ] Firebase 添加 Android 应用，放置 `google-services.json` 于 `frontend/android/app/`

## 2. 应用签名

Release 当前使用 debug 签名，**上架前必须**配置 upload key：

1. 生成 keystore：

```bash
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

2. 复制模板并填写：

```bash
cp frontend/android/key.properties.example frontend/android/key.properties
# 编辑 storeFile、storePassword、keyAlias、keyPassword
```

3. 在 `frontend/android/app/build.gradle.kts` 的 `release` 中引用 signing config（见模板内注释）。

4. Play App Signing：首次上传 AAB 时选择 **Google 管理应用签名**（推荐）。

## 3. 订阅商品

| 字段 | 值 |
|------|-----|
| Product ID | `newsflow_premium_monthly` |
| 类型 | 订阅 |
| 计费周期 | 每月 |

Play Console → **Monetize → Subscriptions** 创建，与后端 `PREMIUM_PRODUCT_ID` 一致。

## 4. 商店 listing

- 默认语言：English (United States)  
- 文案：[listing.en.md](./listing.en.md)  
- 隐私政策 URL：HTTPS 托管的 PRIVACY_POLICY  
- 截图：[SCREENSHOTS.md](./SCREENSHOTS.md)

## 5. 构建与内测

```bash
cd frontend
flutter build appbundle --release
# 产出: build/app/outputs/bundle/release/app-release.aab
```

- [ ] **Internal testing** 轨道上传 AAB，添加测试人员邮箱  
- [ ] 完成 **Data safety** 表单（账号、购买、推送与隐私政策对齐）  
- [ ] **Content rating** 问卷（IARC）

## 6. 生产购买验证

- [ ] Play Developer API：服务端校验 `purchaseToken`  
- [ ] 后端关闭 `ALLOW_DEV_PURCHASE_VERIFY`  
- [ ] 使用 Play 许可测试账号验证升级流程

## 7. 合规

- [ ] GDPR：应用内可导出/删除账号（`/users/me/export`、DELETE `/users/me`）  
- [ ] 仅展示 AI 摘要 + 外链，不缓存全文（与 Phase 1 版权策略一致）
