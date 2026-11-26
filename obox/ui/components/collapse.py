"""折叠面板：标题可点，展开或收起正文。"""

from __future__ import annotations

from typing import Any

from obox.qt import Qt, Signal
from obox.qt import QColor, QFont, QPainter, QPolygonF
from obox.qt import QPointF
from obox.qt import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .. import palette
from .base import Component


class _Arrow(QWidget):
    """自绘三角箭头，避免字体缺字形。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._open = False
        self.setFixedSize(12, 12)

    def set_open(self, opened: bool) -> None:
        self._open = opened
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(palette.TEXT_MUTED))
        if self._open:
            points = [QPointF(2, 4), QPointF(10, 4), QPointF(6, 9)]
        else:
            points = [QPointF(4, 2), QPointF(9, 6), QPointF(4, 10)]
        painter.drawPolygon(QPolygonF(points))


class _Header(QWidget):
    clicked = Signal()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class CollapseComponent(Component):
    tag = "collapse"
    supported_states = ("open", "title", "visible")
    state_accessors = {
        "open": ("is_open", "set_open"),
        "title": ("title", "set_title"),
        "visible": ("is_visible", "set_visible"),
    }
    supported_events = ("toggle",)
    event_methods = {"toggle": "on_toggle"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._header = _Header(widget)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(0, 10, 0, 6)
        header_layout.setSpacing(8)
        self._title_label = QLabel(attrs.get("title", ""), self._header)
        font = QFont()
        font.setPixelSize(16)
        font.setWeight(QFont.Weight.DemiBold)
        self._title_label.setFont(font)
        self._title_label.setStyleSheet(f"color: {palette.TEXT};")
        self._arrow = _Arrow(self._header)
        header_layout.addWidget(self._title_label, 1)
        header_layout.addWidget(self._arrow)
        outer.addWidget(self._header)

        self._body = QWidget(widget)
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 2)
        self._body_layout.setSpacing(10)
        outer.addWidget(self._body)

        self._open = str(attrs.get("open", "false")).lower() == "true"
        self._header.clicked.connect(self.toggle)
        self._apply()
        return widget

    def container_layout(self) -> QVBoxLayout:
        return self._body_layout

    def _apply(self) -> None:
        self._body.setVisible(self._open)
        self._arrow.set_open(self._open)

    def is_open(self) -> bool:
        return self._open

    def set_open(self, value: Any) -> None:
        self._open = bool(value)
        self._apply()

    def title(self) -> str:
        return self._title_label.text()

    def set_title(self, value: Any) -> None:
        self._title_label.setText(str(value))

    def toggle(self) -> None:
        self._open = not self._open
        self._apply()
        self._emit_toggle()

    def _emit_toggle(self) -> None:
        callback = getattr(self, "_toggle_callback", None)
        if callback is not None:
            callback({"open": self._open})

    def on_toggle(self, callback) -> None:
        self._toggle_callback = callback