"""图片：按路径显示图标或位图。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from obox.qt import Qt
from obox.qt import QPixmap
from obox.qt import QLabel

from .base import Component


class ImageComponent(Component):
    tag = "image"
    supported_states = ("visible",)
    state_accessors = {"visible": ("is_visible", "set_visible")}

    def build_widget(self, attrs: dict[str, str]) -> QLabel:
        width = int(attrs.get("width", "24"))
        height = int(attrs.get("height", "24"))
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedSize(width, height)
        self._path = attrs.get("src", "")
        self._apply(label)
        return label

    def _apply(self, label: QLabel | None = None) -> None:
        target = label if label is not None else self.widget
        if not self._path or not Path(self._path).exists():
            return
        pixmap = QPixmap(self._path)
        if pixmap.isNull():
            return
        target.setPixmap(
            pixmap.scaled(
                target.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def set_path(self, value: Any) -> None:
        self._path = str(value)
        self._apply()
