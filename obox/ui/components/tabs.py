"""页签：自绘按钮条 + 内容区。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .base import Component


class TabBar(QWidget):
    """按钮条；同一时刻只有一个按钮处于选中态。"""

    currentItemChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(24)
        self._layout.addStretch(1)
        self._buttons: dict[str, QPushButton] = {}
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def addItem(self, routeKey: str, text: str) -> None:  # noqa: N802 - 保持原接口
        button = QPushButton(text, self)
        button.setObjectName("obox-tab")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: self.currentItemChanged.emit(routeKey))
        self._layout.insertWidget(self._layout.count() - 1, button)
        self._buttons[routeKey] = button
        if len(self._buttons) == 1:
            button.setChecked(True)

    def currentRouteKey(self) -> str:  # noqa: N802
        for key, button in self._buttons.items():
            if button.isChecked():
                return key
        return ""

    def setCurrentItem(self, routeKey: str) -> None:  # noqa: N802
        button = self._buttons.get(routeKey)
        if button is None:
            return
        button.setChecked(True)
        self.currentItemChanged.emit(routeKey)


class TabsComponent(Component):
    tag = "tabs"
    supported_states = ("value", "visible")
    state_accessors = {
        "value": ("value", "set_value"),
        "visible": ("is_visible", "set_visible"),
    }
    supported_events = ("change",)
    event_methods = {"change": "on_change"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._bar = TabBar(widget)
        self._content = QWidget(widget)
        layout.addWidget(self._bar)
        layout.addWidget(self._content, 1)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        items = [item.strip() for item in attrs.get("items", "").split(",") if item.strip()]
        for index, item in enumerate(items):
            self._bar.addItem(f"tab-{index}", item)
        return widget

    def container_layout(self):
        return self._content_layout

    def value(self) -> str:
        return self._bar.currentRouteKey()

    def set_value(self, value: Any) -> None:
        self._bar.setCurrentItem(str(value))

    def on_change(self, callback) -> None:
        self._bar.currentItemChanged.connect(lambda key: callback({"value": key}))
