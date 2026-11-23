"""单行与多行输入：QLineEdit / QTextEdit。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QLineEdit, QTextEdit

from .. import palette
from .base import Component, border_css


class _FocusFilter(QObject):
    """把获得焦点与失去焦点转成回调；由组件持有引用防止被回收。"""

    def __init__(self, callback, on_focus: bool) -> None:
        super().__init__()
        self._callback = callback
        self._on_focus = on_focus

    def eventFilter(self, _obj, event) -> bool:  # noqa: N802 - Qt 接口
        if self._on_focus and event.type() == QEvent.Type.FocusIn:
            self._callback({})
        if not self._on_focus and event.type() == QEvent.Type.FocusOut:
            self._callback({})
        return False


class InputComponent(Component):
    tag = "input"
    supported_states = ("value", "readonly", "visible", "enabled")
    state_accessors = {
        "value": ("text", "set_text"),
        "readonly": ("is_readonly", "set_readonly"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("input", "change", "focus", "blur")
    event_methods = {
        "input": "on_input",
        "change": "on_change",
        "focus": "on_focused",
        "blur": "on_blurred",
    }

    def build_widget(self, attrs: dict[str, str]) -> QLineEdit:
        widget = QLineEdit()
        widget.setPlaceholderText(attrs.get("placeholder", ""))
        widget.setText(attrs.get("value", ""))
        if str(attrs.get("password", "")).lower() == "true":
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        widget.setClearButtonEnabled(True)
        widget.setMinimumHeight(palette.CONTROL_HEIGHT)
        widget.setStyleSheet(border_css(attrs, "all", palette.INPUT_BORDER) + f"border-radius: {palette.RADIUS_CONTROL}px;")
        self._filters: list[_FocusFilter] = []
        return widget

    def text(self) -> str:
        return self.widget.text()

    def set_text(self, value: Any) -> None:
        self.widget.setText(str(value))

    def is_readonly(self) -> bool:
        return self.widget.isReadOnly()

    def set_readonly(self, value: Any) -> None:
        self.widget.setReadOnly(bool(value))

    def on_input(self, callback) -> None:
        self.widget.textEdited.connect(lambda text: callback({"value": text}))

    def on_change(self, callback) -> None:
        self.widget.textChanged.connect(lambda text: callback({"value": text}))

    def on_focused(self, callback) -> None:
        self._install_focus_filter(callback, True)

    def on_blurred(self, callback) -> None:
        self._install_focus_filter(callback, False)

    def _install_focus_filter(self, callback, on_focus: bool) -> None:
        event_filter = _FocusFilter(callback, on_focus)
        self._filters.append(event_filter)
        self.widget.installEventFilter(event_filter)


class TextAreaComponent(Component):
    tag = "textarea"
    supported_states = ("value", "text", "visible", "enabled")
    state_accessors = {
        "value": ("text", "set_text"),
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("change",)
    event_methods = {"change": "on_change"}

    def build_widget(self, attrs: dict[str, str]) -> QTextEdit:
        widget = QTextEdit()
        widget.setPlainText(attrs.get("value", ""))
        widget.setFixedHeight(int(attrs.get("height", "96")))
        widget.setStyleSheet(border_css(attrs, "all", palette.INPUT_BORDER) + f"border-radius: {palette.RADIUS_CONTROL}px;")
        return widget

    def text(self) -> str:
        return self.widget.toPlainText()

    def set_text(self, value: Any) -> None:
        self.widget.setPlainText(str(value))

    def on_change(self, callback) -> None:
        self.widget.textChanged.connect(lambda: callback({"value": self.text()}))