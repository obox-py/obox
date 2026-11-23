"""图表组件：matplotlib 的 QtAgg 画布，支持缩放、平移、悬停坐标与重置。"""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from .. import palette
from .base import Component

_MISSING = "未安装 matplotlib，无法渲染图表"


def _parse_data(value: Any) -> dict:
    if isinstance(value, dict):
        return dict(value)
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


class ChartComponent(Component):
    tag = "chart"
    supported_states = ("data", "title", "visible")
    state_accessors = {
        "data": ("data", "set_data"),
        "title": ("title", "set_title"),
        "visible": ("is_visible", "set_visible"),
    }
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        self._data = _parse_data(attrs.get("data") or "")
        self._title = attrs.get("title") or self._data.get("title") or ""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._canvas = None
        self._figure = None
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure
        except ImportError:
            self._missing = QLabel(_MISSING)
            self._missing.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._missing.setStyleSheet(f"color: {palette.TEXT_MUTED};")
            layout.addWidget(self._missing)
            return widget

        self._figure = Figure(figsize=(4, 3), tight_layout=True)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._canvas.setObjectName(f"{self.id}-canvas")
        layout.addWidget(self._canvas, 1)
        self._reset = QPushButton("重置", widget)
        self._reset.setFixedHeight(24)
        self._reset.clicked.connect(self.reset_view)
        layout.addWidget(self._reset, 0, Qt.AlignmentFlag.AlignRight)
        self._canvas.mpl_connect("scroll_event", self._on_scroll)
        self._canvas.mpl_connect("button_press_event", self._on_press)
        self._canvas.mpl_connect("button_release_event", self._on_release)
        self._canvas.mpl_connect("motion_notify_event", self._on_move)
        self._drag: tuple[float, float] | None = None
        self._annotation = None
        self._render()
        return widget

    def _render(self) -> None:
        if self._canvas is None or self._figure is None:
            return
        self._figure.clear()
        axis = self._figure.add_subplot(111)
        data = self._data or {}
        kind = str(data.get("type") or "line")
        series = data.get("series") or []
        labels = data.get("x") or []
        axis.set_title(self._title or str(data.get("title") or ""))
        for item in series:
            points = item.get("points") or []
            xs = [float(point.get("x", index)) for index, point in enumerate(points)]
            ys = [float(point.get("y", 0)) for point in points]
            name = str(item.get("name") or "")
            if kind == "bar":
                axis.bar(xs, ys, label=name)
            elif kind == "scatter":
                axis.scatter(xs, ys, label=name)
            else:
                axis.plot(xs, ys, label=name)
        if labels:
            axis.set_xticks(range(len(labels)))
            axis.set_xticklabels([str(label) for label in labels])
            self._figure.autofmt_xdate(rotation=30)
        if series:
            axis.legend()
        axis.grid(True, color=palette.LINE, linewidth=0.6)
        self._canvas.draw_idle()

    def data(self) -> str:
        return json.dumps(self._data, ensure_ascii=False)

    def set_data(self, value: Any) -> None:
        self._data = _parse_data(value)
        self._render()

    def title(self) -> str:
        return self._title

    def set_title(self, value: Any) -> None:
        self._title = str(value)
        self._render()

    def reset_view(self) -> None:
        if self._canvas is None or self._figure is None:
            return
        self._render()

    def _on_scroll(self, event) -> None:
        if event.inaxes is None:
            return
        scale = 0.85 if event.button == "up" else 1.15
        xlim = event.inaxes.get_xlim()
        ylim = event.inaxes.get_ylim()
        cx, cy = event.xdata, event.ydata
        event.inaxes.set_xlim([cx - (cx - xlim[0]) * scale, cx + (xlim[1] - cx) * scale])
        event.inaxes.set_ylim([cy - (cy - ylim[0]) * scale, cy + (ylim[1] - cy) * scale])
        self._canvas.draw_idle()

    def _on_press(self, event) -> None:
        if event.inaxes is None or event.button != 1:
            return
        self._drag = (event.xdata, event.ydata)

    def _on_release(self, event) -> None:
        self._drag = None

    def _on_move(self, event) -> None:
        if self._canvas is None:
            return
        if self._drag is not None and event.inaxes is not None and event.button == 1:
            dx = self._drag[0] - event.xdata
            dy = self._drag[1] - event.ydata
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()
            event.inaxes.set_xlim(xlim[0] + dx, xlim[1] + dx)
            event.inaxes.set_ylim(ylim[0] + dy, ylim[1] + dy)
            self._canvas.draw_idle()
            return
        if event.inaxes is None or event.xdata is None:
            return
        text = f"({event.xdata:.2f}, {event.ydata:.2f})"
        if self._annotation is None:
            self._annotation = event.inaxes.annotate(
                text,
                xy=(event.xdata, event.ydata),
                xytext=(8, 8),
                textcoords="offset points",
                fontsize=8,
            )
        else:
            self._annotation.xy = (event.xdata, event.ydata)
            self._annotation.set_text(text)
            if self._annotation.axes is not event.inaxes:
                self._annotation.remove()
                self._annotation = event.inaxes.annotate(
                    text,
                    xy=(event.xdata, event.ydata),
                    xytext=(8, 8),
                    textcoords="offset points",
                    fontsize=8,
                )
        self._canvas.draw_idle()

    def on_click(self, callback) -> None:
        self._callbacks = getattr(self, "_callbacks", [])
        self._callbacks.append(callback)

    def detach(self) -> None:
        if self._canvas is not None:
            close = getattr(self._canvas, "close", None)
            if close is not None:
                close()
