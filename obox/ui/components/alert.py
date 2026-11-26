"""提醒条：半透明浅色底 + 白色文字，可配 top/bottom 与 offset。"""

from __future__ import annotations

from typing import Any

from obox.qt import QEvent, QObject, Qt
from obox.qt import QColor
from obox.qt import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from .. import palette
from .base import Component, animate

_TYPES = {
    "info": ("#eaf1fe", "#2f6bee", "i"),
    "warn": ("#fff7e6", "#ff9a2e", "!"),
    "error": ("#fde8e7", "#d93026", "×"),
}
_POSITIONS = {"top", "bottom"}


class _Watcher(QObject):
    """宿主窗口改尺寸时重新摆放。"""

    def __init__(self, reposition) -> None:
        super().__init__()
        self._reposition = reposition

    def eventFilter(self, watched, event):  # noqa: N802 - Qt 接口
        if event.type() == QEvent.Type.Resize:
            self._reposition()
        return False


class AlertComponent(Component):
    tag = "alert"
    supported_states = ("visible", "text")
    state_accessors = {
        "visible": ("is_visible", "set_visible"),
        "text": ("text", "set_text"),
    }
    supported_events: tuple[str, ...] = ()
    event_methods: dict[str, str] = {}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        kind = attrs.get("type", "info")
        if kind not in _TYPES:
            raise ValueError(f"type 取值非法：{kind}；可选：info、warn、error")
        position = attrs.get("position", "top")
        if position not in _POSITIONS:
            raise ValueError(f"position 取值非法：{position}；可选：top、bottom")
        self._position = position
        self._offset = int(attrs.get("offset", "24"))
        self._text = attrs.get("text", "")
        background, accent, glyph = _TYPES[kind]

        widget = QWidget()
        widget.setObjectName(self.id)
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        badge = QLabel(glyph, widget)
        badge.setFixedSize(20, 20)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background: {accent}; color: #ffffff; border-radius: 2px;"
            " font-size: 12px; font-weight: 700;"
        )
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        self._label = QLabel(self._text, widget)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(f"color: {palette.TEXT}; font-size: 14px; background: transparent;")
        shadow = QGraphicsDropShadowEffect(self._label)
        shadow.setBlurRadius(6)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 1)
        self._label.setGraphicsEffect(shadow)
        layout.addWidget(self._label, 1)

        widget.setStyleSheet(
            f"#{self.id} {{ background: {background}; border: 1px solid {accent}; border-radius: 2px; }}"
        )
        self._effect = QGraphicsOpacityEffect(widget)
        self._effect.setOpacity(0.0)
        widget.setGraphicsEffect(self._effect)
        widget.hide()
        self._watcher: _Watcher | None = None
        return widget

    def attach(self, host: QWidget) -> None:
        self._host = host
        self._watcher = _Watcher(self._reposition)
        self._ensure_parent()

    def _ensure_parent(self) -> None:
        """挂到当前顶层窗口；视图后来才进窗口时在显示前纠正一次。"""
        host = getattr(self, "_host", None)
        if host is None:
            return
        window = host.window()
        if self.widget.parentWidget() is not window:
            self.widget.setParent(window)
            if self._watcher is not None:
                window.installEventFilter(self._watcher)
        self._reposition()

    def detach(self) -> None:
        self.widget.hide()
        parent = self.widget.parentWidget()
        if self._watcher is not None and parent is not None:
            parent.removeEventFilter(self._watcher)
        self._watcher = None
        self.widget.setParent(None)
        self.widget.deleteLater()

    def _reposition(self) -> None:
        window = self.widget.parentWidget()
        if window is None:
            return
        width = max(window.width() - 32, 200)
        height = max(52, self._label.sizeHint().height() + 26)
        x = (window.width() - width) // 2
        title = window.findChild(QWidget, "obox-titlebar")
        top_inset = title.height() if title is not None else 0
        bar = window.findChild(QWidget, "obox-bottom")
        bottom_inset = bar.height() if bar is not None and bar.isVisible() else 0
        if self._position == "bottom":
            y = window.height() - height - bottom_inset - self._offset
        else:
            y = top_inset + self._offset
        self.widget.setGeometry(x, y, width, height)

    def set_visible(self, value: Any) -> None:
        if bool(value):
            self._ensure_parent()
            self._effect.setOpacity(0.0)
            self.widget.show()
            self.widget.raise_()
            animate(self._effect, b"opacity", 0.0, 1.0, 200)
        else:
            self.widget.hide()

    def is_visible(self) -> bool:
        return self.widget.isVisible()

    def text(self) -> str:
        return self._text

    def set_text(self, value: Any) -> None:
        self._text = str(value)
        self._label.setText(self._text)
        self._reposition()