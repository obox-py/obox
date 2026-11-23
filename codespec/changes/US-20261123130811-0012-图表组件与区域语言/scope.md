---
status: done
---

# Scope

## 目标范围

把 21 个组件迁进 obox 并改为调色板取色，主题瘦身为样式包；新增 matplotlib 图表组件；i18n 支持区域回退与全量地区语言项。由图表组件、区域语言与缺省回退、界面套件清单与加载、组件契约不变、组件能力接口与消息处理分界、主题色板与文字层级、i18n 注册与占位替换、设置扩展八条需求驱动。

## 可改（白名单）

- `pyproject.toml`、`uv.lock`
- `obox/i18n.py`
- `obox/app.py`
- `obox/ui/palette.py`
- `obox/ui/components/**`
- `obox/ui/component_protocol.py`
- `obox/ui/builder.py`
- `obox/ui/kit.py`
- `theme/light/theme.py`、`theme/light/provider.py`
- `theme/dark/theme.py`、`theme/dark/provider.py`
- `theme/_build/light.py`、`theme/_build/dark.py`
- `theme/light/components/**`、`theme/dark/components/**`（迁移后删除）
- `scripts/verify_ui.py`
- `tests/**`
- `.theme/**`
- `.agents/skills/obox-theme-dev/**`
- `.agents/skills/obox-ext-dev/**`
- `.agents/skills/obox-ui-test/**`

## 明确不动

- `codespec/**`
- `obox/core/**`、`obox/api/**`、`obox/extensions/**`
- `obox/ui/registry.py`、`obox/ui/template.py`、`obox/ui/main_window.py`、`obox/ui/anchor.py`、`obox/ui/qss.py`、`obox/ui/parser.py`
- `extensions/**`
- `installer/**`、`dist/**`、`build/**`、`.obox/**`
- `.agents/skills/df-*/**`、`.agents/skills/obox-test/**`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」——把路径、理由与需求名替换成实际值，拿到用户确认后才扩范围；不许先改了再解释。

## 与任务的一致性

白名单覆盖 T1-T10：T1 i18n.py；T2 app.py；T3 palette.py；T4 components 与 tests；T5 component_protocol/builder/kit/app；T6 theme 两套与 _build；T7 chart；T8 verify_ui；T9 三个技能目录；T10 pyproject/uv.lock/.theme 与全量验证。
