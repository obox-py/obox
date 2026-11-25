"""图表组件：matplotlib 的 QtAgg 画布，支持缩放、平移、悬停坐标与重置。"""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from .. import palette
from .base import Component

_MISSING = "未安装 matplotlib，无法渲染图表"


_FONT_READY = False
_CJK_FONTS = ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "HarmonyOS Sans SC", "Source Han Sans SC")


def _line_icon(kind: str, color: QColor) -> QIcon:
    """自绘线性工具栏图标（32px 画布，逻辑 16px），比 matplotlib 位图更细。"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(2.0)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color)
    pen.setWidthF(1.15)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    if kind == "home":
        painter.drawPolyline([QPointF(2.5, 8), QPointF(8, 3), QPointF(13.5, 8)])
        painter.drawPolyline([QPointF(4, 7), QPointF(4, 13), QPointF(12, 13), QPointF(12, 7)])
    elif kind == "back":
        painter.drawLine(QPointF(13, 8), QPointF(5, 8))
        painter.drawPolyline([QPointF(8, 5), QPointF(5, 8), QPointF(8, 11)])
    elif kind == "forward":
        painter.drawLine(QPointF(3, 8), QPointF(11, 8))
        painter.drawPolyline([QPointF(8, 5), QPointF(11, 8), QPointF(8, 11)])
    elif kind == "pan":
        painter.drawLine(QPointF(8, 3), QPointF(8, 13))
        painter.drawLine(QPointF(3, 8), QPointF(13, 8))
        painter.drawPolyline([QPointF(6, 5), QPointF(8, 3), QPointF(10, 5)])
        painter.drawPolyline([QPointF(6, 11), QPointF(8, 13), QPointF(10, 11)])
        painter.drawPolyline([QPointF(5, 6), QPointF(3, 8), QPointF(5, 10)])
        painter.drawPolyline([QPointF(11, 6), QPointF(13, 8), QPointF(11, 10)])
    elif kind == "zoom":
        painter.drawEllipse(QPointF(8, 7), 5, 5)
        painter.drawLine(QPointF(11.5, 10.5), QPointF(14, 13))
        painter.drawLine(QPointF(6, 7), QPointF(10, 7))
    elif kind == "subplots":
        painter.drawRect(3, 3, 10, 10)
        painter.drawLine(QPointF(8, 3), QPointF(8, 13))
        painter.drawLine(QPointF(3, 8), QPointF(13, 8))
    elif kind == "save":
        painter.drawLine(QPointF(8, 3), QPointF(8, 10))
        painter.drawPolyline([QPointF(5, 7), QPointF(8, 10), QPointF(11, 7)])
        painter.drawLine(QPointF(4, 13), QPointF(12, 13))
    painter.end()
    return QIcon(pixmap)


def _tint_icon(icon: QIcon, color: QColor, size: int = 24) -> QIcon:
    """把工具栏自带的深色图标染成当前主题的文字色；无图标时原样返回。"""
    if icon.isNull():
        return icon
    pixmap = icon.pixmap(size, size)
    if pixmap.isNull():
        return icon
    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.GlobalColor.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return QIcon(tinted)


def _apply_theme() -> None:
    """把画布配色跟随当前主题，避免深色主题里出现刺眼的白底图。"""
    try:
        from matplotlib import rcParams

        rcParams.update(
            {
                "figure.facecolor": palette.SURFACE,
                "axes.facecolor": palette.SURFACE,
                "savefig.facecolor": palette.SURFACE,
                "text.color": palette.TEXT,
                "axes.labelcolor": palette.TEXT,
                "axes.edgecolor": palette.LINE,
                "xtick.color": palette.TEXT_MUTED,
                "ytick.color": palette.TEXT_MUTED,
                "grid.color": palette.LINE,
                "legend.facecolor": palette.SURFACE,
                "legend.edgecolor": palette.LINE,
                "legend.labelcolor": palette.TEXT,
                "figure.edgecolor": palette.SURFACE,
            }
        )
    except ImportError:
        pass


def _configure_fonts() -> None:
    """让 matplotlib 用系统中文字体，避免标题与刻度出现方块。"""
    global _FONT_READY
    if _FONT_READY:
        return
    _FONT_READY = True
    try:
        from matplotlib import font_manager, rcParams

        available = {font.name for font in font_manager.fontManager.ttflist}
        for name in _CJK_FONTS:
            if name in available:
                rcParams["font.sans-serif"] = [name, *rcParams["font.sans-serif"]]
                break
        rcParams["axes.unicode_minus"] = False
    except ImportError:
        pass


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
    supported_states = ("data", "title", "code", "visible")
    state_accessors = {
        "data": ("data", "set_data"),
        "title": ("title", "set_title"),
        "code": ("code", "set_code"),
        "visible": ("is_visible", "set_visible"),
    }
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        self._data = _parse_data(attrs.get("data") or "")
        self._code = str(attrs.get("code") or "")
        self._title = attrs.get("title") or self._data.get("title") or ""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._canvas = None
        self._figure = None
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
            from matplotlib.figure import Figure
        except ImportError:
            self._missing = QLabel(_MISSING)
            self._missing.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._missing.setStyleSheet(f"color: {palette.TEXT_MUTED};")
            layout.addWidget(self._missing)
            return widget

        _configure_fonts()
        _apply_theme()
        self._figure = Figure(figsize=(4, 3), tight_layout=True)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._canvas.setObjectName(f"{self.id}-canvas")
        self._toolbar = NavigationToolbar2QT(self._canvas, widget)
        self._toolbar.setObjectName(f"{self.id}-toolbar")
        try:
            self._toolbar.locLabel.hide()
        except AttributeError:
            pass
        self._toolbar.hide()

        bar = QWidget(widget)
        bar.setObjectName(f"{self.id}-toolbar-bar")
        bar.setFixedHeight(30)
        bar.setStyleSheet(
            "QToolButton { background: transparent; border: none; border-radius: 4px; padding: 2px; }"
            f"QToolButton:hover {{ background: {palette.SURFACE_MUTED}; }}"
            f"QToolButton:checked {{ background: {palette.ACCENT_SOFT}; }}"
        )
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 1, 0, 1)
        row.setSpacing(2)
        tint = QColor(palette.TEXT_MUTED)

        def _add_button(kind: str, tooltip: str, slot, checkable: bool = False) -> QToolButton:
            button = QToolButton(bar)
            button.setIcon(_line_icon(kind, tint))
            button.setIconSize(QSize(16, 16))
            button.setToolTip(tooltip)
            button.setCheckable(checkable)
            button.setAutoRaise(True)
            button.clicked.connect(slot)
            row.addWidget(button)
            return button

        _add_button("home", "回到初始视图", self._toolbar.home)
        _add_button("back", "后退", self._toolbar.back)
        _add_button("forward", "前进", self._toolbar.forward)
        row.addSpacing(6)
        pan = _add_button("pan", "平移", lambda: self._toolbar.pan(), True)
        zoom = _add_button("zoom", "缩放", lambda: self._toolbar.zoom(), True)
        pan.toggled.connect(lambda on: zoom.setChecked(False) if on else None)
        zoom.toggled.connect(lambda on: pan.setChecked(False) if on else None)
        row.addSpacing(6)
        _add_button("subplots", "子图设置", self._toolbar.configure_subplots)
        _add_button("save", "保存图片", self._toolbar.save_figure)
        row.addStretch(1)
        layout.addWidget(bar)
        layout.addWidget(self._canvas, 1)
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
        self._annotation = None
        axis = self._figure.add_subplot(111)
        if self._code:
            self._render_code(axis)
            return
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

    def _render_code(self, axis) -> None:
        """执行扩展提供的 matplotlib 代码；fig/ax/plt 可直接用。"""
        namespace = {"__name__": "__chart__", "fig": self._figure, "ax": axis}
        try:
            import matplotlib.pyplot as plt

            namespace["plt"] = plt
        except ImportError:
            pass
        try:
            exec(compile(self._code, "<chart>", "exec"), namespace)
        except Exception as exc:  # 用户代码错误直接画在图上
            self._figure.clear()
            self._annotation = None
            error_axis = self._figure.add_subplot(111)
            error_axis.axis("off")
            error_axis.text(
                0.5, 0.5, f"图表代码错误：{exc}", ha="center", va="center", wrap=True, fontsize=10
            )
        self._canvas.draw_idle()

    def code(self) -> str:
        return self._code

    def set_code(self, value: Any) -> None:
        self._code = str(value or "")
        self._render()

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
        if getattr(self, "_toolbar", None) is not None and self._toolbar.mode:
            return
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
        if getattr(self, "_toolbar", None) is not None and self._toolbar.mode:
            return
        if event.inaxes is None or event.button != 1:
            return
        self._drag = (event.xdata, event.ydata)

    def _on_release(self, event) -> None:
        self._drag = None

    def _on_move(self, event) -> None:
        if self._canvas is None:
            return
        if getattr(self, "_toolbar", None) is not None and self._toolbar.mode:
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
                try:
                    self._annotation.remove()
                except (NotImplementedError, ValueError):
                    pass
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