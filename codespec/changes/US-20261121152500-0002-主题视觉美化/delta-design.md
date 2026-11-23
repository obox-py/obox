---
status: done
---

# 主题视觉美化 Design Delta

迭代一的设计（D27 视觉取值、两套 pyd 重建）已并入基线 design.md。本次只写浮层、卡片选中态与标题栏语言入口的设计差异。受影响的组件、依赖方向与流程时序由 df-arch 画在 delta-arch.md。

## Context

三条改动落在两处既有结构上：

- 套件侧：theme/{light,dark}/components 各 21 个组件，双向镜像实现；provider.py 只依赖 PySide6、不 import obox（theme/light/provider.py:12）。卡片选中在 card.py:22-26 用 QLabel 画对勾；浮层在 modal.py 里是一块固定 360 宽的面板，样式由 theme.py:148-159 的 #obox-modal-* 规则提供。
- 外壳侧：MainWindow 持有 TitleBar，语言按钮在 title_bar.py:110-114，菜单在 main_window.py:304-315；关闭询问是独立的 CloseDialog（close_dialog.py），由 app.py:840-843 用 exec() 阻塞取结果，内联 QSS 把圆角写成 10，与主题 2px 不一致。

基线 design.md 的 D27 只覆盖配色、圆角与字体，没有浮层结构与关闭语义；D25 说明询问框是自绘 QDialog，但没规定它必须复用主题面板。

## Scope

- 浮层（ADDED）：容器化面板、尺寸初值与拖拽、三种关闭来源、变体、系统询问框复用同一面板
- 选择容器与卡片（MODIFIED）：去掉对勾，选中只用底色与描边
- i18n 注册与占位替换（MODIFIED）：语言入口从标题栏移到设置页
- 视觉统一（MODIFIED）：圆角与边框口径收敛到 2px / 1px

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| theme/{light,dark}/components/card.py | 删掉 QLabel 对勾与 set_selected 里的显隐逻辑，选中态只保留 ACCENT_SOFT 底 + ACCENT 描边 | 选择容器与卡片 |
| theme/{light,dark}/components/modal.py | 面板拆成标题区、正文容器、按钮区；正文容器作为 container_layout 接受子组件；面板直接子级的 Button 进按钮区（按声明顺序回传 value），其余子节点进正文容器；读 width/height 初值、min 320×160、max 宿主窗口 90%；右下角 16×16 热区拖拽改尺寸；Esc 与遮罩关闭按 close_on_esc / close_on_overlay 判断；variant 取 info/confirm/danger 换图标与主按钮色；无子组件时退回标题+正文+"知道了" | 浮层 |
| theme/{light,dark}/components/modal.py（宿主尺寸） | 装 Resize 事件过滤器，宿主改尺寸时重设覆盖层几何，取代只在 set_visible 时重设一次 | 浮层 |
| theme/{light,dark}/theme.py | 补遮罩、按钮区、变体图标与缩放柄的 QSS；#obox-modal-card 圆角 2px、1px 描边、无阴影 | 浮层、视觉统一 |
| obox/ui/close_dialog.py | 改成无边框 + 半透明遮罩的 QDialog，尺寸对齐父窗口，内嵌名为 obox-modal-card 的面板与 obox-modal-title / obox-modal-body 文案位；保留"记住我的选择"与三按钮；Esc 等同取消 | 浮层 |
| obox/ui/title_bar.py | 删语言按钮、language_requested 信号、set_language_label 与布局占位 | i18n 注册与占位替换 |
| obox/ui/main_window.py | 删 set_languages、_open_language_menu、_choose_language 与 _languages / _language_callback 字段 | i18n 注册与占位替换 |
| obox/app.py | 删 _language_choices 与 _sync_languages 的两处调用；switch_language 保留并继续写配置 | i18n 注册与占位替换 |
| extensions/demo/views/main.oml、extensions/gallery/views/main.oml | 浮层示例改为容器写法（正文子组件 + 自定义按钮），保留一处旧写法做兼容示例 | 浮层 |
| scripts/verify_ui.py | 语言场景改为从设置页切换；浮层截图补缩放与变体 | 浮层、i18n 注册与占位替换 |
| .agents/skills/obox-theme-dev、obox-ui-test | 同步 modal 契约（容器、尺寸、关闭语义）与截图编号 | 浮层、视觉统一 |

## Decisions

- 两套套件各写一份浮层实现：不新增共享包，不破 theme/light/provider.py:12 的"只依赖 PySide6"约定；代价是两份实现要同步，用契约校验脚本与双套件截图兜底。
- 关闭询问框保留 QDialog.exec()：app.py:840-843 的阻塞流程与 decide_close 不动，只把造型改成无边框遮罩 + 主题对象名面板；QSS 靠父窗口继承，所以构造必须传主窗口作 parent。
- 变体图标用字形 badge（i、!、×）而不是矢量图：与 alert.py:64-71 同一手法，不引入图标资源与重染管线。
- 缩放只做右下角 16×16 热区：命中区单一，光标只在 SizeFDiagCursor 与箭头之间切换；max 取宿主矩形 90%，不用系统屏幕尺寸。
- 关闭语义收在面板内：上抛 close 事件带 reason（button/esc/overlay）与按钮文本，宿主不替扩展判断关闭原因；按钮区最后一个按钮随 variant 染主色。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| design.md | D27 扩为「参考图视觉规范与浮层」：补 2px 圆角、1px 描边、无阴影的浮层口径与 variant；新增 D28「浮层容器化与关闭语义」（正文容器、0..N 按钮、尺寸与拖拽、Esc/遮罩、旧写法兼容）；新增 D29「系统询问框复用主题面板」（exec 语义不变，造型与主题同源） |
| docs/arch.md | 4.1 分层与模块架构图的套件组件行补浮层容器与缩放柄；5.x 或 8.x 补一句询问框走主题面板；组件图里 modal 从叶子节点变为容器节点（由 df-arch 落图） |
| spec.md | 本次不改，差异在 delta-spec.md 里；合并时按它的 ADDED/MODIFIED 落地 |
| README.md | 组件能力表若列了 modal 的写法，补容器与按钮一段；其余不动 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| light 与 dark 两份浮层实现走样 | 契约校验脚本跑两套 provider；verify_ui 双主题截图对比 |
| 宿主改尺寸后覆盖层仍按旧几何摆放 | 装 Resize 事件过滤器，照 alert.py:22-32 的先例；缩放时同步 clamp |
| Esc 收不到（焦点在输入框或被宿主抢走） | 覆盖层设 StrongFocus 并在显示时抢焦点，keyPressEvent 在覆盖层统一处理 |
| QDialog 拿不到主题 QSS（parent 传空或提前销毁） | 构造必须传主窗口 parent；缺样式时退回内联兜底样式 |
| 删除 set_languages 影响外部脚本 | 全仓 grep 调用点，tests 与 verify_ui 已确认只用 app.switch_language |
| 旧 Modal 片段渲染异常 | 无子组件分支走旧布局，demo 里保留一处旧写法作为回归样本 |

回退：三条互相独立，可分别回退——卡片只回退 card.py 的选中分支；浮层回退 modal.py 与 close_dialog.py 到 v1 实现；标题栏回退 title_bar.py + main_window.py + app.py 三处。
