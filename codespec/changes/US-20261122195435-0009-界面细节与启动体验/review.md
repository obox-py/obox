---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 仓库无提交历史，按文件清单统计：修改 15 个、新增 8 个（3 个测试、1 个 ico、4 个窗口图标 svg）；核心是 obox/app.py、obox/ui/{tray,title_bar,main_window,app_window}.py、两套 theme/provider、设置页 main.oml、verify_ui、build_exe |
| 对应需求 | 启动落点、任务栏标识（ADDED）；托盘常驻、运行中切换套件、设置扩展、自绘标题栏、视觉统一（MODIFIED） |
| 验证证据 | `uv run pytest -q` → 243 passed；`uv run python scripts/verify_ui.py --theme light|dark` → 0 失败；`check.py` → 0 issues；`ruff check obox tests scripts theme extensions --select F,E9` → All checks passed |

## 作者自查

- [x] 每个 `完成` 任务的验收命令都真的跑过，并有输出
- [x] `check.py` 无严重项
- [x] 变更没有超出 delta-spec 的范围
- [x] 没有把"看起来对"当成"验证过"

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | `obox/app.py` 托盘切换回调 | 切主题/语言后子菜单勾选不刷新（处理：两个回调末尾补 `_refresh_tray()`，新增 test_tray_theme_switch_refreshes_menu） | 原 `_refresh_tray` 只在 `_setup_tray` 调一次 | 接受 |
| R2 | 一般 | `obox/ui/tray.py` 子菜单 | 主题/语言子菜单没有对象名，匹配不到 QSS（处理：子菜单命名 `obox-tray-menu` 并单独设样式；复测子菜单样式长度 5054） | 实测子菜单 `objectName=''`、样式长度 0 | 接受 |
| R3 | 一般 | `theme/*/theme.py` 托盘 QSS | 菜单宽 182、行高 42，与需求 240/44 不符（处理：加 `min-width: 228px`、条目 `min-height: 24px`；复测宽 242、条目高 44） | `sizeHint()` 实测 | 接受 |
| R4 | 一般 | `obox/ui/title_bar.py` 按钮绘制 | 自绘按钮不消费 QSS，关闭红写死，dark 的 DANGER 不生效（处理：按钮本就是自绘（不调 super 是有意），但颜色改为从 provider 的 `danger` 注入，两套主题各自取值） | `paintEvent` 无 `super()`，红值 `QColor(214,48,60,235)` | 部分接受 |
| R5 | 一般 | `obox/extensions/supervisor.py:83` | `stop()` 置 `_stopping=True`，`start()` 不复位，刷新后宿主崩溃不再自动拉起（处理：待用户决策：修法是一行 `self._stopping = False`，但 supervisor.py 在「明确不动」里，扩白名单的提问两次超时未答，暂记入 validation 遗留） | supervisor.py:83、157-164 | 部分接受 |
| R6 | 一般 | `pyproject.toml` package-data | 新增的 `assets/icons/*.svg` 不会进打包产物（处理：图标平铺到 `obox/assets/`，沿用既有 `assets/*` 规则，不改打包配置） | package-data 只声明 `assets/*` | 接受 |
| R7 | 一般 | `scripts/build_exe.py` | ico 缺失时不生成、也不打日志（处理：新增 `_render_icon()` 由 svg 生成 256px ico，失败时打日志并继续） | 原逻辑只判断存在性 | 接受 |
| R8 | 一般 | `scripts/verify_ui.py` | 没有切主题保位与滑块场景，T9 无法核对（处理：新增「切主题后仍在原视图」「切回原主题」「滑块轨道样式存在」三项断言） | grep `switch_theme` 零命中 | 接受 |
| R9 | 一般 | `obox/ui/main_window.py` | `set_icon_colors` 仍顺带改标题栏按钮色，配色依赖调用顺序（处理：`set_icon_colors` 只管侧栏，标题色只走 `set_title_button_colors`） | 与 title_bar 的"解耦"注释矛盾 | 接受 |
| R10 | 一般 | `obox/ui/main_window.py:24` | `SIDEBAR_CONTAINER` 连续定义两次（处理：删掉重复行） | 复制粘贴残留 | 接受 |
| R11 | 一般 | `tests/test_app_switches.py` | 只断言视图 id，没断言设置分类保位与文案切换（处理：视图保位与英文重建已分别有断言；分类状态活在扩展进程里，主窗口侧观测不到，留给 verify_ui 的场景断言） | 原测试 | 部分接受 |
| R12 | 一般 | `tests/` | 没有 `set_enabled` 用例（处理：新增 `test_disable_keeps_window_and_quit`，并同时收窄禁用范围） | grep 零命中 | 接受 |
| R13 | 建议 | `obox/app.py` `_mount_view(rebuild=...)` | 参数从未被读取（处理：不修复：既有参数，调用方多处在传，删改属于跨模块重构，超出本次范围） | grep | 反驳 |
| R14 | 建议 | `obox/app.py` `_on_extensions_ready` | `_push_settings()` 调了两次（处理：不修复：既有顺序，删第一次可能改变扩展配置下发时机，留给后续专项） | 首次在挂载前，没有接收方 | 反驳 |
| R15 | 建议 | `obox/ui/title_bar.py` | 单行转发 `set_icon_colors` 已无调用（处理：随 R9 一并删除） | grep 零命中 | 接受 |
| R16 | 建议 | `obox/app.py` `_finish_reload` | `set_visible(True)` 是空操作且全仓唯一调用（处理：删除调用与 `TrayIcon.set_visible` 方法） | grep | 接受 |
| R17 | 建议 | `obox/app.py` 与 `scripts/verify_ui.py` | 文件超 400 行、三个函数超 40 行（处理：登记到下方「长度超阈值」，本次不拆） | `wc -l` | 部分接受 |
| R18 | 建议 | `tests/test_settings_label.py` | `pytest.raises(Exception)` 断言盲异常（处理：改为 `ComponentNotFound`） | ruff B017 | 接受 |
| R19 | 建议 | `tests/test_settings_label.py` | 验私有方法与字符串，没验可聚焦性（处理：补 `focusPolicy() == NoFocus` 断言，保留类型断言作为契约） | 原断言 | 接受 |
| R20 | 建议 | `tests/test_tray.py` | 测试标签与线上文案对不上（处理：`_refresh_tray` 按套件 mode 给「浅色/深色」，测试与线上一致） | 线上曾传 `(kit.name, kit.name)` | 接受 |
| R21 | 建议 | `theme/*/theme.py` `SLIDER_TRACK` | 轨道与底色、边框对比不足，dark 与 INPUT_BORDER 同色（处理：light 改 `#c2cad6`、dark 改 `#454b55`） | 1.29:1 / 1.05:1 / 1.00:1 | 接受 |
| R22 | 建议 | `obox/app.py` AppUserModelID | 没有调用序测试（处理：函数只在 `run()` 首行调用且非 Windows 直接返回；加调用序测试需要 mock QApplication，代价大于收益，未加） | grep 零命中 | 部分接受 |
| R23 | 建议 | `obox/ui/tray.py` `set_enabled` | 禁用范围过宽，连「打开窗口」「设置」也禁（处理：只禁用切主题、切语言、刷新、打开目录四项） | 7 项只有退出可用 | 接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `obox/app.py` | 1024 | 一直是装配中枢：消息路由、视图挂载、设置下发、托盘与关闭都在这里。拆出 TrayController 会新增一个模块与一层回调，收益低于跨模块查找成本；本次只新增约 130 行接线 |
| `obox/app.py` `_on_extensions_ready` | 55 | 一次激活回调里依次做 i18n 注册、失败提示、应用列表、视图挂载、启动落点与刷新收尾，拆开要传递 4 个中间状态 |
| `obox/app.py` `_settings_groups` | 83 | 四组设置项的静态装配，拆成四个小函数只是把相邻代码挪远 |
| `scripts/verify_ui.py` | 317 | 串行脚本，按场景顺序执行；拆文件会打断共享的 obox 实例与截图编号 |

## 回归

- R1：`uv run pytest -q tests/test_app_switches.py` → 5 passed（新增 test_tray_theme_switch_refreshes_menu）
- R2/R3：离屏实测菜单 `sizeHint=242x348`、条目高 44、子菜单样式长度 5054
- R4：`uv run pytest -q tests/test_titlebar.py` → 8 passed（颜色改由 provider.danger 注入）
- R6：`ls obox/assets` 平铺 4 个 window-*.svg，package-data 的 `assets/*` 即可覆盖
- R7：`uv run python -c "import ast,pathlib; ast.parse(pathlib.Path('scripts/build_exe.py').read_text(encoding='utf-8'))"` → 语法通过；缺 ico 分支打日志
- R8：`uv run python scripts/verify_ui.py --theme light` 与 `--theme dark` → 各 0 失败（含切主题保位与滑块样式断言）
- R9/R10/R15/R16：`uv run pytest -q` → 243 passed；ruff 无 F/E9
- R12/R18/R19/R20：`uv run pytest -q tests/test_tray.py tests/test_settings_label.py` → 13 passed
- R21：重编两套 pyd 后 verify 两套 0 失败

## 结论

- 严重：剩余 0 条
- 一般：R5 转入 validation 遗留（需用户批准扩白名单后一行修复）；R11 部分接受，分类保位由 verify_ui 场景覆盖
- 建议：R13、R14 记入 validation 遗留；R17、R22 部分接受并登记原因