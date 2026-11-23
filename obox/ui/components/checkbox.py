"""复选框：自绘方框与对勾，勾选带过渡。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

from .. import palette
from .base import Component, animate, color


class CheckBoxWidget(QAbstractButton):
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
        box = QRect(1, (self.height() - 18) // 2, 18, 18)
        fraction = self._progress
        idle = QColor(color(palette.SURFACE))
        active = QColor(color(palette.ACCENT))
        fill = QColor(
            int(idle.red() + (active.red() - idle.red()) * fraction),
            int(idle.green() + (active.green() - idle.green()) * fraction),
            int(idle.blue() + (active.blue() - idle.blue()) * fraction),
        )
        border = QColor(color(palette.LINE))
        painter.setPen(QPen(border if fraction < 0.5 else active, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(box, 2, 2)
        if fraction > 0:
            painter.setOpacity(fraction)
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(box.left() + 4, box.center().y(), box.center().x() - 1, box.bottom() - 5)
            painter.drawLine(box.center().x() - 1, box.bottom() - 5, box.right() - 4, box.top() + 5)
            painter.setOpacity(1.0)
        painter.setPen(color(palette.TEXT))
        painter.drawText(
            QRect(26, 0, self.width() - 26, self.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text(),
        )


class CheckboxComponent(Component):
    tag = "checkbox"
    supported_states = ("checked", "text", "visible", "enabled")
    state_accessors = {
        "checked": ("checked", "set_checked"),
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("checkedchange", "click")
    event_methods = {"checkedchange": "on_checkedchange", "click": "on_click"}

    def build_widget(self, attrs: dict[str, str]) -> CheckBoxWidget:
        widget = CheckBoxWidget(attrs.get("text") or attrs.get("children") or "")
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

    def on_click(self, callback) -> None:
        self.widget.clicked.connect(lambda: callback({}))