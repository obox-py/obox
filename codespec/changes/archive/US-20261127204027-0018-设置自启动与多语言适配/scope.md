---
status: done
---

# Scope

## 目标范围

本次只动设置自启动、壳层与扩展文案、语言存储形态、浅色主文本与 rdp 打包入口，由 delta-spec 的七条需求驱动；api 契约、宿主进程与构建脚本不动。

## 可改（白名单）

- `obox/app.py`
- `obox/i18n.py`
- `obox/i18n.json`
- `obox/core/autostart.py`
- `obox/ui/tray.py`
- `obox/ui/close_dialog.py`
- `obox/ui/template.py`
- `obox/ui/main_window.py`
- `extensions/*/extension.py`
- `extensions/*/i18n.json`
- `extensions/rdp/fields.py`
- `theme/light/theme.py`
- `theme/light/styles.qss`
- `.theme/light/**`
- `tests/test_i18n*.py`
- `tests/test_autostart.py`
- `tests/test_hardcoded_text.py`
- `tests/test_tray.py`
- `tests/test_settings_close.py`
- `tests/test_settings_label.py`
- `tests/test_app_switches.py`
- `tests/test_app_smoke.py`
- `tests/test_app_handlers.py`
- `dist/rdp.*.oix`
- `.agents/skills/obox-theme-dev/references/theme-constants.md`
- `.agents/skills/obox-ext-dev/references/i18n.md`
- `extensions/settings/**`
- `extensions/*/views/*.oml`
- `obox/ui/builder.py`
- `obox/ui/window_api.py`
- `scripts/verify_ui.py`
- `codespec/changes/US-20261127204027-0018-设置自启动与多语言适配/**`

## 明确不动

- `obox/api/**`（消息类型与协议字段不动）
- `obox/extensions/host.py`、`obox/extensions/supervisor.py`、`obox/extensions/manifest.py`
- `obox/ui/modal_dialog.py`
- `scripts/**`（打包与构建规则不变；`scripts/verify_ui.py` 的语言断言随四种语言模型改写，已单独列入白名单）
- `theme/dark/**`
- `pyproject.toml`、`uv.lock`
- `codespec/specs/**`（基线由收尾合并统一改）
- `docs/arch.md`、`README.md`
- `.obox/config.json`（运行时产物，不手改）

## 越界处置

停手，报出三件事：要改的路径、理由、对应的需求名；拿到用户确认后才扩范围，不许先改了再解释。

## 与任务的一致性

T1→obox/i18n.*、tests/test_i18n*；T2→obox/core/autostart.py、tests/test_autostart.py；T3→obox/app.py、tests/test_app_*、test_settings_*；T4→obox/ui/tray.py、close_dialog.py、tests/test_tray.py；T5→extensions/management/*；T6→extensions/app/*、gallery/*；T7→demo、chartdemo、pickerdemo、webapp；T8→extensions/rdp/*；T9→theme/light/*、.theme/light；T10→dist/rdp.*.oix；T11→tests/、scripts/verify_ui.py（只跑不改）；T12→两个技能 reference；T13→extensions/settings/*；T14→obox/ui/template.py、obox/ui/main_window.py、obox/app.py、tests/test_app_handlers.py。
