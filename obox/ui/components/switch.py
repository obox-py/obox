"""开关：自绘轨道与滑块，切换带滑动过渡。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

from .. import palette
from .base import Component, animate, color


class SwitchWidget(QAbstractButton):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._knob = 0.0
        self.toggled.connect(self._slide)

    def _get_knob(self) -> float:
        return self._knob

    def _set_knob(self, value: float) -> None:
        self._knob = value
        self.update()

    knob = Property(float, _get_knob, _set_knob)

    def _slide(self, checked: bool) -> None:
        animate(self, b"knob", self._knob, 1.0 if checked else 0.0, 170)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(36, 20)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        idle = QColor(color(palette.TEXT_MUTED))
        idle.setAlpha(70)
        active = QColor(color(palette.ACCENT))
        fraction = self._knob
        track = QColor(
            int(idle.red() + (active.red() - idle.red()) * fraction),
            int(idle.green() + (active.green() - idle.green()) * fraction),
            int(idle.blue() + (active.blue() - idle.blue()) * fraction),
            int(idle.alpha() + (active.alpha() - idle.alpha()) * fraction),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track)
        radius = self.height() / 2
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), radius, radius)
        knob = max(12.0, self.height() - 4.0)
        x = 2 + (self.width() - knob - 4) * fraction
        painter.setBrush(color(palette.SURFACE))
        painter.drawEllipse(QRectF(x, (self.height() - knob) / 2, knob, knob))


class SwitchComponent(Component):
    tag = "switch"
    supported_states = ("checked", "visible", "enabled")
    state_accessors = {
        "checked": ("checked", "set_checked"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("checkedchange",)
    event_methods = {"checkedchange": "on_checkedchange"}

    def build_widget(self, attrs: dict[str, str]) -> SwitchWidget:
        widget = SwitchWidget()
        widget.setChecked(attrs.get("checked", "").lower() == "true")
        widget._knob = 1.0 if widget.isChecked() else 0.0
        return widget

    def checked(self) -> bool:
        return self.widget.isChecked()

    def set_checked(self, value: Any) -> None:
        self.widget.setChecked(bool(value))

    def on_checkedchange(self, callback) -> None:
        self.widget.toggled.connect(lambda state: callback({"checked": state}))