"""下拉选择：QComboBox + 自绘箭头。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QComboBox

from .. import palette
from .base import Component, border_css, color


class ComboBox(QComboBox):
    """默认箭头依赖原生样式，深色主题下不可见，这里自己画一个。"""

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color(palette.TEXT_MUTED), 1.6))
        x = self.width() - 20
        y = self.height() / 2 - 2
        painter.drawPolyline([QPointF(x, y), QPointF(x + 5, y + 5), QPointF(x + 10, y)])


class SelectComponent(Component):
    tag = "select"
    supported_states = ("value", "visible", "enabled")
    state_accessors = {
        "value": ("value", "set_value"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("change",)
    event_methods = {"change": "on_change"}

    def build_widget(self, attrs: dict[str, str]) -> QComboBox:
        widget = ComboBox()
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        items = [item.strip() for item in attrs.get("options", "").split(",") if item.strip()]
        if items:
            widget.addItems(items)
        current = attrs.get("value", "")
        if current and current in items:
            widget.setCurrentText(current)
        widget.setMinimumHeight(palette.CONTROL_HEIGHT)
        widget.setStyleSheet(border_css(attrs, "all", palette.LINE))
        return widget

    def value(self) -> str:
        return self.widget.currentText()

    def set_value(self, value: Any) -> None:
        self.widget.setCurrentText(str(value))

    def on_change(self, callback) -> None:
        self.widget.currentTextChanged.connect(lambda text: callback({"value": text}))
