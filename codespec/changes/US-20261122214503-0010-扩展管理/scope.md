---
status: done
---

# Scope

## 目标范围

本次只做「扩展管理」这一条线：新增控制消息与宿主处理、loader 单包能力、obox 编排与增量应用、摘视图与确认框、管理扩展本体、端到端测试与验证脚本；由扩展管理、扩展安装、扩展生命周期与上下文注入、扩展目录与清单四条需求驱动。

## 可改（白名单）

- `obox/api/extensions.py`
- `obox/extensions/host.py`
- `obox/extensions/loader.py`
- `obox/app.py`
- `obox/ui/main_window.py`
- `obox/ui/confirm_dialog.py`
- `obox/i18n.json`
- `extensions/management/**`
- `tests/test_extension_manage.py`
- `scripts/verify_ui.py`
- `.agents/skills/obox-ext-dev/**`
- `.theme/**`

## 明确不动

- `codespec/**`：规格与变更产物由 df 流程维护
- `obox/core/**`、`obox/extensions/{context,contributions,manifest}.py`、`obox/api/` 下除 extensions.py 以外的文件
- `obox/ui/{tray,title_bar,close_dialog,builder,kit,qss}.py`
- `theme/light/**`、`theme/dark/**`：本次不加主题常量与组件
- `extensions/app/**`、`extensions/gallery/**`、`extensions/demo/**`、`extensions/settings/**`
- `installer/**`、`dist/**`、`build/**`、`.obox/**`（运行期数据，测试用 tmp_path）
- `pyproject.toml`、`uv.lock`
- `.agents/skills/df-*/**`、`.agents/skills/obox-theme-dev/**`、`.agents/skills/obox-ui-test/**`、`.agents/skills/obox-test/**`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」——把路径、理由与需求名替换成实际值，拿到用户确认后才扩范围；不许先改了再解释。

## 与任务的一致性

白名单覆盖 T1-T10：T1 消息模块；T2 loader；T3 host；T4 app；T5 main_window 与确认框；T6 管理扩展目录；T7 测试；T8 verify_ui；T9 obox-ext-dev；T10 .theme 与全量验证。obox/i18n.json 用于新增的对话框文案，属于 T5/T6 的必要落点。
