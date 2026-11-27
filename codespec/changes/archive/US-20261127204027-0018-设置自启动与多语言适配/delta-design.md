---
status: done
---

# 设置与多语言 Design Delta

> 受影响的组件、依赖方向与流程时序由 `df-arch` 画在 `codespec/changes/US-20261127204027-0018-设置自启动与多语言适配/delta-arch.md`。本文件只写这次改哪里、为什么这么改、基线会怎么变。

## Context

改动落在宿主壳层（obox/）、主题套件（theme/light）与随包扩展（extensions/*）三处，不新增加载路径：

- 设置与配置读写集中在 obox/app.py（_settings_groups、_save_settings、_on_settings_set）；语言注册与回退在 obox/i18n.py。
- 壳层文案当前硬编码在 obox/ui/tray.py:26-36 与 obox/ui/close_dialog.py:12-24，绕过了 D11 约定的 i18n 注册通道。
- 扩展打包遵循 D15：scripts/pack_extension.py 只编译入口 import 图可达的 .py；rdp 用 `exec(read_text())` 读兄弟文件，图里没有它。
- 主题文字色由 theme/light/theme.py 的 TEXT 常量经 styles.qss 注入，改常量即可，不动组件实现（D12）。

## Scope

覆盖 delta-spec 的六条：开机自启动、界面文案多语言覆盖、主题色板与文字层级、设置读写、设置扩展、扩展故障隔离、扩展打包产物。

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/core/autostart.py`（新增） | winreg 读写 HKCU Run 的 `obox` 值：enable/disable/is_enabled/current_command；路径取打包后的 exe，源码运行返回不可用 | 开机自启动 |
| `obox/app.py` | 行为分组增加 `obox.autostart` bool 项，_validate_setting 与 _on_settings_set 分发；启动时同步注册表与配置；失败原因并入通知文案 | 开机自启动、扩展故障隔离、设置扩展 |
| `obox/i18n.py` | 增加 SUPPORTED_LANGUAGES 常量（zh-CN/zh-HK/zh-TW/en-US）与 label→code 映射；normalize_language 供启动迁移 | 界面文案多语言覆盖、设置读写 |
| `obox/i18n.json` | 补齐 zh-HK、zh-TW 文案；新增托盘、关闭框、toast、扩展失败相关条目 | 界面文案多语言覆盖 |
| `obox/ui/tray.py` | 构造参数接收 translator，菜单项与分组标题改为翻译取值；切语言后重建菜单 | 界面文案多语言覆盖 |
| `obox/ui/close_dialog.py` | 构造参数接收 translator，标题、提示、三个按钮与「记住选择」走 i18n | 界面文案多语言覆盖 |
| `extensions/*/extension.py`、`extensions/*/i18n.json` | 9 个扩展（含 settings）的硬编码文案抽成 i18n 占位符并补齐四种语言；management 的「激活/失败/已禁用/用户安装」等标签入 i18n，条目副标题显示失败原因 | 界面文案多语言覆盖、扩展故障隔离 |
| `obox/ui/template.py`、`obox/ui/main_window.py` | 数据绑定文本与侧栏标题在写入控件前，按该视图所属扩展的命名空间替换 i18n 占位符 | 界面文案多语言覆盖 |
| `extensions/rdp/extension.py` | `exec(fields.py)` 改为 `from fields import FIELDS`，让 import 图覆盖该模块 | 扩展打包产物 |
| `theme/light/theme.py`、`theme/light/styles.qss` | TEXT 改为 #000000；TEXT_MUTED 保持 #86909c；重编 .theme/light | 主题色板与文字层级 |
| `scripts/`、`tests/` | 打包后校验安装目录无 .py 且扩展可加载；i18n 键集合一致性测试；autostart 单测（monkeypatch winreg） | 扩展打包产物、界面文案多语言覆盖、开机自启动 |

新增类型只有一个模块：`obox/core/autostart.py`。不内联进 app.py 的理由是 winreg 调用要在无 Qt 环境单测，而 app.py 已有 1700 行；删掉该模块会让「开关写注册表」这条判据无法在 CI 上验证。

## Baseline Diff

- design.md D43「Windows 能力封在扩展内」加一条例外：宿主自身的开机自启动由 obox/core/autostart.py 用 winreg 直接写 HKCU Run，其它 DPAPI/cmdkey/mstsc 仍封在扩展内。理由是自启动指向 obox.exe 本身，宿主不启动自己就没法由扩展代管。
- design.md D15「扩展编译为 pyd 并打包为 .oix」补一句：扩展的运行期依赖必须落在 import 图内，打包器只编译 import 可达的模块，扩展不得在运行期 exec 兄弟源码文件。
- design.md 新增 D46：语言集合固定为 zh-CN/zh-HK/zh-TW/en-US，配置统一存 BCP-47 码，列表由宿主常量给出并用测试守护覆盖度；否掉「按 QLocale 全量枚举」与「按已注册文案动态求交集」（前者必然缺文案，后者随扩展加载时序抖动）。
- docs/arch.md 第 4 节逻辑架构增加 obox/core/autostart.py 与宿主配置流向；第 7 节运行架构补安装版写 HKCU Run 一条；依赖方向不变。
- design.md D46 之外新增 D47：扩展不持有翻译表，文案以 i18n 占位符形式经消息传给宿主，由宿主在渲染点按扩展命名空间替换；否掉给扩展下发文案表（多一条同步通道，语言切换时扩展进程要重启）与让扩展自备多语言文件（与 obox/i18n.json 两套事实）。
- spec.md 的六处改动由 delta-spec 定义，合并时按它替换。

## Risks / Rollback

- winreg 写入被组策略或权限拒绝：捕获 OSError，开关回滚为 false 并在设置项描述里提示，不阻断启动。
- 旧配置标签迁移误伤：只映射四个已知标签，其余值回退 zh-CN 并保留原值到日志；迁移只写一次，回滚即删掉顶层 language 键让程序回落默认。
- 四语言文案量大（obox 约百条 + 8 个扩展），漏键会让界面回退中文：用键集合测试守住，缺键即红。
- rdp 改 import 后若 fields.py 出现导入副作用会连带失败：fields.py 只有数据表，无副作用；若仍失败，回滚为 exec 并在打包器里显式带上该文件（记录在案）。
- 浅色正文改黑后对比度过高：用 `uv run python scripts/verify_ui.py` 出 light/dark 截图回归，必要时只调 TEXT 不改其它色阶。
