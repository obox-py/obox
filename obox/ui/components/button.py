"""按钮：primary / secondary / ghost / danger 四种外观，自绘底色与过渡。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

from .. import palette
from .base import Component, animate, color

_VARIANTS = ("primary", "secondary", "ghost", "danger")


def _mix(first: QColor, second: QColor, ratio: float) -> QColor:
    ratio = max(0.0, min(1.0, ratio))
    return QColor(
        int(first.red() + (second.red() - first.red()) * ratio),
        int(first.green() + (second.green() - first.green()) * ratio),
        int(first.blue() + (second.blue() - first.blue()) * ratio),
        int(first.alpha() + (second.alpha() - first.alpha()) * ratio),
    )


class ButtonWidget(QAbstractButton):
    def __init__(
        self, text: str, variant: str = "secondary", parent=None, *, primary: bool | None = None
    ) -> None:
        super().__init__(parent)
        self.setText(text)
        if primary is not None:
            variant = "primary" if primary else "secondary"
        self._variant = variant if variant in _VARIANTS else "secondary"
        self._hover = 0.0
        self._press = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumHeight(palette.CONTROL_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def set_variant(self, variant: str) -> None:
        """切换外观变体；浮层用它把主按钮染成对应色。"""
        self._variant = variant if variant in _VARIANTS else "secondary"
        self.update()

    def _get_hover(self) -> float:
        return self._hover

    def _set_hover(self, value: float) -> None:
        self._hover = value
        self.update()

    hover = Property(float, _get_hover, _set_hover)

    def _get_press(self) -> float:
        return self._press

    def _set_press(self, value: float) -> None:
        self._press = value
        self.update()

    press = Property(float, _get_press, _set_press)

    def enterEvent(self, event) -> None:  # noqa: N802
        animate(self, b"hover", self._hover, 1.0, 140)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        animate(self, b"hover", self._hover, 0.0, 160)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        animate(self, b"press", self._press, 1.0, 90)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        animate(self, b"press", self._press, 0.0, 140)
        super().mouseReleaseEvent(event)

    def sizeHint(self) -> QSize:  # noqa: N802
        metrics = self.fontMetrics()
        return QSize(metrics.horizontalAdvance(self.text()) + 36, palette.CONTROL_HEIGHT)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._variant == "primary":
            base, hovered = QColor(color(palette.ACCENT)), _mix(QColor(color(palette.ACCENT)), QColor("#ffffff"), 0.12)
            text_color, border = color(palette.ACCENT_TEXT), None
        elif self._variant == "danger":
            base, hovered = QColor(color(palette.DANGER)), _mix(QColor(color(palette.DANGER)), QColor("#ffffff"), 0.12)
            text_color, border = "#ffffff", None
        elif self._variant == "ghost":
            base, hovered = QColor(0, 0, 0, 0), QColor(color(palette.ACCENT_SOFT))
            text_color, border = color(palette.ACCENT), None
        else:
            base, hovered = QColor(color(palette.SURFACE)), QColor(color(palette.SURFACE_MUTED))
            text_color, border = color(palette.TEXT), color(palette.LINE)
        fill = _mix(base, hovered, self._hover)
        if self._press > 0:
            fill = _mix(fill, QColor("#000000"), 0.08 * self._press)
        rect = QRect(0, 0, self.width() - 1, self.height() - 1)
        painter.setBrush(fill)
        if border is None:
            painter.setPen(Qt.PenStyle.NoPen)
        else:
            painter.setPen(QPen(QColor(border), 1))
        painter.drawRoundedRect(rect, palette.RADIUS_CONTROL, palette.RADIUS_CONTROL)
        if not self.isEnabled():
            painter.setOpacity(0.45)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class ButtonComponent(Component):
    tag = "button"
    supported_states = ("text", "visible", "enabled")
    state_accessors = {
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("click", "contextmenu")
    event_methods = {"click": "on_click", "contextmenu": "on_contextmenu"}

    def build_widget(self, attrs: dict[str, str]) -> ButtonWidget:
        label = attrs.get("text") or attrs.get("children") or ""
        return ButtonWidget(label, variant=attrs.get("type", "secondary"))

    def text(self) -> str:
        return self.widget.text()

    def set_text(self, value: Any) -> None:
        self.widget.setText(str(value))

    def on_click(self, callback) -> None:
        self.widget.clicked.connect(lambda: callback({}))

    def on_contextmenu(self, callback) -> None:
        self.widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.widget.customContextMenuRequested.connect(lambda _pos: callback({}))