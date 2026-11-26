---
status: done
---

# PyQt5 与 PySide6 双绑定兼容

## 背景

现在 137 处 import 直接写 PySide6，主题包已经不依赖绑定，扩展只经 obox.api 交互。要求同一套代码在 PyQt5 与 PySide6 下都能运行，构建与运行时可选择其一，且两套绑定的 UI 与 API 行为完全一致。

## 目标

- 新增唯一绑定层 obox/qt.py：按 OBOX_QT=pyside6|pyqt5 选择，命令行 --qt 覆盖，缺省 PySide6
- obox、脚本与测试统一从绑定层取 QtCore/QtGui/QtWidgets/Qt/Signal/Slot/Property/QAction 与 exec
- 两套绑定下 pytest 与 verify（light/dark）全部通过，界面行为与 API 一致
- 构建按绑定出安装包与扩展产物：产物名带绑定，PyQt5 与 PySide6 不混装
- 主题包与用户扩展不改：主题本来无绑定依赖，扩展只用 obox.api

## 范围

**做：**

- 绑定层与差异适配：scoped enums、Signal/Property、QAction 位置、exec、QFont 度量、HighDPI 属性
- 全量替换 obox/、scripts/、tests/ 里的 PySide6 import 为绑定层
- pyproject：PySide6 保持基础依赖，PyQt5 作为可选 extra；构建脚本支持 --qt 选绑定
- CI 矩阵增加 binding 维度；README 与技能文档说明选择方式
- 双绑定测试与 verify 截图

**不做：**

- 同一进程同时加载两套绑定
- 兼容 Qt6 专有 API（统一用 5.15 可用子集）
- 改主题包内容（已无绑定依赖）
- 扩展源码兼容层（扩展不应直接 import Qt；如需，文档说明用 obox.qt）

## 需求草案

1. obox/qt.py 依据 OBOX_QT 或 --qt 选择绑定；非法值报错退出
2. 绑定层导出 QtCore、QtGui、QtWidgets、Qt、Signal、Slot、Property、QAction、exec_app
3. 所有 obox 代码不再直接 import PySide6/PyQt5；脚本与测试同规则
4. 枚举、事件类型、字体权重等写法在两端一致（scoped enum 可直接用）
5. PyQt5 下 Signal=pyqtSignal、Property=pyqtProperty、QAction 取自 QtWidgets、exec 用 exec_
6. 构建脚本按 --qt 选择依赖与打包；安装包名带绑定与架构
7. CI 在 PySide6 与 PyQt5 下各跑 pytest 与 verify light/dark
8. 扩展与主题代码不改；文档补「扩展不要直接 import Qt」

## 关键取舍

- 自建绑定层而不是引入 qtpy：少一个依赖，差异点只针对实际用到的 API
- 缺省 PySide6：现有产物与 CI 不变，PyQt5 作为显式选项
- 每绑定一套安装包：避免双份 Qt 运行库混装与体积翻倍
- 统一用 Qt 5.15 可用子集：PySide6 下也能跑，减少分支

## 与基线的冲突

- 基线依赖写死 PySide6，需 MODIFIED 为「PySide6 或 PyQt5 二选一」
- 基线构建与安装包只描述单一绑定，需补 binding 维度
- 技能文档里的 import 示例需改为绑定层

## 假设

- PyQt5 版本 5.15.11+，PySide6 6.6+
- 选择方式：环境变量 + CLI，缺省 PySide6（提问超时，按推荐执行）
- 发布：每个绑定一套安装包；PyQt5 是否随版本长期发布由用户后续决定
