---
status: done
---

# Scope

## 目标范围

只做通用视图锚点能力与 sticky 吸顶：消息、滚动控制器、装配识别与测试文档；设置页保持原布局，不在本次范围内。

## 可改（白名单）

- `obox/api/view.py`
- `obox/ui/anchor.py`
- `obox/app.py`
- `tests/test_anchor.py`
- `.theme/**`
- `.agents/skills/obox-ext-dev/**`

## 明确不动

- `codespec/**`
- `obox/core/**`、`obox/api/` 下除 view.py 以外的文件
- `obox/ui/builder.py`、`obox/ui/parser.py`、`obox/ui/registry.py`、`obox/ui/main_window.py`、`obox/ui/kit.py`、`obox/ui/qss.py`
- `theme/light/**`、`theme/dark/**`：设置页样式已还原，无净改动
- `extensions/**`：设置页回到原布局，其它扩展不改
- `scripts/verify_ui.py`：按原场景验证，不新增锚点场景
- `installer/**`、`dist/**`、`build/**`、`.obox/**`
- `pyproject.toml`、`uv.lock`
- `.agents/skills/df-*/**`、`.agents/skills/obox-theme-dev/**`、`.agents/skills/obox-ui-test/**`、`.agents/skills/obox-test/**`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」——把路径、理由与需求名替换成实际值，拿到用户确认后才扩范围；不许先改了再解释。

## 与任务的一致性

白名单覆盖 T1-T5：T1 view.py；T2 anchor.py；T3 app.py；T4 技能文档；T5 .theme 与全量验证。
