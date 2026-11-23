---
status: done
---

# 组件归位与区域语言 Design Delta

受影响的组件、依赖方向与流程时序由 df-arch 画在 delta-arch.md。本文件只写这次改哪里、为什么这么改、基线会怎么变。

## Context

现在 21 个组件在 theme/{light,dark}/components 各一份，直接 import 主题常量绘制；装配器从 provider.component_types 取组件类（obox/ui/builder.py:102），契约校验要求 provider 覆盖 REQUIRED_TAGS（obox/ui/component_protocol.py:88）。i18n 只有 zh-CN 兜底，设置语言项写死 zh-CN / en-US 两个选项。

本次要把组件搬到 obox 单份实现、主题只剩样式；新增 chart；语言改按地区并全量列出。

## Scope

- 图表组件（ADDED）
- 区域语言与缺省回退（ADDED）
- 界面套件清单与加载、组件契约不变、组件能力接口与消息处理分界、主题色板与文字层级、i18n 注册与占位替换、设置扩展（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/ui/palette.py`（新） | 定义 Palette（颜色、圆角、控件高度、字体族）与全局活动调色板；app 在应用主题时设置 | 主题色板与文字层级 |
| `obox/ui/components/`（新，从主题迁入） | 21 个组件的唯一实现；绘制颜色改为从 palette 取；删除对主题包的 import | 组件契约不变、组件能力接口与消息处理分界 |
| `obox/ui/components/chart.py`（新） | chart 组件：matplotlib QtAgg 画布、data/title 状态、缩放/平移/悬停/重置 | 图表组件 |
| `obox/ui/components/__init__.py`（新） | 宿主组件表 COMPONENT_TYPES（21 + chart） | 组件契约不变 |
| `obox/ui/component_protocol.py` | REQUIRED_TAGS 改为宿主组件表校验；provider 校验改为样式能力（stylesheet、palette、font_dir、icon 色、spacing） | 界面套件清单与加载 |
| `obox/ui/builder.py` | 组件表来源改为宿主组件表（或由 app 注入），签名不改 | 组件契约不变 |
| `obox/app.py` | 应用主题时设置调色板；装配用宿主组件表；语言项改为 Qt 全量地区；语言回退走 i18n 注册表 | 主题色板与文字层级、设置扩展、区域语言与缺省回退 |
| `theme/light/provider.py`、`theme/dark/provider.py` | 去掉 component_types；新增 palette 属性；保留 stylesheet、font_dir、icon 两色、spacing、title 两色、danger | 界面套件清单与加载、主题色板与文字层级 |
| `theme/light/theme.py`、`theme/dark/theme.py` | 只保留颜色常量与 PALETTE；QSS 移到 styles.qss | 主题色板与文字层级 |
| `theme/light/styles.qss`、`theme/dark/styles.qss`（新） | QSS 源文件，键名用双花括号包裹，provider 加载时替换 | 界面套件清单与加载 |
| `theme/_build/light.py`、`dark.py` | 只打包样式、调色板与字体，不再包含组件模块 | 界面套件清单与加载 |
| `obox/i18n.py` | 解析改为精确 → 语言基码 → zh-CN；注册校验必须含 zh-CN | 区域语言与缺省回退、i18n 注册与占位替换 |
| `pyproject.toml` | 运行时依赖加 matplotlib | 图表组件 |
| `tests/test_components.py` 等 | 适配宿主组件表与调色板；新增 chart 与 i18n 回退测试 | 全部 |
| `.agents/skills/obox-theme-dev`、`obox-ext-dev`、`obox-ui-test` | 主题只写样式与调色板；组件归属、标签计数 21+1、语言示例同步 | 全部 |

## Decisions

- QSS 以 styles.qss 文件交付：provider 读取文件并把 双花括号包裹的键名 换成 PALETTE 取值，构建把文件复制到 .theme/<kit>/；样式可直接编辑，不藏在 pyd 字符串里。
- 调色板走模块级「活动调色板」：app 在 _apply_provider 里 set_active(provider.palette)，组件用 `palette()` 取色。理由是组件构造签名不扩散，切换主题只换一次全局值；代价是同一进程内只能有一套活动主题。
- 主题包彻底不含组件：provider 不再有 component_types，REQUIRED_TAGS 改为校验宿主组件表；主题厂商只能通过 QSS 与调色板影响外观。
- 组件表由 obox 模块提供，app 注入 Builder；Builder 的签名不变，只换数据来源。
- chart 用 matplotlib 的 FigureCanvasQTAgg 嵌入 QWidget；canvas 工具栏关闭，交互自己实现（滚轮缩放、拖动平移、悬停坐标、重置按钮）。
- 图表数据只传 JSON：扩展设置 data 状态为字典或 JSON 字符串，obox 解析后重绘；宿主进程不引入 matplotlib。
- 语言列表用 QLocale.matchingLocales 枚举，显示 nativeTerritoryName；重名时补地区代码以区分。
- 语言回退按语言基码，之后才是 zh-CN；注册缺 zh-CN 直接拒绝。
- 调色板字段：背景、面板、弱背景、文字、辅助文字、分隔线、主色、强调淡底、强调文字、卡片面、卡片边框、危险、成功、警告、输入边框、占位符、圆角控件、圆角卡片、控件高度、字体族。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 按 delta-spec.md 的 2 条 ADDED 与 5 条 MODIFIED 合并 |
| design.md | 新增 D38「组件归宿主、主题只样式」、D39「调色板注入」、D40「matplotlib 图表组件」、D41「区域语言与回退」；D12 主题套件一节改写 |
| docs/arch.md | 分层图里 theme 行变为样式包、obox/ui 增加 components 目录；组件装配的依赖方向更新（图由 df-arch 落） |
| README.md | 能力清单补图表与地区语言，目录结构里主题包说明改样式包 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 21 个组件迁移引入行为差异 | 逐组件对照旧实现；用现有组件测试与两套 verify 截图做回归 |
| 全局调色板的时序问题（组件先于主题创建） | app 在装配前设置调色板；palette() 在未设置时返回默认亮色并记一次日志 |
| 主题 pyd 里残留组件模块 | 构建脚本只包含 styles 与 palette；重编后检查 pyd 体积与导入 |
| matplotlib 体积与打包 | 进运行时依赖；打包脚本包含 matplotlib 数据；缺失时 chart 显示「未安装」而不是崩溃 |
| 全量地区列表让设置项很长 | Select 下拉可搜索；列表项用原生名 + 地区代码去重 |
| 回退链改变既有文案 | 单测覆盖 zh-HK、en-GB、zh-TW、未知语言四条路径 |

回滚：恢复主题包的 components 目录与 provider.component_types，装配器改回从 provider 取；palette 模块保留但不再使用；chart 与 i18n 可独立回退。