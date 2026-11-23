"""通知：自绘浮层，显示若干秒后自动收起。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget

from .base import Component, animate


class Toast(QFrame):
    closed = Signal()

    def __init__(self, host: QWidget, text: str, duration: int = 3000) -> None:
        super().__init__(host)
        self.setObjectName("obox-toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        label = QLabel(text, self)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.adjustSize()
        self.setFixedWidth(320)
        window = host.window()
        title = window.findChild(QWidget, "obox-titlebar")
        top = title.height() if title is not None else 0
        self.move(window.width() - self.width() - 20, top + 20)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self.show()
        self.raise_()
        animate(self._effect, b"opacity", 0.0, 1.0, 180)
        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self) -> None:
        animation = animate(self._effect, b"opacity", 1.0, 0.0, 220)
        animation.finished.connect(self.close)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.closed.emit()
        super().closeEvent(event)



class NotificationComponent(Component):
    tag = "notification"
    supported_states = ("visible", "text")
    state_accessors = {
        "visible": ("is_visible", "set_visible"),
        "text": ("text", "set_text"),
    }
    supported_events = ("close",)
    event_methods = {"close": "on_close"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        self._text = attrs.get("text") or attrs.get("children") or ""
        self._title = attrs.get("title", "obox")
        self._host: QWidget | None = None
        self._open = False
        self._callbacks: list = []
        self._toast: Toast | None = None
        placeholder = QWidget()
        placeholder.hide()
        return placeholder

    def attach(self, host: QWidget) -> None:
        self._host = host

    def detach(self) -> None:
        if self._toast is not None:
            self._toast.close()
            self._toast = None
        self._open = False

    def text(self) -> str:
        return self._text

    def set_text(self, value: Any) -> None:
        self._text = str(value)

    def is_visible(self) -> bool:
        return self._open

    def set_visible(self, value: Any) -> None:
        if not bool(value) or self._host is None or self._open:
            return
        self._open = True
        self._toast = Toast(self._host.window(), self._text)
        self._toast.closed.connect(self._on_closed)

    def on_close(self, callback) -> None:
        self._callbacks.append(callback)

    def _on_closed(self) -> None:
        self._open = False
        self._toast = None
        for callback in self._callbacks:
            callback({})
