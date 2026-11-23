"""单选按钮：自绘圆环与圆点，选中带过渡。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

from .. import palette
from .base import Component, animate, color


class RadioWidget(QAbstractButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._progress = 0.0
        self.toggled.connect(self._fade)

    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, value: float) -> None:
        self._progress = value
        self.update()

    progress = Property(float, _get_progress, _set_progress)

    def _fade(self, checked: bool) -> None:
        animate(self, b"progress", self._progress, 1.0 if checked else 0.0, 140)

    def sizeHint(self) -> QSize:  # noqa: N802
        metrics = self.fontMetrics()
        return QSize(26 + metrics.horizontalAdvance(self.text()) + 6, max(26, metrics.height() + 8))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        circle = QRect(1, (self.height() - 18) // 2, 18, 18)
        fraction = self._progress
        painter.setPen(QPen(color(palette.ACCENT) if fraction > 0.4 else color(palette.LINE), 2 if fraction > 0.4 else 1))
        painter.setBrush(color(palette.SURFACE))
        painter.drawRoundedRect(circle, 2, 2)
        if fraction > 0:
            inset = 9 - 4 * fraction
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color(palette.ACCENT))
            painter.drawRoundedRect(circle.adjusted(inset, inset, -inset, -inset), 1, 1)
        painter.setPen(color(palette.TEXT))
        painter.drawText(
            QRect(26, 0, self.width() - 26, self.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text(),
        )


class RadioComponent(Component):
    tag = "radio"
    supported_states = ("checked", "text", "visible", "enabled")
    state_accessors = {
        "checked": ("checked", "set_checked"),
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("checkedchange",)
    event_methods = {"checkedchange": "on_checkedchange"}

    def build_widget(self, attrs: dict[str, str]) -> RadioWidget:
        widget = RadioWidget(attrs.get("text") or attrs.get("children") or "")
        checked = attrs.get("checked", "").lower() == "true"
        widget.setChecked(checked)
        widget._progress = 1.0 if checked else 0.0
        return widget

    def checked(self) -> bool:
        return self.widget.isChecked()

    def set_checked(self, value: Any) -> None:
        self.widget.setChecked(bool(value))

    def text(self) -> str:
        return self.widget.text()

    def set_text(self, value: Any) -> None:
        self.widget.setText(str(value))

    def on_checkedchange(self, callback) -> None:
        self.widget.toggled.connect(lambda state: callback({"checked": state}))