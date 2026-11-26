---
status: done
---

# PyQt5 与 PySide6 双绑定 Spec Delta

## Purpose

同一套 obox 代码同时兼容 PySide6 与 PyQt5，构建与运行时二选一，两个绑定下 UI 与 API 行为一致。

## ADDED Requirements

### Requirement: 双绑定兼容层

工程 SHALL 提供唯一的 Qt 绑定层 obox/qt.py，按 OBOX_QT（pyside6 或 pyqt5）选择绑定，命令行 --qt 可覆盖，缺省 pyside6。绑定层 SHALL 统一导出 QtCore、QtGui、QtWidgets、QtNetwork、QtSvg、QtTest、Qt、Signal、Slot、Property、QAction、exec_app、event_pos、event_global_pos、icon_pixmap，并抹平两个绑定的差异。obox、脚本与测试 SHALL 不再直接 import PySide6 或 PyQt5。

#### Scenario: 选择 PySide6
- **WHEN** 未设置 OBOX_QT 且未传 --qt
- **THEN** 绑定层加载 PySide6，程序正常运行

#### Scenario: 选择 PyQt5
- **WHEN** OBOX_QT=pyqt5 或 --qt pyqt5
- **THEN** 绑定层加载 PyQt5，程序正常运行

#### Scenario: 非法绑定
- **WHEN** OBOX_QT 取值不在 pyside6/pyqt5
- **THEN** 启动时报错退出并指明合法取值

### Requirement: 双绑定行为一致

同一组 pytest 与 verify_ui（light/dark）SHALL 在两个绑定下全部通过；界面布局、主题、事件与 API 返回一致。

#### Scenario: 双绑定测试
- **WHEN** 分别在 pyside6 与 pyqt5 下运行 pytest
- **THEN** 两次都通过且用例数相同

### Requirement: 依赖与安装包

运行期依赖为 PySide6（默认）或 PyQt5（可选 extra pyqt5），外加 matplotlib 与 paramiko；构建脚本用 --qt 选择绑定并排除另一绑定，安装包名带绑定标识，CI 按绑定矩阵出包与测试。

#### Scenario: 构建 PyQt5 包
- **WHEN** 执行 build_installer.py --qt pyqt5
- **THEN** Nuitka 以 pyqt5 插件编译并排除 PySide6，产物名含 pyqt5


## Impact

- 137 处绑定 import 收敛到 obox.qt
- PyQt5 下需处理 Qt6 专有 API（事件坐标、QIcon.pixmap、QLocale 地区名）与字符串颜色
- 安装包与 CI 增加 binding 维度；同一机器源码运行可切换绑定