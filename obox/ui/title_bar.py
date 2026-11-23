"""自绘标题栏：图标、标题、窗口按钮与拖动/双击/右键菜单。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QWidget

from .icons import tinted_pixmap


class WindowButton(QPushButton):
    """窗口按钮：SVG 图标按主题重染，悬停只在底色上做文章。"""

    _ICONS = {
        "min": "window-min.svg",
        "max": "window-max.svg",
        "restore": "window-restore.svg",
        "close": "window-close.svg",
    }
    _ICON_SIZE = 16
    _ICON_DIR = Path(__file__).resolve().parent.parent / "assets"

    def __init__(self, kind: str, tip: str, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self._kind = kind
        self._muted = "#4e5969"
        self._active = "#1d2129"
        self._danger = "#d93026"
        self.setFixedSize(40, 30)
        self.setToolTip(tip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        self.update()

    def set_colors(self, muted: str, active: str, danger: str = "#d93026") -> None:
        self._muted = muted
        self._active = active
        self._danger = danger
        self.update()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        self.update()
        super().leaveEvent(event)

    def _icon_path(self) -> Path:
        return self._ICON_DIR / self._ICONS.get(self._kind, "window-max.svg")

    def _icon_color(self) -> str:
        if not self.underMouse():
            return self._muted
        return "#ffffff" if self._kind == "close" else self._active

    def _pixmap(self) -> QPixmap:
        dpr = self.devicePixelRatioF() or 1.0
        size = max(1, int(round(self._ICON_SIZE * dpr)))
        pixmap = tinted_pixmap(self._icon_path(), self._icon_color(), size)
        pixmap.setDevicePixelRatio(dpr)
        return pixmap

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        painter = QPainter(self)
        if self.underMouse():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            if self._kind == "close":
                background = QColor(self._danger)
                background.setAlpha(235)
                painter.setBrush(background)
            else:
                background = QColor(self._active)
                background.setAlpha(32)
                painter.setBrush(background)
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 6, 6)
        pixmap = self._pixmap()
        x = (self.width() - self._ICON_SIZE) / 2.0
        y = (self.height() - self._ICON_SIZE) / 2.0
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawPixmap(QPointF(x, y), pixmap)
        painter.end()


class TitleBar(QWidget):
    """所有窗口行为交给宿主窗口，这里只发信号。"""

    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(self, title: str = "obox", icon_path: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("obox-titlebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(40)
        self._drag_origin: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(8)

        self._icon_label = QLabel(self)
        self._icon_label.setFixedSize(18, 18)
        layout.addWidget(self._icon_label)

        self._title_label = QLabel(title, self)
        self._title_label.setObjectName("obox-title")
        layout.addWidget(self._title_label)
        layout.addStretch(1)

        self._min_button = self._window_button("min", "最小化")
        self._max_button = self._window_button("max", "最大化")
        self._close_button = self._window_button("close", "关闭")
        self._min_button.clicked.connect(self.minimize_requested)
        self._max_button.clicked.connect(self.maximize_requested)
        self._close_button.clicked.connect(self.close_requested)
        for button in (self._min_button, self._max_button, self._close_button):
            layout.addWidget(button)

        self.set_icon(icon_path)
        self._title_label.setText(title)

    def _window_button(self, kind: str, tip: str) -> WindowButton:
        button = WindowButton(kind, tip, self)
        button.setObjectName({
            "min": "obox-min",
            "max": "obox-max",
            "close": "obox-close",
        }.get(kind, kind))
        return button

    def set_button_colors(self, muted: str, active: str, danger: str = "#d93026") -> None:
        """窗口按钮的线条色与悬停底色，和侧栏图标配色解耦。"""
        for button in (self._min_button, self._max_button, self._close_button):
            button.set_colors(muted, active, danger)

    def set_icon(self, icon_path: str) -> None:
        """应用图标保持原色：obox 的 svg 是多色的，不做单色重染。"""
        if icon_path and Path(icon_path).exists():
            pixmap = QIcon(icon_path).pixmap(QSize(18, 18), self.devicePixelRatioF())
            self._icon_label.setPixmap(pixmap)

    def set_maximized(self, maximized: bool) -> None:
        self._max_button.set_kind("restore" if maximized else "max")
        self._max_button.setToolTip("还原" if maximized else "最大化")

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self._on_button(event.position()):
            self._drag_origin = event.globalPosition().toPoint() - self.window().pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            window = self.window()
            if window.isMaximized():
                window.showNormal()
            window.move(event.globalPosition().toPoint() - self._drag_origin)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self._on_button(event.position()):
            self.maximize_requested.emit()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu(self)
        window = self.window()
        menu.addAction("还原" if window.isMaximized() else "最大化", self.maximize_requested.emit)
        menu.addAction("最小化", self.minimize_requested.emit)
        menu.addSeparator()
        menu.addAction("关闭", self.close_requested.emit)
        menu.exec(event.globalPos())

    def _on_button(self, position) -> bool:
        for button in (self._min_button, self._max_button, self._close_button):
            if button.geometry().contains(position.toPoint()):
                return True
        return False