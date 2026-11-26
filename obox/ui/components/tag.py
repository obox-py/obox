"""标签：自绘胶囊。"""

from __future__ import annotations

from typing import Any

from obox.qt import QLabel, QSizePolicy

from .. import palette
from .base import Component


class TagComponent(Component):
    tag = "tag"
    supported_states = ("text", "visible")
    state_accessors = {
        "text": ("text", "set_text"),
        "visible": ("is_visible", "set_visible"),
    }

    def build_widget(self, attrs: dict[str, str]) -> QLabel:
        label = QLabel(attrs.get("text") or attrs.get("children") or "")
        label.setContentsMargins(10, 2, 10, 2)
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        kind = attrs.get("type", "tag")
        if kind == "label":
            label.setStyleSheet(
                f"border-radius: 2px; padding: 1px 8px; background: {palette.SURFACE_MUTED}; color: {palette.TEXT_MUTED};"
            )
        else:
            label.setStyleSheet(
                f"border-radius: 2px; padding: 1px 8px; background: {palette.ACCENT}; color: {palette.ACCENT_TEXT};"
            )
        return label

    def text(self) -> str:
        return self.widget.text()

    def set_text(self, value: Any) -> None:
        self.widget.setText(str(value))