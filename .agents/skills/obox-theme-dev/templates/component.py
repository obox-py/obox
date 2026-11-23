"""__TITLE__：__TAG__ 组件。"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget

from .base import Component
from ..theme import CONTROL_HEIGHT, RADIUS_CONTROL, SURFACE, TEXT


class __CLASS__(Component):
    tag = "__TAG__"
    supported_states = ("text", "visible")
    state_accessors = {
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
    }
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        widget = QWidget()
        widget.setFixedHeight(CONTROL_HEIGHT)
        widget.setStyleSheet(f"border-radius: {RADIUS_CONTROL}px; background: {SURFACE}; color: {TEXT};")
        self._text = attrs.get("text") or attrs.get("children") or ""
        return widget

    def text(self) -> str:
        return self._text

    def set_text(self, value: Any) -> None:
        self._text = str(value)

    def on_click(self, callback) -> None:
        self.widget.mousePressEvent = lambda event: callback({})
