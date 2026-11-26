"""滑块：QSlider + QSS。"""

from __future__ import annotations

from typing import Any

from obox.qt import Qt
from obox.qt import QSlider

from .base import Component


class SliderComponent(Component):
    tag = "slider"
    supported_states = ("value", "visible", "enabled")
    state_accessors = {
        "value": ("value", "set_value"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("change",)
    event_methods = {"change": "on_change"}

    def build_widget(self, attrs: dict[str, str]) -> QSlider:
        widget = QSlider(Qt.Orientation.Horizontal)
        widget.setFixedHeight(32)
        widget.setRange(int(attrs.get("min", "0")), int(attrs.get("max", "100")))
        widget.setValue(int(attrs.get("value", "0")))
        widget.setMinimumWidth(160)
        return widget

    def value(self) -> int:
        return self.widget.value()

    def set_value(self, value: Any) -> None:
        self.widget.setValue(int(value))

    def on_change(self, callback) -> None:
        self.widget.valueChanged.connect(lambda value: callback({"value": value}))
