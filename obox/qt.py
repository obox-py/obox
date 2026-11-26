"""Qt 绑定层：统一 PyQt5 与 PySide6 的 API，供 obox 内部使用。

选择方式：环境变量 OBOX_QT=pyside6|pyqt5，缺省 pyside6；命令行 --qt 在启动前写入环境变量。
所有 obox、脚本与测试都从这里取 Qt 名称，不直接 import 具体绑定。
"""

from __future__ import annotations

import os

BINDING = os.environ.get("OBOX_QT", "pyside6").strip().lower() or "pyside6"
if BINDING not in ("pyside6", "pyqt5"):
    raise RuntimeError(f"OBOX_QT 只能是 pyside6 或 pyqt5：{BINDING!r}")

if BINDING == "pyside6":
    from PySide6 import QtCore, QtGui, QtNetwork, QtSvg, QtTest, QtWidgets

    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
    QAction = QtGui.QAction
else:
    from PyQt5 import QtCore, QtGui, QtNetwork, QtSvg, QtTest, QtWidgets

    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
    Property = QtCore.pyqtProperty
    QAction = QtWidgets.QAction

Qt = QtCore.Qt
QPointF = QtCore.QPointF

for _module in (QtCore, QtGui, QtWidgets, QtNetwork, QtSvg, QtTest):
    for _name in dir(_module):
        if not _name.startswith("_"):
            globals().setdefault(_name, getattr(_module, _name))

QAction = QtGui.QAction if BINDING == "pyside6" else QtWidgets.QAction


def event_pos(event):
    """鼠标/滚轮事件坐标：Qt6 用 position()，Qt5 用 localPos()。"""
    getter = getattr(event, "position", None) or getattr(event, "localPos", None)
    return QPointF(getter()) if getter is not None else QPointF()


def event_global_pos(event):
    getter = getattr(event, "globalPosition", None) or getattr(event, "globalPos", None)
    return QPointF(getter()) if getter is not None else QPointF()


def icon_pixmap(icon, size, ratio: float = 1.0):
    """按设备像素比取图标：Qt6 有 pixmap(size, ratio)，Qt5 只能取完再设 DPR。"""
    try:
        return icon.pixmap(size, ratio)
    except TypeError:
        pixmap = icon.pixmap(size)
        if ratio and ratio != 1.0 and not pixmap.isNull():
            pixmap.setDevicePixelRatio(ratio)
        return pixmap


def exec_app(app) -> int:
    """统一 exec/exec_ 的差异。"""
    runner = getattr(app, "exec", None) or getattr(app, "exec_")
    return int(runner())


def version() -> str:
    return str(QtCore.qVersion())


__all__ = [
    "BINDING",
    "Qt",
    "QtCore",
    "QtGui",
    "QtNetwork",
    "QtSvg",
    "QtTest",
    "QtWidgets",
    "QAction",
    "Property",
    "Signal",
    "Slot",
    "event_global_pos",
    "icon_pixmap",
    "event_pos",
    "exec_app",
    "version",
]