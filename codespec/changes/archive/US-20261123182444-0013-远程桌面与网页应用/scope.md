---
status: done
---

# Scope

## 目标范围

新增两个用户扩展（rdp、webapp）与一条扩展配置下发通道；系统能力（DPAPI、mstsc、Chrome）封在扩展内。由远程桌面扩展、网页应用扩展、扩展配置贡献、扩展开发技能四条需求驱动。

## 可改（白名单）

- `obox/api/settings.py`
- `obox/app.py`
- `extensions/rdp/**`
- `extensions/webapp/**`
- `tests/test_extension_config.py`
- `tests/test_extensions_process.py`
- `scripts/verify_ui.py`
- `.agents/skills/obox-ext-dev/**`

## 明确不动

- `codespec/**`
- `obox/core/**`、`obox/extensions/**`、`obox/ui/**`
- `extensions/app/**`、`extensions/demo/**`、`extensions/gallery/**`、`extensions/settings/**`、`extensions/management/**`
- `theme/**`（两个扩展不做主题改动，界面沿用 docs/UI.md）
- `installer/**`、`dist/**`、`build/**`、`.obox/**`
- `pyproject.toml`、`uv.lock`
- `.agents/skills/df-*/**`、`.agents/skills/obox-theme-dev/**`、`.agents/skills/obox-ui-test/**`、`.agents/skills/obox-test/**`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」——把路径、理由与需求名替换成实际值，拿到用户确认后才扩范围；不许先改了再解释。

## 与任务的一致性

白名单覆盖 T1-T10：T1 api/settings 与 app；T2-T4 rdp；T5-T7 webapp；T8 verify_ui；T9 技能文档；T10 全量验证。
