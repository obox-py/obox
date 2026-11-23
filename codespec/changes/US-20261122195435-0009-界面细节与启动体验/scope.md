---
status: done
---

# Scope

## 目标范围

本次只动外壳与主题两层：obox/app.py、托盘/标题栏/主窗口/应用窗口、设置页片段、两套主题的常量与 QSS、exe 图标与验证脚本；由启动落点、任务栏标识、托盘常驻、运行中切换套件、设置扩展、自绘标题栏、视觉统一七条需求驱动。

## 可改（白名单）

- `obox/app.py`
- `obox/ui/tray.py`
- `obox/ui/main_window.py`
- `obox/ui/title_bar.py`
- `obox/ui/app_window.py`
- `obox/assets/obox.ico`
- `obox/assets/icons/window-{min,max,restore,close}.svg`（用户要求窗口按钮改用 SVG 图标）
- `extensions/settings/views/main.oml`
- `theme/light/theme.py`
- `theme/dark/theme.py`
- `theme/light/provider.py`
- `theme/dark/provider.py`
- `scripts/build_exe.py`
- `scripts/verify_ui.py`
- `tests/test_settings_label.py`
- `tests/test_app_switches.py`
- `tests/test_tray.py`
- `tests/test_titlebar.py`
- `tests/test_theme_kits.py`
- `tests/test_component_protocol.py`
- `tests/test_settings_filter.py`
- `tests/test_i18n_switch.py`
- `.theme/**`
- `.agents/skills/obox-theme-dev/**`
- `.agents/skills/obox-ui-test/**`

## 明确不动

- `codespec/**`：规格与变更产物由 df 流程维护
- `obox/api/**`、`obox/core/**`、`obox/extensions/**`
- `obox/ui/builder.py`、`obox/ui/component_protocol.py`、`obox/ui/kit.py`、`obox/ui/qss.py`、`obox/ui/close_dialog.py`
- `theme/light/components/**`、`theme/dark/components/**`：本次不碰组件
- `extensions/demo/**`、`extensions/gallery/**`、`extensions/settings/extension.py`
- `installer/**`、`dist/**`、`build/**`、`.obox/**`
- `pyproject.toml`、`uv.lock`
- `.agents/skills/df-*/**`、`.agents/skills/obox-ext-dev/**`、`.agents/skills/obox-test/**`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」——把路径、理由与需求名替换成实际值，拿到用户确认后才扩范围；不许先改了再解释。

## 与任务的一致性

白名单覆盖 task.md 的 T1-T10：T1 app.py + 设置页 + 新测试；T2 app.py + main_window；T3 app.py；T4 app.py + app_window + build_exe + obox.ico；T5 tray.py + test_tray；T6 app.py；T7 两套 theme/provider + theme-dev 技能；T8 title_bar + main_window + app；T9 verify_ui + ui-test 技能；T10 .theme 与全量验证。

两个技能目录按 AGENTS.md 的强制同步规则放开：主题常量与 QSS 归 obox-theme-dev，截图编号与托盘场景归 obox-ui-test。
