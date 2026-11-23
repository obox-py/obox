---
status: done
---

# Scope

## 目标范围

本次只改浮层、卡片选中态与标题栏语言入口三处：两套套件的 card 与 modal 组件及其 QSS、关闭询问框、标题栏与壳的语言入口、两个示例片段、验证脚本与两个技能文档；由 delta-spec 的浮层、选择容器与卡片、i18n 注册与占位替换、视觉统一四条需求驱动。

## 可改（白名单）

- `theme/light/components/card.py`
- `theme/dark/components/card.py`
- `theme/light/components/button.py`
- `theme/dark/components/button.py`
- `obox/api/events.py`
- `theme/light/components/modal.py`
- `theme/dark/components/modal.py`
- `theme/light/theme.py`
- `theme/dark/theme.py`
- `obox/ui/close_dialog.py`
- `obox/ui/title_bar.py`
- `obox/ui/main_window.py`
- `obox/ui/app_window.py`（删一行对已移除按钮的引用，属同一需求的连带修复）
- `obox/app.py`
- `extensions/demo/views/main.oml`
- `extensions/gallery/views/main.oml`
- `scripts/verify_ui.py`
- `tests/test_card.py`
- `tests/test_choice.py`
- `tests/test_components.py`
- `tests/test_settings_close.py`
- `tests/test_titlebar.py`
- `tests/test_i18n_switch.py`
- `tests/test_settings_filter.py`
- `tests/test_kit_switch.py`
- `tests/test_builder.py`
- `tests/test_e2e.py`
- `.agents/skills/obox-theme-dev/**`
- `.agents/skills/obox-ui-test/**`
- `.theme/**`

## 明确不动

- `codespec/**`：规格与变更产物由 df 流程维护，执行阶段只读
- `obox/ui/builder.py`、`obox/ui/component_protocol.py`、`obox/ui/kit.py`、`obox/ui/qss.py`
- `obox/core/**`、`obox/api/**`（`events.py` 已按用户批准扩入白名单）、`obox/extensions/**`
- `theme/light/provider.py`、`theme/dark/provider.py`
- `theme/light/components/__init__.py`、`theme/dark/components/__init__.py`
- `theme/light/components/{alert,base,checkbox,choice,container,flex,image,input,navitem,notification,radio,select,slider,switch,table,tabs,tag}.py` 与 dark 同名文件
- `extensions/demo/**` 除 `views/main.oml`；`extensions/gallery/**` 除 `views/main.oml`
- `extensions/demo/extension.py`、`extensions/gallery/extension.py`
- `pyproject.toml`、`uv.lock`
- `dist/**`、`build/**`、`.obox/**`
- `.agents/skills/df-*/**`、`.agents/skills/obox-ext-dev/**`、`.agents/skills/obox-test/**`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」——把路径、理由与需求名替换成实际值，拿到用户确认后才扩范围；不许先改了再解释。

## 与任务的一致性

白名单覆盖 task.md 中 T6-T14 的全部「涉及文件 / 模块」，逐条对应：T6 card 两套与两个测试；T7-T8 modal 与 theme.py 两套；T9 close_dialog 与其测试；T10 title_bar、main_window、app 与标题栏测试；T11 两个 OML；T12 verify_ui；T13 两个技能目录；T14 .theme 产物。

T1-T5 为迭代一已完成任务，其文件（其余 17 个组件、provider、字体）列入「明确不动」，本次执行不再触碰。tests 目录按单文件放开，避免整目录授权。
