---
status: done
---

# 界面细节与启动体验 Design Delta

受影响的组件、依赖方向与流程时序由 df-arch 画在 delta-arch.md。本文件只写这次改哪里、为什么这么改、基线会怎么变。

## Context

八条落在三层：外壳（启动落点、切换保位、任务栏标识、托盘菜单）、主题（滑块轨道、标题栏按钮色）、设置扩展（只读 label）。现状是按需求逐条读出来的：

- 切换类：obox/app.py:164-209 的 switch_language 与 switch_theme 都是 clear_views() 后整窗重建，栈回到首页；设置页分类状态存在扩展进程里，宿主不重启所以分类本身没丢，丢的是窗口当前选中的视图。
- 启动落点：_on_extensions_ready（obox/app.py:266-314）只挂视图，不选中任何一项，所以停首页。
- 托盘：obox/ui/tray.py 只有 显示主窗口/设置/退出 三项，QMenu 无样式。
- 任务栏：没有 AppUserModelID，窗口图标只设在 MainWindow 上，任务栏按 python.exe 显示。
- 颜色：标题栏按钮取 provider.icon_muted/icon_active（theme/light/theme.py:14-15），与侧栏图标同一组；滑块轨道用 SURFACE_MUTED（#f7f8fa）压在 BACKGROUND（#f4f5f7）上，几乎不可见。
- 设置页：extensions/settings/views/main.oml:13-15 只按 bool/enum/string 分支渲染，readonly 被忽略。

## Scope

- 启动落点（ADDED）
- 任务栏标识（ADDED）
- 托盘常驻（MODIFIED）
- 运行中切换套件（MODIFIED）
- 设置扩展（MODIFIED）
- 自绘标题栏（MODIFIED）
- 视觉统一（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| obox/app.py | 关于分类的版本项改成 type=label；启动激活完成后 show_view 到 App 应用页；切语言与切主题前记下当前视图、重建后恢复；托盘菜单信号接线（切主题、切语言、刷新扩展、打开扩展目录）；新增 reload_extensions；run() 里设置 AppUserModelID 与应用图标；把 title_muted/title_active 下发给窗口 | 设置扩展、启动落点、运行中切换套件、托盘常驻、任务栏标识、自绘标题栏 |
| extensions/settings/views/main.oml | 条目渲染增加 label 分支，用 Text 而非 Input | 设置扩展 |
| obox/ui/tray.py | 菜单改三组：打开 obox 窗口 ‖ 切换主题/切换语言/刷新扩展/打开扩展目录 ‖ 设置/退出；主题与语言为可勾选子菜单；新增 reload_requested、open_extensions_requested、theme_requested、language_requested 信号；接受外部样式串 | 托盘常驻 |
| obox/ui/main_window.py | 新增 current_view_id()；设置标题栏按钮颜色；应用窗口共用 obox 图标 | 启动落点、自绘标题栏、任务栏标识 |
| obox/ui/title_bar.py | 按钮颜色改由外部注入，默认值换成深色；悬停底色跟随主题的 active 色 | 自绘标题栏 |
| theme/{light,dark}/theme.py | 新增 TITLE_MUTED / TITLE_ACTIVE；滑块轨道换成可辨的中性色；新增 #obox-tray-menu 及子项 QSS（白底、圆角、行高、分隔线、悬停） | 自绘标题栏、视觉统一、托盘常驻 |
| theme/{light,dark}/provider.py | 暴露 title_muted / title_active | 自绘标题栏 |
| scripts/build_exe.py、obox/assets/obox.ico | 由 obox.svg 生成 ico，编译时传 --windows-icon-from-ico | 任务栏标识 |
| scripts/verify_ui.py | 新场景：启动落在应用页、切主题/语言后仍在原分类、版本号只读、托盘菜单三组结构、滑块与标题栏截图 | 全部 |
| tests/test_tray.py、tests/test_app_switches.py、tests/test_settings_label.py | 覆盖菜单结构、切换保位、label 渲染 | 托盘常驻、运行中切换套件、设置扩展 |

## Decisions

- 托盘菜单用 QMenu + 主题 QSS，开 WA_TranslucentBackground 换圆角与细阴影；圆角在个别 Windows 版本失效时退化为直角，分组与行高不变，不减功能。
- 标题栏按钮颜色走 provider 新增的 title_muted / title_active，主题各自定值；旧 provider 缺这两个字段时回退 icon_muted / icon_active，避免第三方套件直接崩。
- 刷新扩展复用「记住视图 → 清空重建 → 恢复视图」这条与切主题相同的路径，不另写一套；完成后推一条通知。
- 启动落点用固定的视图 id app.main，找不到就停首页；不把「默认打开哪个扩展」做成配置项。
- AppUserModelID 用固定串 obox.desktop，在 QApplication 创建前设置；exe 图标由 svg 生成 ico 后交给 Nuitka，不引入图像依赖。
- label 是宿主自用条目类型，扩展配置贡献仍只接受 bool/string/enum，避免把只读项混进可写配置。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 按 delta-spec.md 的 2 条 ADDED 与 5 条 MODIFIED 合并；托盘常驻一节重写菜单描述，设置扩展一节补 label 类型 |
| design.md | 新增 D30「托盘菜单分组与主题样式」、D31「启动落点与切换保位」、D32「任务栏标识与图标来源」；D25 托盘与关闭行为一节补一句菜单入口不变 |
| docs/arch.md | 4.1 分层图里外壳行补托盘菜单与 AppUserModelID；5.x 补一条切换保位的时序说明（图由 df-arch 落） |
| README.md | 使用方式补托盘菜单项与启动默认页，安装说明补 exe 图标 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| QMenu 圆角在部分 Windows 版本失效 | 失效只影响圆角，保持分组与行高；截图比对时记录 |
| 切语言/主题重建期间托盘「刷新扩展」被点 | 重建期间禁用菜单项，或在 reload 里加运行中标记，重入直接返回 |
| 启动落点依赖 app.main 这个 id | 常量集中一处，扩展改名时提示并退回首页 |
| AppUserModelID 设置晚于 QApplication 创建会无效 | 在 run() 最前面设置，并加测试断言调用序 |
| 第三方套件没有 title_* 字段 | getattr 回退 icon 色，契约校验不强制 |
| 滑块换色后与输入框边框撞色 | 轨道用比边框更深一档的中性色，暗色同步调亮 |

回滚：八条互相独立。托盘菜单回退 tray.py 与 theme.py 的 #obox-tray-menu 段；启动落点回退 app.py 的 show_view 一行；切换保位回退两处记位代码；label 回退 app.py 的类型与 main.oml 的 o-if 分支；颜色回退 theme.py 常量与 provider 字段。
