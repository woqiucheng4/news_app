# NewsFlow UI 组件库设计文档

**版本：** v1.0
**日期：** 2026-05-27
**状态：** Draft

---

## 1. 设计原则

| 原则 | 说明 |
|---|---|
| **极简克制** | Notion/Linear 风格，去除一切不必要装饰 |
| **内容优先** | 标题和摘要占据视觉重心，操作按钮弱化 |
| **一致性** | 统一间距、圆角、阴影、动效 |
| **可访问性** | 对比度 ≥ 4.5:1，最小触控区域 44×44 |
| **跨平台一致** | iOS/Android/Web 同一套视觉规范 |

---

## 2. 设计令牌 (Design Tokens)

### 2.1 色彩系统

基于 Material 3 `ColorScheme.fromSeed`，种子色 `#1A73E8`（Google Blue）。

#### 亮色主题

| Token | 值 | 用途 |
|---|---|---|
| `primary` | `#1A73E8` | 主按钮、链接、强调色 |
| `onPrimary` | `#FFFFFF` | 主色上的文字 |
| `primaryContainer` | `#D3E3FD` | Tag 背景、选中态 |
| `onPrimaryContainer` | `#041E49` | 容器上的文字 |
| `surface` | `#FFFFFF` | 卡片、弹窗背景 |
| `onSurface` | `#1F1F1F` | 正文文字 |
| `onSurfaceVariant` | `#44474F` | 次要文字（来源、时间） |
| `outline` | `#74777F` | 边框、分割线 |
| `outlineVariant` | `#C4C6D0` | 轻量分割线 |
| `surfaceContainerLow` | `#F7F8FA` | 页面背景 |
| `surfaceContainerHighest` | `#ECECEE` | 骨架屏背景 |
| `error` | `#BA1A1A` | 错误状态 |

#### 暗色主题

| Token | 值 | 用途 |
|---|---|---|
| `primary` | `#A8C7FA` | 主按钮、链接 |
| `onPrimary` | `#062E6F` | 主色上的文字 |
| `primaryContainer` | `#0842A0` | Tag 背景、选中态 |
| `surface` | `#121212` | 卡片背景 |
| `onSurface` | `#E3E2E6` | 正文文字 |
| `onSurfaceVariant` | `#C4C6D0` | 次要文字 |
| `surfaceContainerLow` | `#1B1B1F` | 页面背景 |
| `surfaceContainerHighest` | `#36343B` | 骨架屏背景 |

#### 语义色

| Token | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `success` | `#1B8D3A` | `#4DD86B` | 成功状态 |
| `warning` | `#E8A317` | `#FFD666` | 警告状态 |
| `info` | `#1A73E8` | `#A8C7FA` | 信息提示 |

---

### 2.2 排版系统

基于 Material 3 Typography，使用系统默认字体（SF Pro / Roboto）。

| Token | 大小 | 行高 | 字重 | 用途 |
|---|---|---|---|---|
| `displayLarge` | 32sp | 40sp | w700 | 页面大标题（极少用） |
| `headlineLarge` | 24sp | 32sp | w700 | 文章详情标题 |
| `headlineMedium` | 20sp | 28sp | w600 | 页面标题 |
| `headlineSmall` | 18sp | 26sp | w600 | 卡片标题 |
| `titleMedium` | 16sp | 24sp | w600 | 卡片标题（主要） |
| `titleSmall` | 14sp | 20sp | w600 | 子标题、Section header |
| `bodyLarge` | 16sp | 24sp | w400 | 正文（详情页） |
| `bodyMedium` | 14sp | 20sp | w400 | 摘要文字、卡片正文 |
| `bodySmall` | 12sp | 16sp | w400 | 来源、时间、标签 |
| `labelLarge` | 14sp | 20sp | w500 | 按钮文字 |
| `labelMedium` | 12sp | 16sp | w500 | Chip、Badge |
| `labelSmall` | 11sp | 14sp | w400 | 辅助标注 |

---

### 2.3 间距系统

基于 4px 网格，使用命名常量。

| Token | 值 | 用途 |
|---|---|---|
| `spaceXxs` | 2px | 极小间隔 |
| `spaceXs` | 4px | 图标与文字间距 |
| `spaceS` | 8px | 紧凑元素间距 |
| `spaceM` | 12px | 卡片内元素间距 |
| `spaceL` | 16px | 卡片内边距、页面边距 |
| `spaceXL` | 24px | 区块间距 |
| `spaceXXL` | 32px | 页面顶部间距 |
| `spaceXXXL` | 48px | 大区块分隔 |

---

### 2.4 圆角系统

| Token | 值 | 用途 |
|---|---|---|
| `radiusXs` | 4px | 标签、小按钮 |
| `radiusS` | 8px | 输入框、Chip |
| `radiusM` | 12px | 卡片、对话框 |
| `radiusL` | 16px | 底部弹窗 |
| `radiusXL` | 24px | 全屏弹窗 |
| `radiusFull` | 999px | 圆形头像、圆形按钮 |

---

### 2.5 阴影系统

基于 Material 3 Elevation。

| Token | Elevation | 用途 |
|---|---|---|
| `elevationNone` | 0dp | 默认卡片（平面设计） |
| `elevationLow` | 1dp | 悬浮按钮 |
| `elevationMedium` | 3dp | 弹窗、底部导航 |
| `elevationHigh` | 6dp | 对话框 |

> NewsFlow 设计以平面为主，默认卡片无阴影，使用边框或背景色区分层级。

---

### 2.6 动效系统

| Token | 时长 | 曲线 | 用途 |
|---|---|---|---|
| `durationFast` | 150ms | `easeOut` | 按钮反馈、颜色切换 |
| `durationNormal` | 250ms | `easeInOut` | 页面转场、展开收起 |
| `durationSlow` | 350ms | `easeInOut` | 模态弹窗 |
| `durationPage` | 300ms | `FastOutSlowIn` | 页面导航转场 |

---

## 3. 基础组件

### 3.1 AppButton

```dart
enum AppButtonType { filled, outlined, text, tonal }

class AppButton extends StatelessWidget {
  final String label;
  final IconData? icon;
  final AppButtonType type;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isExpanded;

  // 用法
  // AppButton(label: 'Sign In', type: AppButtonType.filled, onPressed: () {})
  // AppButton(label: 'Cancel', type: AppButtonType.outlined, onPressed: () {})
  // AppButton(label: 'Loading...', isLoading: true)
}
```

| 类型 | 样式 | 场景 |
|---|---|---|
| `filled` | 实心主色 | 主操作（登录、提交） |
| `outlined` | 边框无填充 | 次要操作（取消、返回） |
| `text` | 无边框无填充 | 文字链接 |
| `tonal` | 浅色填充 | 中等优先级操作 |

---

### 3.2 AppTextField

```dart
class AppTextField extends StatelessWidget {
  final String? label;
  final String? hint;
  final String? errorText;
  final IconData? prefixIcon;
  final IconData? suffixIcon;
  final bool obscureText;
  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;

  // 用法
  // AppTextField(label: 'Email', hint: 'you@example.com', prefixIcon: Icons.email)
  // AppTextField(label: 'Password', obscureText: true, prefixIcon: Icons.lock)
}
```

---

### 3.3 AppChip

```dart
enum AppChipType { filter, action, suggestion }

class AppChip extends StatelessWidget {
  final String label;
  final AppChipType type;
  final bool isSelected;
  final VoidCallback? onTap;
  final IconData? icon;

  // 用法
  // AppChip(label: 'Tech', type: AppChipType.filter, isSelected: true, onTap: () {})
  // AppChip(label: '+ Add', type: AppChipType.action, onTap: () {})
}
```

---

### 3.4 AppCard

```dart
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;
  final Color? backgroundColor;
  final bool hasBorder;

  // 用法
  // AppCard(onTap: () {}, child: Column(...))
}
```

**默认样式：**
- 圆角：12px
- 内边距：16px
- 背景：`surface`
- 无阴影，1px `outlineVariant` 边框（暗色主题下）

---

### 3.5 AppAvatar

```dart
class AppAvatar extends StatelessWidget {
  final String? imageUrl;
  final String? initials;
  final double size;
  final Color? backgroundColor;

  // 用法
  // AppAvatar(imageUrl: 'https://...', size: 40)
  // AppAvatar(initials: 'JD', size: 32)
}
```

---

### 3.6 AppBadge

```dart
class AppBadge extends StatelessWidget {
  final int count;
  final bool showZero;
  final Color? color;

  // 用法
  // AppBadge(count: 3)  // 显示红色圆点 + 数字
  // AppBadge(count: 0, showZero: false)  // 不显示
}
```

---

### 3.7 AppDivider

```dart
class AppDivider extends StatelessWidget {
  final double? height;
  final bool isIndented;

  // 用法
  // AppDivider()  // 标准分割线
  // AppDivider(isIndented: true)  // 带缩进（用于列表项之间）
}
```

---

## 4. 复合组件

### 4.1 ArticleCard（信息流卡片）

信息流的核心组件，占据大部分视觉空间。

```
┌─────────────────────────────────────────┐
│ [icon] TechCrunch · 2h ago       [···] │  ← 来源行 (bodySmall, onSurfaceVariant)
│                                         │
│ Apple 发布新 iPhone 17                  │  ← 标题 (titleMedium, onSurface, w600)
│                                         │
│ Apple 今日发布了新一代 iPhone 17，       │  ← 摘要 (bodyMedium, onSurfaceVariant)
│ 搭载 A19 芯片，性能提升 30%...           │     maxLines: 3, overflow: ellipsis
│                                         │
│ ──────────────────────────────────────  │  ← 分割线 (outlineVariant)
│ [🔖 3]                     [↗️] [🔗]   │  ← 操作行 (iconButton, bodySmall)
└─────────────────────────────────────────┘
```

```dart
class ArticleCard extends ConsumerWidget {
  final Article article;
  final VoidCallback? onTap;
  final bool isCompact; // 紧凑模式（搜索结果）

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SourceRow(source: article.source, publishedAt: article.publishedAt),
          const SizedBox(height: spaceM),
          _Title(title: article.title),
          if (!isCompact && article.summary != null) ...[
            const SizedBox(height: spaceS),
            _Summary(text: article.summary!),
          ],
          const SizedBox(height: spaceM),
          AppDivider(isIndented: true),
          const SizedBox(height: spaceS),
          _ActionBar(article: article),
        ],
      ),
    );
  }
}
```

**变体：**

| 变体 | 用途 | 差异 |
|---|---|---|
| 默认 | 信息流 | 完整布局：来源 + 标题 + 摘要 + 操作 |
| 紧凑 | 搜索结果 | 仅标题 + 来源行，无摘要 |
| 事件卡片 | 事件聚类 | 额外显示关联文章数 |

---

### 4.2 ArticleDetailHeader（文章详情头部）

```
┌─────────────────────────────────────────┐
│                                         │
│ Apple 发布新 iPhone 17                  │  ← headlineLarge
│                                         │
│ [icon] TechCrunch · 2026-05-27          │  ← bodyMedium, onSurfaceVariant
│                                         │
│ [AI] [Apple] [iPhone]                   │  ← Tags: AppChip, primaryContainer
│                                         │
└─────────────────────────────────────────┘
```

---

### 4.3 SummaryBlock（AI 摘要块）

```
┌─────────────────────────────────────────┐
│ 🤖 AI 摘要                      [复制] │  ← labelMedium, primary
│                                         │
│ Apple 今日发布了新一代 iPhone 17，      │  ← bodyLarge, onSurface
│ 搭载 A19 芯片，性能提升 30%。           │
│ 新增卫星通信功能，售价 $999 起。        │
│                                         │
│ gpt-4o-mini · 2026-05-27 10:00         │  ← labelSmall, onSurfaceVariant
└─────────────────────────────────────────┘
```

```dart
class SummaryBlock extends StatelessWidget {
  final String summary;
  final String? model;
  final DateTime? generatedAt;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(spaceL),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
        borderRadius: BorderRadius.circular(radiusM),
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withOpacity(0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _Header(model: model),
          const SizedBox(height: spaceM),
          Text(summary, style: Theme.of(context).textTheme.bodyLarge),
          if (generatedAt != null) ...[
            const SizedBox(height: spaceS),
            _Footer(model: model, generatedAt: generatedAt!),
          ],
        ],
      ),
    );
  }
}
```

---

### 4.4 TopicCard（话题卡片）

```
┌─────────────────────────────────────────┐
│ [icon]  Artificial Intelligence         │  ← titleSmall
│         1.2K subscribers                │  ← bodySmall, onSurfaceVariant
│                                         │
│                     [订阅] / [已订阅]   │  ← AppButton (outlined/filled)
└─────────────────────────────────────────┘
```

---

### 4.5 NotificationItem（通知项）

```
┌─────────────────────────────────────────┐
│ ● 🔔 AI 领域重大更新                    │  ← 未读: dot + titleSmall
│   NVIDIA 发布新一代 AI 芯片...           │  ← bodyMedium, onSurfaceVariant
│   3 小时前                              │  ← labelSmall, onSurfaceVariant
└─────────────────────────────────────────┘
```

### 4.5.1 NotificationChannelTile（通知渠道选项）

```
┌─────────────────────────────────────────┐
│ [📱] FCM Push                           │  ← leading icon + titleSmall
│      即时推送到设备                      │  ← bodySmall, onSurfaceVariant
│                              [● 选中]   │  ← trailing radio
├─────────────────────────────────────────┤
│ [📧] Email                              │
│      发送到注册邮箱                      │
│                              [○]        │
├─────────────────────────────────────────┤
│ [✈️] Telegram                           │
│      通过 Telegram Bot 推送              │
│                              [○]        │
└─────────────────────────────────────────┘
```

### 4.5.2 QuietHoursCard（免打扰时段卡片）

```
┌─────────────────────────────────────────┐
│ 🌙 免打扰时段                   [🔘]   │  ← titleMedium + Switch
│                                         │
│ 开始    22:00                           │  ← TimePicker tap
│ 结束    08:00                           │
│ 时区    America/New_York (自动)         │  ← labelSmall
└─────────────────────────────────────────┘
```

### 4.5.3 RelevanceScoreSlider（推送价值滑块）

```
┌─────────────────────────────────────────┐
│ 最低推送价值                            │  ← titleSmall
│                                         │
│ ──────────●──────────  6.0             │  ← Slider (1-10)
│                                         │
│ 只推送 ≥ 6 分的新闻                     │  ← bodySmall, onSurfaceVariant
│ 1-4: 低价值  5-6: 一般  7-8: 重要  9+: 重大 │  ← labelSmall, outline
└─────────────────────────────────────────┘
```

---

### 4.6 CategoryChipBar（分类导航栏）

```
[全部] [科技] [财经] [娱乐] [体育] [+]
 ← 横向滚动，选中态用 primaryContainer 填充
```

```dart
class CategoryChipBar extends StatelessWidget {
  final List<String> categories;
  final String selected;
  final ValueChanged<String> onSelected;
  final VoidCallback? onAdd;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: spaceL),
        itemCount: categories.length + (onAdd != null ? 1 : 0),
        separatorBuilder: (_, __) => const SizedBox(width: spaceS),
        itemBuilder: (context, index) {
          if (index == categories.length) {
            return AppChip(
              label: '+',
              type: AppChipType.action,
              onTap: onAdd,
            );
          }
          return AppChip(
            label: categories[index],
            type: AppChipType.filter,
            isSelected: categories[index] == selected,
            onTap: () => onSelected(categories[index]),
          );
        },
      ),
    );
  }
}
```

---

### 4.7 FeedSkeleton（骨架屏）

```dart
class FeedSkeleton extends StatelessWidget {
  final int itemCount;

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Theme.of(context).colorScheme.surfaceContainerHighest,
      highlightColor: Theme.of(context).colorScheme.surface,
      child: ListView.builder(
        itemCount: itemCount,
        padding: const EdgeInsets.symmetric(vertical: spaceS),
        itemBuilder: (_, __) => const _ArticleCardSkeleton(),
      ),
    );
  }
}

class _ArticleCardSkeleton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 来源行占位
          Row(children: [
            _Box(width: 20, height: 20, radius: 4),
            const SizedBox(width: spaceS),
            _Box(width: 80, height: 12, radius: 4),
          ]),
          const SizedBox(height: spaceM),
          // 标题占位
          _Box(width: double.infinity, height: 16, radius: 4),
          const SizedBox(height: spaceS),
          _Box(width: 200, height: 16, radius: 4),
          const SizedBox(height: spaceM),
          // 摘要占位
          _Box(width: double.infinity, height: 12, radius: 4),
          const SizedBox(height: spaceS),
          _Box(width: 250, height: 12, radius: 4),
        ],
      ),
    );
  }
}
```

---

### 4.8 EmptyView / ErrorView

```dart
class EmptyView extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? description;
  final String? actionLabel;
  final VoidCallback? onAction;

  // EmptyView(
  //   icon: Icons.article_outlined,
  //   title: 'No articles yet',
  //   description: 'Subscribe to topics to see articles here',
  //   actionLabel: 'Browse Topics',
  //   onAction: () => context.go('/discover'),
  // )
}

class ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  // ErrorView(
  //   message: 'Failed to load articles',
  //   onRetry: () => ref.invalidate(feedNotifierProvider),
  // )
}
```

---

### 4.9 SearchBar

```
┌─────────────────────────────────────────┐
│ 🔍  Search articles...          [Cancel]│  ← 圆角输入框，primaryContainer 背景
└─────────────────────────────────────────┘
```

```dart
class AppSearchBar extends StatelessWidget {
  final TextEditingController? controller;
  final String? hint;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onCancel;
  final bool autofocus;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 44,
      padding: const EdgeInsets.symmetric(horizontal: spaceM),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(radiusS),
      ),
      child: Row(
        children: [
          Icon(Icons.search, size: 20, color: Theme.of(context).colorScheme.onSurfaceVariant),
          const SizedBox(width: spaceS),
          Expanded(
            child: TextField(
              controller: controller,
              autofocus: autofocus,
              decoration: InputDecoration(
                hintText: hint ?? 'Search articles...',
                border: InputBorder.none,
                isDense: true,
              ),
              onChanged: onChanged,
              onSubmitted: onSubmitted,
            ),
          ),
          if (onCancel != null)
            TextButton(
              onPressed: onCancel,
              child: Text('Cancel'),
            ),
        ],
      ),
    );
  }
}
```

---

### 4.10 ArticleTimeline（新闻时间线）

参考 BettaFish 的时间线展示方式，按时间轴展示事件发展脉络。

```
┌─────────────────────────────────────────┐
│                                         │
│ ── 今天 ─────────────────────── 3 条 ── │
│                                         │
│  10:00  ●── Apple 发布新 iPhone 17     │  ← 最新节点，primary 色圆点
│         │   搭载 A19 芯片...            │
│         │                               │
│  08:30  ●── 供应链消息：富士康增产      │  ← 普通节点
│         │   为满足 iPhone 17 首批...     │
│         │                               │
│ ── 昨天 ─────────────────────── 2 条 ── │
│         │                               │
│  22:00  ●── 分析师预测 iPhone 17 售价   │
│         │   $999 起...                  │
│         │                               │
│  15:00  ●── Apple 确认秋季发布会日期    │
│             ...                         │
│                                         │
└─────────────────────────────────────────┘
```

```dart
class ArticleTimeline extends StatelessWidget {
  final List<TimelineGroup> groups; // 按日期分组的文章

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: groups.length,
      itemBuilder: (context, groupIndex) {
        final group = groups[groupIndex];
        return _TimelineDayGroup(group: group);
      },
    );
  }
}

class _TimelineDayGroup extends StatelessWidget {
  final TimelineGroup group;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 日期标题
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: spaceL, vertical: spaceS),
          child: Row(
            children: [
              Text(group.label, style: Theme.of(context).textTheme.titleSmall),
              const Spacer(),
              Text('${group.articles.length} 条',
                  style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
        // 时间线节点
        ...group.articles.asMap().entries.map((entry) {
          final isLast = entry.key == group.articles.length - 1;
          return _TimelineNode(
            article: entry.value,
            isFirst: entry.key == 0,
            isLast: isLast,
          );
        }),
      ],
    );
  }
}

class _TimelineNode extends StatelessWidget {
  final Article article;
  final bool isFirst;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 时间标签
          SizedBox(
            width: 56,
            child: Text(
              DateFormat('HH:mm').format(article.publishedAt),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.right,
            ),
          ),
          const SizedBox(width: spaceM),
          // 时间轴线 + 圆点
          Column(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isFirst ? colorScheme.primary : colorScheme.outlineVariant,
                ),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    color: colorScheme.outlineVariant,
                  ),
                ),
            ],
          ),
          const SizedBox(width: spaceM),
          // 文章卡片
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: spaceL),
              child: ArticleCard(article: article, isCompact: true),
            ),
          ),
        ],
      ),
    );
  }
}

@freezed
sealed class TimelineGroup with _$TimelineGroup {
  const factory TimelineGroup({
    required String label,        // "今天"、"昨天"、"5月25日"
    required DateTime date,
    required List<Article> articles,
  }) = _TimelineGroup;
}
```

### 4.11 BottomSheet 系列

```dart
class AppBottomSheet {
  // 确认弹窗
  static Future<bool> confirm(
    BuildContext context, {
    required String title,
    required String message,
    String confirmLabel = 'Confirm',
    String cancelLabel = 'Cancel',
    bool isDestructive = false,
  }) async { ... }

  // 选择弹窗
  static Future<T?> select<T>(
    BuildContext context, {
    required String title,
    required List<BottomSheetOption<T>> options,
  }) async { ... }

  // 分享弹窗
  static Future<void> share(
    BuildContext context, {
    required String title,
    required String url,
  }) async { ... }
}
```

---

## 5. 布局组件

### 5.1 MainScaffold（主框架）

```dart
class MainScaffold extends StatelessWidget {
  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) =>
            navigationShell.goBranch(index, initialLocation: index == navigationShell.currentIndex),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Feed'),
          NavigationDestination(icon: Icon(Icons.explore_outlined), selectedIcon: Icon(Icons.explore), label: 'Discover'),
          NavigationDestination(icon: Icon(Icons.bookmark_outline), selectedIcon: Icon(Icons.bookmark), label: 'Bookmarks'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
```

---

### 5.2 PageScaffold（子页面框架）

```dart
class PageScaffold extends StatelessWidget {
  final String? title;
  final Widget? leading;
  final List<Widget>? actions;
  final Widget body;
  final bool showBackButton;
  final Widget? floatingActionButton;
  final Widget? bottomSheet;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: title != null
          ? AppBar(
              title: Text(title!),
              leading: leading,
              actions: actions,
              automaticallyImplyLeading: showBackButton,
            )
          : null,
      body: body,
      floatingActionButton: floatingActionButton,
      bottomSheet: bottomSheet,
    );
  }
}
```

---

### 5.3 PaginatedList（分页列表）

```dart
class PaginatedList<T> extends StatelessWidget {
  final List<T> items;
  final Widget Function(BuildContext, T) itemBuilder;
  final VoidCallback? onLoadMore;
  final Future<void> Function()? onRefresh;
  final bool isLoading;
  final bool hasNext;
  final Widget? emptyView;
  final Widget? header;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh ?? () async {},
      child: ListView.builder(
        itemCount: items.length + (hasNext ? 1 : 0) + (header != null ? 1 : 0),
        itemBuilder: (context, index) {
          if (header != null && index == 0) return header;
          final itemIndex = header != null ? index - 1 : index;
          if (itemIndex >= items.length) {
            onLoadMore?.call();
            return const Center(child: CircularProgressIndicator());
          }
          return itemBuilder(context, items[itemIndex]);
        },
      ),
    );
  }
}
```

---

## 6. 动效规范

### 6.1 页面转场

```dart
// go_router 默认使用 Material 转场
// 自定义：从右侧滑入
CustomTransitionPage(
  child: ArticleDetailPage(articleId: id),
  transitionsBuilder: (context, animation, secondaryAnimation, child) {
    return SlideTransition(
      position: Tween<Offset>(
        begin: const Offset(1.0, 0.0),
        end: Offset.zero,
      ).animate(CurvedAnimation(
        parent: animation,
        curve: Curves.fastOutSlowIn,
      )),
      child: child,
    );
  },
)
```

### 6.2 列表项入场

```dart
// 列表项淡入 + 上移
AnimatedBuilder(
  animation: animation,
  builder: (context, child) {
    return FadeTransition(
      opacity: Tween<double>(begin: 0.0, end: 1.0).animate(
        CurvedAnimation(parent: animation, curve: Curves.easeOut),
      ),
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0.0, 0.1),
          end: Offset.zero,
        ).animate(animation),
        child: child,
      ),
    );
  },
  child: ArticleCard(article: article),
)
```

### 6.3 交互反馈

| 交互 | 动效 | 时长 |
|---|---|---|
| 按钮点击 | `InkWell` ripple | 系统默认 |
| 收藏切换 | 图标缩放 + 颜色变化 | 150ms |
| 下拉刷新 | `RefreshIndicator` | 系统默认 |
| 加载更多 | 底部 `CircularProgressIndicator` | - |
| 切换 Tab | `NavigationBar` indicator 动画 | 250ms |

---

## 7. 响应式设计

### 7.1 断点

| 断点 | 宽度 | 布局 |
|---|---|---|
| 手机 | < 600px | 单列，底部导航 |
| 平板 | 600-840px | 单列，侧边导航 |
| 桌面 | > 840px | 双列（列表 + 详情），侧边导航 |

### 7.2 适配策略

```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 840) {
          return desktop ?? tablet ?? mobile;
        }
        if (constraints.maxWidth >= 600) {
          return tablet ?? mobile;
        }
        return mobile;
      },
    );
  }
}

// 桌面端：左侧列表 + 右侧详情
ResponsiveLayout(
  mobile: FeedPage(),
  desktop: Row(
    children: [
      SizedBox(width: 400, child: FeedPage()),
      Expanded(child: ArticleDetailPage(articleId: selectedId)),
    ],
  ),
)
```

---

## 8. 图标系统

使用 Material Icons 为主，自定义图标为辅。

| 用途 | 图标 | 备选 |
|---|---|---|
| 首页 | `Icons.home_outlined` / `Icons.home` | - |
| 发现 | `Icons.explore_outlined` / `Icons.explore` | - |
| 收藏 | `Icons.bookmark_outline` / `Icons.bookmark` | - |
| 个人 | `Icons.person_outline` / `Icons.person` | - |
| 搜索 | `Icons.search` | - |
| 通知 | `Icons.notifications_outlined` | - |
| 设置 | `Icons.settings_outlined` | - |
| 分享 | `Icons.share_outlined` | `Icons.ios_share` |
| 外链 | `Icons.open_in_new` | - |
| 返回 | `Icons.arrow_back_ios` | - |
| 更多 | `Icons.more_horiz` | - |
| AI 摘要 | `Icons.auto_awesome` | - |
| 订阅 | `Icons.add_circle_outline` | - |
| 已订阅 | `Icons.check_circle` | - |

---

## 9. 文件结构

```
lib/core/theme/
├── app_theme.dart           # ThemeData 定义（亮/暗）
├── color_scheme.dart        # 语义色扩展
├── text_styles.dart         # 文字样式扩展
├── spacing.dart             # 间距常量
├── radius.dart              # 圆角常量
├── duration.dart            # 动效时长常量
└── elevation.dart           # 阴影常量

lib/shared/widgets/
├── app_button.dart
├── app_text_field.dart
├── app_chip.dart
├── app_card.dart
├── app_avatar.dart
├── app_badge.dart
├── app_divider.dart
├── app_search_bar.dart
├── app_bottom_sheet.dart
├── loading_indicator.dart
├── error_view.dart
├── empty_view.dart
├── shimmer_card.dart
├── cached_image.dart
└── responsive_layout.dart

lib/features/*/presentation/widgets/
├── article_card.dart           # 信息流卡片
├── article_list.dart           # 信息流列表
├── article_timeline.dart       # 新闻时间线视图
├── summary_block.dart          # AI 摘要块
├── topic_card.dart             # 话题卡片
├── notification_item.dart      # 通知项
├── notification_channel_tile.dart  # 通知渠道选项
├── quiet_hours_card.dart       # 免打扰时段卡片
├── relevance_score_slider.dart # 推送价值滑块
├── category_chip_bar.dart      # 分类导航
├── feed_skeleton.dart          # 信息流骨架屏
└── detail_skeleton.dart        # 详情页骨架屏
```

---

## 10. 设计规范速查

### 间距速查

```
组件内元素间距:     8-12px  (spaceS - spaceM)
卡片内边距:         16px    (spaceL)
卡片之间间距:       8-12px  (spaceS - spaceM, 在 ListView.separated)
页面水平边距:       16px    (spaceL)
区块之间间距:       24px    (spaceXL)
```

### 文字速查

```
页面标题:     headlineMedium (20sp, w600)
卡片标题:     titleMedium (16sp, w600)
卡片摘要:     bodyMedium (14sp, w400)
来源/时间:    bodySmall (12sp, w400)
按钮文字:     labelLarge (14sp, w500)
标签文字:     labelMedium (12sp, w500)
```

### 触控区域

```
最小触控区域: 44 × 44 px
IconButton:   48 × 48 px
Chip:         高度 32px
按钮高度:     44px (filled/outlined), 40px (text)
```

### 时间线速查

```
时间轴线宽:        2px, outlineVariant 色
圆点直径:          12px
最新节点圆点:      primary 色
普通节点圆点:      outlineVariant 色
时间标签宽度:      56px
节点间距:          spaceL (16px)
日期分隔:          spaceM (12px) 上下间距
```

---

*文档版本：v1.0*
*最后更新：2026-05-27*
