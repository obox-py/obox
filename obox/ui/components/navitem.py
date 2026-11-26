"""侧栏导航项：纯文本行，选中态用强调色与左侧竖条。"""

from __future__ import annotations

from typing import Any

from obox.qt import QRect, Qt, Signal
from obox.qt import QPainter
from obox.qt import QWidget

from .. import palette
from .base import Component, color


class NavItemWidget(QWidget):
    clicked = Signal()

    def __init__(self, text: str, selected: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self._selected = selected
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRect(0, 0, self.width(), self.height())
        if self._selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color(palette.ACCENT_SOFT))
            painter.drawRoundedRect(rect, palette.RADIUS_CONTROL, palette.RADIUS_CONTROL)
            painter.setBrush(color(palette.ACCENT))
            painter.drawRoundedRect(QRect(0, 6, 3, self.height() - 12), 1, 1)
        elif self.underMouse():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color(palette.SURFACE_MUTED))
            painter.drawRoundedRect(rect, palette.RADIUS_CONTROL, palette.RADIUS_CONTROL)
        painter.setPen(color(palette.ACCENT) if self._selected else color(palette.TEXT if self.underMouse() else palette.TEXT_MUTED))
        painter.drawText(QRect(14, 0, self.width() - 18, self.height()), Qt.AlignmentFlag.AlignVCenter, self._text)

    def set_selected(self, value: bool) -> None:
        self._selected = value
        self.update()

    def text(self) -> str:
        return self._text

    def set_text(self, value: str) -> None:
        self._text = value
        self.update()


class NavItemComponent(Component):
    tag = "navitem"
    supported_states = ("text", "selected", "visible")
    state_accessors = {
        "text": ("text", "set_text"),
        "selected": ("is_selected", "set_selected"),
        "visible": ("is_visible", "set_visible"),
    }
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def build_widget(self, attrs: dict[str, str]) -> NavItemWidget:
        widget = NavItemWidget(attrs.get("text") or attrs.get("children") or "", attrs.get("selected", "").lower() == "true")
        widget.setProperty("nav_value", attrs.get("value", ""))
        widget.setToolTip(attrs.get("text", ""))
        return widget

    def text(self) -> str:
        return self.widget.text()

    def set_text(self, value: Any) -> None:
        self.widget.set_text(str(value))

    def is_selected(self) -> bool:
        return self.widget._selected

    def set_selected(self, value: Any) -> None:
        self.widget.set_selected(bool(value))

    def on_click(self, callback) -> None:
        self.widget.clicked.connect(lambda: callback({"value": str(self.widget.property("nav_value") or "")}))