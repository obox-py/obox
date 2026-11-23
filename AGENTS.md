# AGENTS.md

本文件写给在本仓库工作的 agent。

## 工程速览

- Python 3.12 + PySide6；主程序在 `obox/`，主题套件在 `theme/{light,dark}`，扩展在 `extensions/`，产物在 `.theme/` 与 `dist/`
- 常用命令：`uv sync`、`uv run obox`、`uv run pytest -q`、`uv run python scripts/build_theme.py`、`uv run python scripts/verify_ui.py`、`uv run python scripts/build_installer.py`
- 规格与变更：`codespec/specs` 是基线，`codespec/changes/US-*` 是变更产物；技能与本文档不能替代基线与流程

## 强制规则：组件与 API 变更必须同步技能

只要改动下列任一内容，**必须在同一次改动里更新 `.agents/skills` 对应技能**：

| 改动 | 必须同步 |
|---|---|
| 组件标签、状态、事件、容器契约 | `obox-theme-dev`（references/component-contract.md，必要时 templates/component.py） |
| theme 常量、QSS、配色/圆角/间距 | `obox-theme-dev`（references/theme-constants.md） |
| 组件数量、标签清单、REQUIRED_TAGS | `obox-theme-dev` 与 `obox-ext-dev` 里所有标签计数（当前 21 个标签） |
| 扩展清单字段（views 容器、app、configuration）、context API、oml 指令与绑定、i18n.json、打包产物 | `obox-ext-dev`（references/*、templates/*、scripts/*） |
| verify_ui 场景、截图编号、UiDriver 能力 | `obox-ui-test`（references/scenarios.md、driver.md） |
| 测试矩阵、质量门禁命令、排障 | `obox-test`（references/matrix.md、gates.md、troubleshooting.md） |

规则落地方式：

1. 改代码的同一提交里改技能，禁止「先合并、后补文档」
2. 新增/删除组件时，用 `obox-theme-dev` 的 `scaffold_component.py` 同步两套套件与技能里的标签计数
3. 扩展 API 有变化时，同步 `obox-ext-dev` 的 references 与脚手架模板，确保新扩展按新 API 生成
4. 提交前跑：

```bash
uv run python .agents/skills/obox-test/scripts/check_all.py
```

## 其他约定

- 构建 pyd 前先关闭正在运行的 obox（Windows 会锁文件）
- 测试与验证脚本显式传 `language="zh-CN"`，避免 `.obox/config.json` 污染
- 组件与主题改动后必须重编 `.theme`，否则运行时仍是旧实现