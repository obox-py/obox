"""布局容器与文本。"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .. import palette
from .base import Component


class DivComponent(Component):
    tag = "div"
    supported_states = ("visible", "enabled")
    state_accessors = {
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        widget = QWidget()
        if attrs.get("width"):
            widget.setFixedWidth(int(attrs["width"]))
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._layout = layout
        return widget

    def container_layout(self) -> QVBoxLayout:
        return self._layout


class TextComponent(Component):
    tag = "text"
    supported_states = ("text", "visible")
    state_accessors = {
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
    }

    def build_widget(self, attrs: dict[str, str]) -> QLabel:
        label = QLabel(attrs.get("text") or attrs.get("children") or "")
        label.setWordWrap(True)
        size = attrs.get("size", "")
        weight = attrs.get("weight", "")
        font = f" font-size: {int(size)}px;" if size else ""
        if weight:
            font += f" font-weight: {int(weight)};"
        label.setStyleSheet(f"color: {palette.TEXT_MUTED};{font}")
        return label

    def text(self) -> str:
        return self.widget.text()

    def set_text(self, value: Any) -> None:
        self.widget.setText(str(value))
