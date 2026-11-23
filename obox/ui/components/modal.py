"""模态浮层：遮罩 + 居中面板，正文放任意组件，直接子级的按钮进底部。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent, QObject, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import palette
from .base import Component, animate
from .button import ButtonWidget

_VARIANTS = {
    "info": ("i", palette.ACCENT),
    "confirm": ("i", palette.ACCENT),
    "danger": ("!", palette.DANGER),
}
_MIN_WIDTH = 320
_MIN_HEIGHT = 160
_DEFAULT_WIDTH = 420
_HANDLE = 16
_MAX_RATIO = 0.92
_RATIO = 0.9


class _HostWatcher(QObject):
    """宿主窗口改尺寸时重设覆盖层几何。"""

    def __init__(self, on_resize) -> None:
        super().__init__()
        self._on_resize = on_resize

    def eventFilter(self, watched, event):  # noqa: N802 - Qt 接口
        if event.type() == QEvent.Type.Resize:
            self._on_resize()
        return False


class ModalOverlay(QFrame):
    """覆盖层：Esc 与点遮罩转交组件判定。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("obox-modal-overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.handler = None

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(15, 23, 42, 76))
        super().paintEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if self.handler is not None and self.handler.handle_key(event):
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.handler is not None
            and self.handler.handle_overlay_click(event.position())
        ):
            return
        super().mousePressEvent(event)


class ModalCard(QFrame):
    """面板：底色与描边由套件 QSS 给，右下角 16x16 热区可拖拽改尺寸。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("obox-modal-card")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self._resizing = False
        self._origin = QPointF()
        self._start = (0, 0)

    def _in_handle(self, position: QPointF) -> bool:
        return (
            position.x() >= self.width() - _HANDLE
            and position.y() >= self.height() - _HANDLE
        )

    def _bounds(self) -> tuple[int, int]:
        window = self.window()
        return int(window.width() * _RATIO), int(window.height() * _RATIO)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if event.button() == Qt.MouseButton.LeftButton and self._in_handle(event.position()):
            self._resizing = True
            self._origin = event.globalPosition()
            self._start = (self.width(), self.height())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if self._resizing:
            delta = event.globalPosition() - self._origin
            max_width, max_height = self._bounds()
            width = max(_MIN_WIDTH, min(max_width, int(self._start[0] + delta.x())))
            height = max(_MIN_HEIGHT, min(max_height, int(self._start[1] + delta.y())))
            self.setFixedSize(width, height)
            event.accept()
            return
        self.setCursor(
            Qt.CursorShape.SizeFDiagCursor
            if self._in_handle(event.position())
            else Qt.CursorShape.ArrowCursor
        )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if self._resizing:
            self._resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(palette.TEXT_MUTED)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        right, bottom = self.width() - 4.0, self.height() - 4.0
        for offset in (0.0, 4.0, 8.0):
            painter.drawLine(QPointF(right - offset, bottom), QPointF(right, bottom - offset))


class _MaxButton(QWidget):
    """标题栏右侧的放大/还原按钮（自绘，不依赖字形）。"""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._max = False
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_maximized(self, value: bool) -> None:
        self._max = value
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(palette.TEXT_MUTED)
        pen.setWidthF(1.2)
        painter.setPen(pen)
        if self._max:
            painter.drawRect(4, 7, 9, 8)
            painter.drawRect(8, 4, 9, 8)
        else:
            painter.drawRect(4, 4, 13, 13)


class ModalSlot(QVBoxLayout):
    """装配槽：直接子级的按钮进底部，其余进正文。"""

    def __init__(self, body: QVBoxLayout, footer: QHBoxLayout, on_button) -> None:
        super().__init__()
        self._body = body
        self._footer = footer
        self._on_button = on_button

    def addWidget(self, widget: QWidget) -> None:  # noqa: N802 - Qt 接口
        if isinstance(widget, ButtonWidget):
            self._footer.addWidget(widget)
            widget.clicked.connect(lambda _checked=False, w=widget: self._on_button(w))
        else:
            self._body.addWidget(widget)


class ModalComponent(Component):
    tag = "modal"
    supported_states = ("visible", "text")
    state_accessors = {
        "visible": ("is_visible", "set_visible"),
        "text": ("text", "set_text"),
    }
    supported_events = ("close",)
    event_methods = {"close": "on_close"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        self._text = attrs.get("text") or attrs.get("children") or ""
        variant = attrs.get("variant", "info")
        if variant not in _VARIANTS:
            raise ValueError(f"variant 取值非法：{variant}；可选：info、confirm、danger")
        self._variant = variant
        self._close_on_esc = (attrs.get("close_on_esc", "true").lower() == "true")
        self._close_on_overlay = (attrs.get("close_on_overlay", "false").lower() == "true")
        self._wanted_width = attrs.get("width") or str(_DEFAULT_WIDTH)
        self._wanted_height = attrs.get("height") or ""
        self._callbacks: list = []
        self._maximized = False
        self._saved_size = None
        self._mounted = False
        self._fallback_done = False
        self._variant_done = False
        self._fallback_label: QLabel | None = None
        self._host: QWidget | None = None
        self._watcher: _HostWatcher | None = None

        overlay = ModalOverlay()
        overlay.handler = self
        self._outer = QVBoxLayout(overlay)
        self._outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = ModalCard(overlay)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 18, 0, 16)
        card_layout.setSpacing(16)

        title_holder = QWidget(card)
        title_row = QHBoxLayout(title_holder)
        title_row.setContentsMargins(22, 0, 22, 0)
        title_row.setSpacing(8)
        glyph, accent = _VARIANTS[variant]
        badge = QLabel(glyph, card)
        badge.setFixedSize(16, 16)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background: {accent}; color: #ffffff; border-radius: 2px;"
            " font-size: 11px; font-weight: 700;"
        )
        title_row.addWidget(badge)
        title = QLabel(attrs.get("title", "提示"), card)
        title.setObjectName("obox-modal-title")
        title_row.addWidget(title)
        title_row.addStretch(1)
        self._max_button = _MaxButton(title_holder)
        self._max_button.clicked.connect(self.toggle_maximize)
        title_row.addWidget(self._max_button)
        card_layout.addWidget(title_holder)

        area = QScrollArea(card)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setStyleSheet("background: transparent;")
        area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        body = QVBoxLayout(content)
        body.setContentsMargins(22, 0, 22, 0)
        body.setSpacing(14)
        area.setWidget(content)
        card_layout.addWidget(area, 1)

        footer_holder = QWidget(card)
        footer = QHBoxLayout(footer_holder)
        footer.setContentsMargins(22, 0, 22, 0)
        footer.setSpacing(12)
        footer.addStretch(1)
        card_layout.addWidget(footer_holder)

        self._card = card
        self._body = body
        self._footer = footer
        self._slot = ModalSlot(body, footer, lambda widget: self._close("button", widget.text()))
        self._outer.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

        self._effect = QGraphicsOpacityEffect(overlay)
        self._effect.setOpacity(0.0)
        overlay.setGraphicsEffect(self._effect)
        overlay.hide()
        return overlay

    def container_layout(self) -> QVBoxLayout:
        return self._slot

    def attach(self, host: QWidget) -> None:
        self._host = host

    def detach(self) -> None:
        self.widget.hide()
        parent = self.widget.parentWidget()
        if self._watcher is not None and parent is not None:
            parent.removeEventFilter(self._watcher)
        self._watcher = None
        self._mounted = False
        self.widget.setParent(None)
        self.widget.deleteLater()

    def text(self) -> str:
        return self._text

    def set_text(self, value: Any) -> None:
        self._text = str(value)
        if self._fallback_label is not None:
            self._fallback_label.setText(self._text)

    def set_visible(self, value: Any) -> None:
        if bool(value):
            window = self._mount()
            if window is None:
                return
            self._apply_size(window)
            self._apply_margins(self._card.width())
            self.widget.setGeometry(window.rect())
            self._ensure_fallback()
            self._apply_variant_color()
            self._effect.setOpacity(0.0)
            self.widget.show()
            self.widget.raise_()
            self.widget.setFocus(Qt.FocusReason.OtherFocusReason)
            animate(self._effect, b"opacity", 0.0, 1.0, 160)
        else:
            self.widget.hide()

    def _mount(self) -> QWidget | None:
        host = self._host
        if host is None:
            return None
        window = host.window()
        if not self._mounted:
            self.widget.setParent(window)
            self._watcher = _HostWatcher(self._on_host_resize)
            window.installEventFilter(self._watcher)
            self._mounted = True
        return window

    def _on_host_resize(self) -> None:
        host = self._host
        window = host.window() if host is not None else None
        if window is None:
            return
        self.widget.setGeometry(window.rect())
        if self._maximized:
            self._card.setFixedSize(
                int(window.width() * _MAX_RATIO), int(window.height() * _MAX_RATIO)
            )
            return
        max_width = int(window.width() * _RATIO)
        width = max(_MIN_WIDTH, min(max_width, self._card.width() or int(self._wanted_width)))
        self._card.setFixedWidth(width)
        self._apply_margins(width)

    def _apply_margins(self, width: int) -> None:
        if width < 460:
            side = 14
        else:
            side = max(22, (width - 720) // 2)
        self._body.setContentsMargins(side, 0, side, 0)
        for layout in (self._footer.layout(),):
            if layout is not None:
                layout.setContentsMargins(side, 0, side, 0)

    def toggle_maximize(self) -> None:
        host = self._host
        window = host.window() if host is not None else None
        if window is None:
            return
        if self._maximized:
            self._maximized = False
            self._max_button.set_maximized(False)
            if self._saved_size is not None:
                self._card.setFixedSize(*self._saved_size)
            else:
                self._apply_size(window)
            self._apply_margins(self._card.width())
            return
        self._saved_size = (self._card.width(), self._card.height())
        self._maximized = True
        self._max_button.set_maximized(True)
        self._card.setFixedSize(
            int(window.width() * _MAX_RATIO), int(window.height() * _MAX_RATIO)
        )
        self._apply_margins(self._card.width())

    def _apply_size(self, window: QWidget) -> None:
        max_width = int(window.width() * _RATIO)
        max_height = int(window.height() * _RATIO)
        width = max(_MIN_WIDTH, min(max_width, int(self._wanted_width)))
        if self._wanted_height:
            height = max(_MIN_HEIGHT, min(max_height, int(self._wanted_height)))
            self._card.setFixedSize(width, height)
        else:
            self._card.setFixedWidth(width)
            self._card.setMinimumHeight(_MIN_HEIGHT)
            self._card.setMaximumHeight(max_height)

    def _ensure_fallback(self) -> None:
        if self._fallback_done:
            return
        self._fallback_done = True
        if self._body.count() or self._footer.count() > 1:
            return
        self._fallback_label = QLabel(self._text)
        self._fallback_label.setObjectName("obox-modal-body")
        self._fallback_label.setWordWrap(True)
        self._body.addWidget(self._fallback_label)
        button = ButtonWidget("知道了", variant="secondary")
        button.clicked.connect(lambda _checked=False: self._close("button", button.text()))
        self._footer.addWidget(button)

    def _apply_variant_color(self) -> None:
        if self._variant_done:
            return
        self._variant_done = True
        target = {"confirm": "primary", "danger": "danger"}.get(self._variant)
        if target is None:
            return
        for index in range(self._footer.count() - 1, -1, -1):
            item = self._footer.itemAt(index)
            widget = item.widget() if item is not None else None
            if isinstance(widget, ButtonWidget):
                widget.set_variant(target)
                return

    def _close(self, reason: str, value: str) -> None:
        self.widget.hide()
        for callback in self._callbacks:
            callback({"reason": reason, "value": value})

    def handle_key(self, event) -> bool:
        if event.key() == Qt.Key.Key_Escape and self._close_on_esc:
            self._close("esc", "")
            return True
        return False

    def handle_overlay_click(self, position) -> bool:
        if self._close_on_overlay and not self._card.geometry().contains(position.toPoint()):
            self._close("overlay", "")
            return True
        return False

    def on_close(self, callback) -> None:
        self._callbacks.append(callback)