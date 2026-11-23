---
name: obox-theme-dev
description: 开发 obox 主题套件与组件时使用。覆盖主题作为样式包的契约：theme.py 调色板与 QSS、字体、Nuitka 构建 pyd、套件切换；组件实现已移到 obox/ui/components，主题不再提供组件类。
---

# obox 主题套件开发

## 何时用

- 新增/修改 light 与 dark 套件里的组件
- 调整配色、圆角、间距、字体与 QSS
- 构建 .theme 下的 pyd、切主题、排查套件加载失败

## 快速开始

```bash
# 契约校验（需要先构建，见下）
uv run python .agents/skills/obox-theme-dev/scripts/check_theme.py

# 新增一个组件骨架（两个套件同时生成）
uv run python .agents/skills/obox-theme-dev/scripts/scaffold_component.py divider

# 构建两套 pyd
uv run python scripts/build_theme.py
```

## 步骤

1. 契约：组件类继承 `Component`，声明 tag/supported_states/state_accessors/supported_events/event_methods，实现 `build_widget` 与可选的 `container_layout`
2. 组件实现在 `obox/ui/components/`，主题只通过调色板（PALETTE）与 QSS 影响外观
3. 新组件注册在 `obox/ui/components/__init__.py` 的 COMPONENT_TYPES，标签数断言与技能文档同步（当前 21 个既有标签 + chart + collapse）
4. 外观：颜色/圆角/间距取 `theme.py` 常量；背景与描边优先自绘，QSS 只做全局规则
5. 构建：`scripts/build_theme.py` 会编译 `.theme/{light,dark}`，运行时按配置或 `--theme` 加载
6. 校验：check_theme.py 检查标签齐全与类契约；再跑仓库测试与 verify_ui

## 参考

- `references/component-contract.md`
- `references/theme-constants.md`
- `references/build-and-switch.md`

## 模板

- `templates/component.py`、`templates/theme.py`

## 边界

- kit 不能 import obox；组件只依赖 PySide6 与自己的 theme 模块
- 改组件后必须重编 pyd，否则运行时仍是旧实现