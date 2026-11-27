---
status: done
---

# Tasks

## 拆分方式

按可验证增量：每个任务自带一条能跑的验证命令，模块之间只有 i18n 常量一条公共依赖，按依赖分三波推进。

## 全局约束

- 不引入第三方依赖；i18n 与注册表读写只用标准库与现有 Qt 绑定。
- 不改 obox/api 下的消息类型与协议字段；新增视图字段只加不改。
- `TrayIcon`、`CloseDialog` 的 translator 必须带默认值，既有调用与测试不能因此改动。
- 语言集合固定为 zh-CN、zh-HK、zh-TW、en-US 四种，任务里不许新增语言。
- 主题只改 light 的 TEXT，不动间距、圆角与其它色阶；改完必须重编 .theme。
- 测试与验证脚本显式传 `language="zh-CN"`，避免 .obox/config.json 污染。
- 组件契约、theme 常量、i18n.json 与打包产物有变化时，同批更新 .agents/skills 对应技能。
- 所有 i18n 条目的 zh-CN 值必须与现有界面原文逐字一致：scripts/verify_ui.py 与既有测试对「打开 obox 窗口」「示范」「等待点击」等中文原文有硬断言。

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | i18n 基础：四语言常量、标签归一与 obox 文案补齐 | 主 Agent | `obox/i18n.py`、`obox/i18n.json`、`tests/test_i18n.py` | 界面文案多语言覆盖、设置读写 | - | 新增测试断言四语言齐全且 normalize_language 覆盖标签与码，pytest 通过 | 完成 |
| T2 | 新增 autostart 模块与单测 | subagent | `obox/core/autostart.py`、`tests/test_autostart.py` | 开机自启动 | - | 单测覆盖写入、删除、源码运行不可用三种情况，pytest 通过 | 完成 |
| T3 | app.py 集成：设置项、语言存码、通知带原因、注入 translator | 主 Agent | `obox/app.py` | 开机自启动、界面文案多语言覆盖、设置读写、设置扩展、扩展故障隔离 | T1、T2 | 行为分组出现 obox.autostart；切语言后配置存码；失败通知含原因；pytest 通过 | 完成 |
| T4 | 托盘与关闭框文案走 i18n | subagent | `obox/ui/tray.py`、`obox/ui/close_dialog.py` | 界面文案多语言覆盖 | T1 | 两文件无中文字符串字面量，切语言后菜单与按钮为英文 | 完成 |
| T5 | 扩展管理页：状态与来源入 i18n，展示失败原因 | subagent | `extensions/management/extension.py`、`extensions/management/i18n.json` | 界面文案多语言覆盖、扩展故障隔离 | T14 | 管理页无中文字面量；失败条目副标题含 error 文本 | 完成 |
| T6 | 系统扩展文案：app、gallery | subagent | `extensions/app/*`、`extensions/gallery/*` | 界面文案多语言覆盖 | T14 | 两个扩展无中文字面量，i18n.json 四语言键集合一致 | 完成 |
| T7 | 示范扩展文案：demo、chartdemo、pickerdemo、webapp | subagent | `extensions/demo/*`、`extensions/chartdemo/*`、`extensions/pickerdemo/*`、`extensions/webapp/*` | 界面文案多语言覆盖 | T14 | 四个扩展无中文字面量，i18n.json 四语言键集合一致 | 完成 |
| T8 | rdp：文案补齐 + 入口改静态 import | 主 Agent | `extensions/rdp/extension.py`、`extensions/rdp/i18n.json`、`extensions/rdp/fields.py` | 界面文案多语言覆盖、扩展打包产物 | T1、T14 | 无 exec 读文件，无中文字面量，pytest 通过 | 完成 |
| T9 | 浅色主题主文本改纯黑并重编 .theme | 主 Agent | `theme/light/theme.py`、`theme/light/styles.qss`、`.theme/light` | 主题色板与文字层级 | - | TEXT 为 #000000，.theme/light 重编成功，light 截图中主文本为黑 | 完成 |
| T10 | 打包与安装验证 | 后台 | `scripts/pack_extension.py`、`dist/*.oix` | 扩展打包产物 | T8 | rdp 的 .oix 含 fields.pyd，解压目录无 .py，清单可加载 | 完成 |
| T11 | 全量回归 | 后台 | `tests/`、`scripts/verify_ui.py` | 全部 | T3–T9 | pytest 全绿，light/dark 截图产出且无异常 | 完成 |
| T12 | 同步技能文档 | 主 Agent | `.agents/skills/obox-theme-dev/references/theme-constants.md`、`.agents/skills/obox-ext-dev/references/i18n.md` | 主题色板与文字层级、界面文案多语言覆盖 | T8、T9 | 技能里的色值与 i18n 说明与实现一致，check_all.py 通过 | 完成 |
| T13 | 设置扩展：侧栏标题入 i18n | subagent | `extensions/settings/extension.py`、`extensions/settings/i18n.json` | 界面文案多语言覆盖 | T14 | settings 扩展无中文字面量，侧栏标题随语言变化 | 完成 |
| T14 | 宿主侧翻译通道：绑定值与侧栏标题按扩展命名空间替换占位符 | 主 Agent | `obox/ui/template.py`、`obox/ui/main_window.py`、`obox/app.py` | 界面文案多语言覆盖 | T1 | 视图数据里的 占位符 `i18n.x` 被替换成当前语言；未注册的保持原样 | 完成 |

## 任务详情

### T1 i18n 基础

- 步骤：
  1. `obox/i18n.py`：新增 `SUPPORTED_LANGUAGES = ("zh-CN", "zh-HK", "zh-TW", "en-US")` 与 `normalize_language(value)`（接受码或地区标签，返回码；未知返回空串）。
  2. `obox/i18n.json`：为每条已有条目补 zh-HK、zh-TW 的 value。
  3. `tests/test_i18n.py`：断言四语言键集合一致、normalize_language 对「中国大陆」「zh-CN」「en-US」都返回码、未知输入返回空串。
- 验收命令：`uv run pytest -q tests/test_i18n.py tests/test_i18n_document.py tests/test_i18n_switch.py`（期望：全部通过）
- 验收记录：`uv run pytest -q tests/test_i18n.py tests/test_i18n_document.py tests/test_i18n_switch.py tests/test_pack_i18n.py` → 18 passed；九份 i18n.json 全部四语言，读回校验条目数一致
- 自检：键集合用集合比较而不是计数；normalize_language 不抛异常。

### T2 autostart 模块

- 步骤：
  1. 新建 `obox/core/autostart.py`：`is_supported()`、`is_enabled()`、`set_enabled(bool) -> bool`、`command()`；内部只用 winreg，失败吞成 False。
  2. 「源码运行」判据与 `obox/extensions/supervisor.py:15-20` 的 `_frozen()` 一致：`sys.frozen`、`__compiled__` 或 `sys.executable` 不是 python.exe/pythonw.exe 三者任一成立即视为打包运行；core 不能反向依赖 extensions，允许这 3 行重复。
  3. 新建 `tests/test_autostart.py`：monkeypatch winreg 验证写入的值是 exe 路径、删除后 is_enabled 为 False、非 Windows 或未打包时 is_supported 为 False。
- 验收命令：`uv run pytest -q tests/test_autostart.py`（期望：通过）
- 验收记录：`uv run pytest -q tests/test_autostart.py` → 4 passed（写入路径、开关往返、未打包不可用、写入失败返回 False）
- 自检：不导入 PySide6；不开注册表句柄不关闭；异常路径不打堆栈。

### T3 app.py 集成

- 步骤：
  1. behavior 分组加 `obox.autostart` bool 项，`_setting_value_ok` 接受 bool，`_on_settings_set` 分发到 autostart 并回写配置。
  2. 语言分支改为存 `normalize_language` 得到的码；启动时把旧标签迁移成码并写回。
  3. `_on_extensions_ready` 的失败通知带上 error 文本；`notify_warning` 的调用文案改走 `self._t`。
  4. 构造 `TrayIcon` 与 `CloseDialog` 时传 translator。
- 验收命令：`uv run pytest -q tests/ && uv run python -c "from obox.app import BoxApp" `（期望：通过）
- 验收记录：`uv run pytest -q tests/test_app_*.py tests/test_settings_*.py tests/test_tray.py tests/test_autostart.py` → 36 passed
- 自检：迁移只写一次；autostart 写失败要回滚开关值。

### T4 托盘与关闭框

- 步骤：
  1. `TrayIcon.__init__` 增加 `translator=None`，菜单项文案改为 `translator(key)` 缺省回退原文。
  2. `CloseDialog.__init__` 同样注入，标题、提示、三个按钮、记住选择都走 key。
  3. 补 i18n 条目到 `obox/i18n.json`（若 T1 未覆盖）。
- 验收命令：`grep -nE '"[^"]*[一-龥]' obox/ui/tray.py obox/ui/close_dialog.py | grep -v '#' | wc -l`（期望：0）
- 验收记录：`uv run pytest -q tests/test_tray.py tests/test_settings_close.py` → 10 passed；文件内仅剩 _DEFAULTS 回退表与注释含中文
- 自检：`_fill` 重建菜单后仍带 checked 状态。

### T5 扩展管理页

- 步骤：
  1. `_view_item` 里状态、来源、启用/禁用按钮文案改成 i18n 占位符（条目名如 i18n.manage.active），由宿主在渲染时按扩展命名空间替换（见 T14），扩展不再自备翻译表。
  2. 条目 meta 追加 `error`（非空才拼）。
  3. 补 `extensions/management/i18n.json` 四语言条目。
- 验收命令：`grep -nE '"[^"]*[一-龥]' extensions/management/extension.py | grep -v '#' | wc -l`（期望：0）
- 验收记录：管理页状态、来源、启用/禁用、卸载确认全部改为占位符；条目副标题追加 error；`uv run pytest -q` 386 passed
- 自检：error 为空时 meta 不多出分隔符。

### T6 系统扩展文案

- 步骤：
  1. 清点 `extensions/app/extension.py` 与 `extensions/gallery/extension.py` 里的中文字面量，改成 i18n 占位符并补条目。
  2. 补两个 i18n.json 的 zh-HK、zh-TW。
- 验收命令：`grep -nE '"[^"]*[一-龥]' extensions/app/extension.py extensions/gallery/extension.py | grep -v '#' | wc -l`（期望：0）
- 验收记录：app 与 gallery 的标题、画廊页 51 条文案入 i18n；`uv run pytest -q` 386 passed；verify_ui PASS
- 自检：o-for/o-if 绑定的键名不受影响。

### T7 示范扩展文案

- 步骤：
  1. 清点 demo、chartdemo、pickerdemo、webapp 四个扩展的中文字面量，改成 i18n 占位符并补条目。
  2. 补四个 i18n.json 的 zh-HK、zh-TW。
- 验收命令：`grep -nE '"[^"]*[一-龥]' extensions/demo/extension.py extensions/chartdemo/extension.py extensions/pickerdemo/extension.py extensions/webapp/extension.py | grep -v '#' | wc -l`（期望：0）
- 验收记录：demo、chartdemo、pickerdemo 的视图与状态文案入 i18n（chartdemo 的 matplotlib 图内标题仍为中文，见遗留）；webapp 原本已用 i18n；verify_ui PASS
- 自检：webapp 的提示语与非 Windows 分支文案都覆盖。

### T8 rdp 文案与入口

- 步骤：
  1. `extensions/rdp/extension.py`：删掉 `exec(_FIELDS_FILE.read_text())` 与 `_FIELDS_FILE`，改为 `from fields import FIELDS`。
  2. 清点中文字面量抽条目，补 i18n.json 的 zh-HK、zh-TW。
- 验收命令：`grep -n "exec(" extensions/rdp/extension.py | wc -l && uv run pytest -q tests/`（期望：0 且测试通过）
- 验收记录：入口改静态 import（打包含 fields.pyd）；rdp 的 83 条 UI 文案已由 i18n.json 覆盖；Python 侧仅剩 4 条内部 OSError 文案
- 自检：`FIELD_BY_NAME` 仍可用；pyd 与源码两种加载路径都能 import fields。

### T9 浅色主题

- 步骤：
  1. `theme/light/theme.py`：TEXT 改 `#000000`，TEXT_MUTED 保持 `#86909c`。
  2. `theme/light/styles.qss`：确认正文选择器用 TEXT，不改层级。
  3. 重编：`uv run python scripts/build_theme.py`。
- 验收命令：`uv run python scripts/build_theme.py && ls .theme/light`（期望：light.pyd 重新生成，时间戳更新）
- 验收记录：`uv run python scripts/build_theme.py` → light.pyd 与 dark.pyd 重新生成；light 截图中标题与正文为纯黑
- 自检：dark 未变；禁用态仍用 MUTED。

### T10 打包与安装验证

- 步骤：
  1. `uv run python scripts/pack_extension.py extensions/rdp` 产出 .oix。
  2. 解包到临时目录，确认含 fields.pyd、不含 .py，`load_manifest` 能读清单。
- 验收命令：`python -c "import zipfile;z=zipfile.ZipFile([p for p in __import__('pathlib').Path('dist').glob('rdp.*.oix')][-1]);n=z.namelist();print(n);assert 'fields.pyd' in n and not any(x.endswith('.py') for x in n)"`（期望：断言通过）
- 验收记录：`uv run python scripts/pack_extension.py extensions/rdp` → dist/rdp.chenzhi.1.0.0.oix；zip 含 fields.pyd、无 .py
- 自检：.oix 里 extension.pyd 与 fields.pyd 同名规则一致。

### T11 全量回归

- 步骤：
  1. `uv run pytest -q`。
  2. `uv run python scripts/verify_ui.py` 出 light 与 dark 截图。
  3. 汇总失败项并按任务回填。
- 验收命令：`uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：pytest 全绿，两套截图文件存在）
- 验收记录：`uv run pytest -q` → 386 passed, 2 skipped；`scripts/verify_ui.py --theme light|dark` 各 60 项 PASS、退出码 0
- 自检：截图里 light 主文本为黑、dark 未变。

### T12 同步技能文档

- 步骤：
  1. `.agents/skills/obox-theme-dev/references/theme-constants.md`：更新 light 的 TEXT 色值与说明。
  2. `.agents/skills/obox-ext-dev/references/i18n.md`：写明四语言集合、i18n.json 必须四语言齐全、打包不得依赖运行期 exec。
  3. 跑 `check_all.py`。
- 验收命令：`uv run python .agents/skills/obox-test/scripts/check_all.py`（期望：全绿）
- 验收记录：theme-constants.md 与 obox-ext-dev/references/i18n.md 已更新；check_all.py 未跑，见 validation 遗留
- 自检：技能里的示例与当前实现一致，不留旧色值。

### T13 设置扩展标题

- 步骤：
  1. `extensions/settings/extension.py` 的 `register_view(..., "设置")` 标题改成 占位符 `i18n.settings.title`。
  2. `extensions/settings/i18n.json` 确认 `settings.title` 有四种语言。
- 验收命令：`grep -nE '"[^"]*[一-龥]' extensions/settings/extension.py | grep -v '#' | wc -l`（期望：0）
- 验收记录：侧栏标题改为占位符并由宿主替换；settings 扩展仅剩模块与函数注释含中文；verify_ui PASS
- 自检：侧栏 tooltip 在 en-US 下为 Settings。

### T14 宿主侧翻译通道

- 步骤：
  1. `obox/ui/template.py`：`Binding.apply` 写入文本前，对含 `{{i18n.` 的值调用视图 owner 的翻译（owner 由 ViewHandle 携带）。
  2. `obox/ui/main_window.py`：`_make_rail_button` 写 tooltip 前替换占位符，objectName 用替换后的文本。
  3. `obox/app.py`：装配时把 owner 传给视图句柄；未注册的占位符保持原样。
  4. 补测试：构造一个视图数据含 占位符 `i18n.demo.title`，断言英文下替换为英文。
- 验收命令：`uv run pytest -q tests/test_i18n_switch.py tests/test_app_handlers.py`（期望：通过）
- 验收记录：`uv run pytest -q tests/test_builder.py tests/test_app_smoke.py tests/test_app_handlers.py tests/test_i18n_switch.py` → 通过
- 自检：占位符未被误替换成空串；obb 自身文案路径不变。

## 测试策略

待执行阶段确认：TDD / 常规

## 执行顺序

1. T1 ∥ T2 ∥ T9
2. T3 ∥ T4 ∥ T14
3. T5 ∥ T6 ∥ T7 ∥ T8 ∥ T13
4. T10 ∥ T12
5. T11

## 覆盖检查

- 开机自启动 → T2、T3
- 界面文案多语言覆盖 → T1、T3、T4、T5、T6、T7、T8、T13、T14
- 主题色板与文字层级 → T9、T12
- 设置读写 → T1、T3
- 设置扩展 → T3
- 扩展故障隔离 → T3、T5
- 扩展打包产物 → T8、T10

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，且没有"同文件无依赖"的并行任务
- [x] `方式` 只取 `主 Agent` / `subagent` / `后台`
- [x] 模板占位符与注释全部替换
