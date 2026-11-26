---
status: done
---

# PyQt5 与 PySide6 双绑定 Design Delta

## Context

obox 与脚本、测试此前直接 import PySide6；主题包已无绑定依赖。两套绑定可在同一环境安装，但同进程混用会崩溃，必须在 import 前选定。

## Scope

- 双绑定兼容层（ADDED）
- 双绑定行为一致（ADDED）
- 依赖与安装包（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/qt.py`（新） | 绑定选择、统一导出、exec_app、event_pos/event_global_pos、icon_pixmap | 兼容层 |
| obox/**、scripts/**、tests/** | 137 处 PySide6 import 改为 obox.qt | 兼容层 |
| `obox/main.py` | --qt 参数，在 import app 前写 OBOX_QT | 兼容层 |
| `pyproject.toml` | pyqt5 可选 extra | 依赖与安装包 |
| `scripts/build_exe.py`、`build_installer.py` | --qt 选择插件、排除另一绑定、产物名带绑定 | 依赖与安装包 |
| `.github/workflows/build.yml` | test/package 增加 binding 矩阵 | 双绑定行为一致 |
| 文档与技能 | 绑定选择、扩展不要直接 import Qt | 兼容层 |

## Decisions

- 自建 obox/qt.py 而非 qtpy：差异点只覆盖实际用到的 API，少一个依赖。
- 缺省 PySide6；PyQt5 通过 OBOX_QT=pyqt5 或 --qt pyqt5 启用。
- 兼容 helper：event_pos/event_global_pos（Qt6 position/globalPosition vs Qt5 localPos/globalPos）、icon_pixmap（Qt6 可传 DPR，Qt5 取后设 DPR）、exec_app。
- 颜色：PyQt5 的 QPen/QBrush 不接受 str，统一先 color() 成 QColor。
- 构建：Nuitka --enable-plugin 选绑定，--nofollow-import-to 排除另一绑定。
- 主题与扩展不改；扩展若需要 Qt 能力，文档约定用 obox.qt。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 新增双绑定兼容与行为一致；依赖与安装包改为二选一 |
| design.md | 新增 D48 绑定层与差异适配、D49 按绑定构建 |
| docs/arch.md | 逻辑架构补 obox/qt.py；部署架构补绑定维度 |
| README.md | 安装与运行补 OBOX_QT/--qt 说明 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 两绑定同进程混用崩溃 | 绑定层单次选择；pytest 用 -o qt_api 对齐 |
| PyQt5 缺少 Qt6 API | 兼容 helper 与 Qt5 回退分支 |
| Nuitka 同时打包两套 Qt | --nofollow-import-to 排除另一绑定 |
| PyQt5 下绘制差异 | 双绑定 verify 截图对比 |

回滚：删 obox/qt.py 与 --qt，恢复 PySide6 import。
