---
status: done
---

# Tasks

## 拆分方式

按可验证增量：每个任务都有一条能单独跑的 pytest 或截图判据；app.py 被多条任务涉及，所以它们按依赖串行，tray.py 与主题文件与 app.py 不重叠，可以并行起。

## 全局约束

- 不改扩展配置贡献的类型集合（仍 bool / string / enum），label 只给宿主自用条目
- 托盘旧三项信号保留兼容，只新增信号
- 主题包仍只依赖 PySide6，不 import obox
- 不引入第三方依赖；ico 由现有 Qt 从 svg 生成
- 启动落点的视图 id 只在一处定义

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 版本号改只读 label | 主 Agent | obox/app.py、extensions/settings/views/main.oml、tests/test_settings_label.py | 设置扩展 | - | 版本项渲染为不可编辑文本，test_settings_label 全绿 | 完成 |
| T2 | 切语言/主题保位 | 主 Agent | obox/app.py、obox/ui/main_window.py、tests/test_app_switches.py | 运行中切换套件 | T1 | 切换后仍停在原视图与原分类，测试全绿 | 完成 |
| T3 | 启动落点应用页 | 主 Agent | obox/app.py | 启动落点 | T2 | 激活完成后 show_view(app.main)，缺失回首页，测试覆盖两种 | 完成 |
| T4 | 任务栏标识与应用图标 | 主 Agent | obox/app.py、obox/ui/app_window.py、scripts/build_exe.py、obox/assets/obox.ico | 任务栏标识 | T3 | AppUserModelID 在 QApplication 前设置，窗口与应用图标为 obox，exe 编译带 ico | 完成 |
| T5 | 托盘菜单结构与信号 | 主 Agent | obox/ui/tray.py、tests/test_tray.py | 托盘常驻 | - | 三组七项、主题/语言子菜单可勾选、四个新信号，test_tray 全绿 | 完成 |
| T6 | 托盘接线与刷新扩展 | 主 Agent | obox/app.py | 托盘常驻 | T4,T5 | 刷新走重建保位并通知，打开目录用系统文件管理器，菜单样式随主题 | 完成 |
| T7 | 主题样式与标题色常量 | 主 Agent | theme/{light,dark}/theme.py、theme/{light,dark}/provider.py | 视觉统一、自绘标题栏、托盘常驻 | - | 滑块轨道可辨、#obox-tray-menu 规则生效、provider 暴露 title_* | 完成 |
| T8 | 标题栏按钮配色注入 | 主 Agent | obox/ui/title_bar.py、obox/ui/main_window.py、obox/app.py | 自绘标题栏 | T6,T7 | 两套主题下三按钮对比度足够，悬停与关闭红底保留 | 完成 |
| T9 | verify 场景与截图 | 主 Agent | scripts/verify_ui.py | 全部 | T8 | 新场景全过，两套主题 0 失败，截图编号连续 | 完成 |
| T10 | 重编 pyd 与全量验证 | 后台 | .theme、tests、scripts/verify_ui.py | 全部 | T9 | pytest 全绿，verify light/dark 0 失败，pyd 时间戳为本次 | 完成 |

## 任务详情

### T1 版本号改只读 label

- 步骤：
  1. app.py 的关于分类把版本项 type 改成 label，去掉 readonly 字段
  2. 设置页 main.oml 增加 o-if="item.type == 'label'" 的 Text 分支，展示 value
  3. 新增 tests/test_settings_label.py：断言版本项 type 为 label、设置页装配后该项是文本不是输入框
- 验收命令：`uv run pytest -q tests/test_settings_label.py tests/test_settings_filter.py`（期望：全绿）
- 自检：label 项不可聚焦、不含输入控件；扩展配置仍只有三种类型

### T2 切语言/主题保位

- 步骤：
  1. MainWindow 增 current_view_id()，返回当前栈里的视图 id，首页返回空串
  2. switch_language 与 switch_theme 重建前记下视图 id，重建后 show_view 回去
  3. 新增 tests/test_app_switches.py：切语言后当前视图不变，切主题后同样
- 验收命令：`uv run pytest -q tests/test_app_switches.py tests/test_i18n_switch.py`（期望：全绿）
- 自检：重建失败时仍保留原视图与主题；设置页分类由扩展状态维持，不需要额外恢复

### T3 启动落点应用页

- 步骤：
  1. _on_extensions_ready 末尾按固定 id 调 show_view，找不到就保持首页
  2. 在 T2 的测试文件补两条：有 app.main 时打开应用页；没有时停在首页
- 验收命令：`uv run pytest -q tests/test_app_switches.py`（期望：全绿）
- 自检：落点 id 只有一处常量；启动不因落点失败报错

### T4 任务栏标识与应用图标

- 步骤：
  1. run() 在 QApplication 创建前调用 AppUserModelID（ctypes，Windows 才调）
  2. QApplication 与应用窗口都设 obox 图标
  3. 由 obox.svg 生成 obox/assets/obox.ico；build_exe.py 传 --windows-icon-from-ico，缺 ico 时先生成
- 验收命令：`uv run pytest -q tests/test_titlebar.py` 与 `uv run python -c "from PySide6.QtGui import QIcon; icon=QIcon('obox/assets/obox.ico'); print(sorted((s.width() for s in icon.availableSizes())))"`（期望：测试全绿，ico 可加载且含 256 尺寸）
- 自检：非 Windows 平台跳过 AppUserModelID；ico 缺失时构建仍能继续，且构建日志里写明退化为无图标

### T5 托盘菜单结构与信号

- 步骤：
  1. tray.py 建三组菜单与分隔线，主题/语言用可勾选子菜单
  2. 新增 reload_requested、open_extensions_requested、theme_requested、language_requested，保留旧三项信号
  3. 暴露 apply_stylesheet(qss) 与 set_checked 系列方法刷新勾选
  4. 新增 tests/test_tray.py：组结构、条目文案、子菜单勾选、信号发射
- 验收命令：`uv run pytest -q tests/test_tray.py`（期望：全绿）
- 自检：无托盘环境时 TrayIcon.available() 仍为假，测试跳过

### T6 托盘接线与刷新扩展

- 步骤：
  1. app.py 接四个新信号：切主题、切语言、刷新扩展、打开扩展目录
  2. reload_extensions = 记视图 → clear_views → supervisor.restart() → 恢复视图 → 通知
  3. 重建期间设置重入标记，阻止并发刷新
  4. 托盘样式随 _apply_provider 更新
- 验收命令：`uv run pytest -q tests/test_app_switches.py tests/test_tray.py`（期望：全绿）
- 自检：刷新后视图与选中项不变；打开目录用 QDesktopServices，不阻塞

### T7 主题样式与标题色常量

- 步骤：
  1. 两套 theme.py 增 TITLE_MUTED / TITLE_ACTIVE，滑块轨道换可辨中性色
  2. 增 #obox-tray-menu 及条目的 QSS：白底、圆角、行高、分隔线、悬停
  3. 两套 provider.py 暴露 title_muted / title_active
- 验收命令：`uv run pytest -q tests/test_theme_kits.py tests/test_component_protocol.py`（期望：全绿）
- 自检：暗色套件的轨道在深底上同样可辨；QSS 选择器不与既有规则冲突

### T8 标题栏按钮配色注入

- 步骤：
  1. title_bar.py 按钮颜色由外部注入，默认值改深色
  2. MainWindow.set_title_button_colors 与 app._apply_provider 接线，provider 缺字段时回退 icon 色
  3. 截图对比 light/dark 三按钮
- 验收命令：`uv run pytest -q tests/test_titlebar.py`（期望：全绿）
- 自检：关闭按钮悬停仍是红底白线；最大化与还原图标清晰

### T9 verify 场景与截图

- 步骤：
  1. 新场景：启动落在应用页、切主题后仍在原分类、版本号只读、托盘菜单结构（无托盘时跳过）、滑块与标题栏截图
  2. 更新截图编号并清掉旧编号引用
- 验收命令：`uv run python scripts/verify_ui.py --theme light` 与 `--theme dark`（期望：0 失败）
- 自检：截图编号连续；托盘相关检查在无托盘环境被跳过而不是失败

### T10 重编 pyd 与全量验证

- 步骤：
  1. 关闭正在运行的 obox，重编两套主题
  2. 跑全量 pytest 与两套 verify
- 验收命令：`uv run python scripts/build_theme.py light dark && uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：全绿，verify 0 失败）
- 自检：pyd 时间戳为本次；.theme 里的样式包含新 QSS

## 测试策略

TDD：每任务先写失败测试再实现，验收命令含对应 pytest；测试只写在公开行为上（设置项渲染、视图保位、托盘菜单结构），期望值取自 delta-spec 的场景。

## 执行顺序

1. T1 ∥ T5 ∥ T7
2. T2
3. T3
4. T4
5. T6
6. T8
7. T9
8. T10

## 覆盖检查

- 设置扩展：T1
- 运行中切换套件：T2
- 启动落点：T3
- 任务栏标识：T4
- 托盘常驻：T5、T6、T7
- 自绘标题栏：T7、T8
- 视觉统一：T7

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，且同文件任务没有并行
- [x] 方式只取 主 Agent / subagent / 后台
- [x] 模板占位与注释已全部替换