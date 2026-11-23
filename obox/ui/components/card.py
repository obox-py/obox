"""卡片：可选中的容器，内部放任意自定义组件。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .. import palette
from .base import Component, color


class CardWidget(QWidget):
    """被点击时发信号；背景与描边自己画，避免 id 里带点导致 QSS 选择器失配。"""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._selected = False

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 按设备像素对齐：内缩半个设备像素，cosmetic 1 设备像素描边
        dpr = self.devicePixelRatioF() or 1.0
        # 让描边中心落在整数设备像素上，两侧抗锯齿对称，四边观感一致
        inset = round(0.5 * dpr) / dpr
        rect = QRectF(inset, inset, self.width() - 2 * inset, self.height() - 2 * inset)
        fill = color(palette.ACCENT_SOFT) if self._selected else color(palette.CARD_SURFACE)
        border = color(palette.ACCENT) if (self._selected or self.underMouse()) else color(palette.CARD_BORDER)
        pen = QPen(border)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, palette.RADIUS_CARD, palette.RADIUS_CARD)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.update()


class CardComponent(Component):
    """卡片：内容自定义；独立使用时可用 click 事件，放进 Choice 时复用选中逻辑。"""

    tag = "card"
    supported_states: tuple[str, ...] = ()
    state_accessors: dict[str, tuple[str, str]] = {}
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def __init__(self, component_id: str, owner: str, attrs: dict[str, str]) -> None:
        super().__init__(component_id, owner, attrs)
        self.widget.setProperty("card_value", attrs.get("value") or component_id)
        self.widget.set_selected(False)

    def build_widget(self, attrs: dict[str, str]) -> CardWidget:
        widget = CardWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(6)
        self._layout = layout
        return widget

    def container_layout(self) -> QVBoxLayout:
        return self._layout

    def set_selected(self, selected: bool) -> None:
        self.widget.set_selected(selected)

    def on_click(self, callback) -> None:
        self.widget.clicked.connect(lambda: callback({"value": card_value(self.widget)}))


def card_value(widget: QWidget) -> str:
    return str(widget.property("card_value") or widget.objectName())