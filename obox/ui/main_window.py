"""主窗口：无边框窗口 + 自绘标题栏 + 三段式外壳。"""

from __future__ import annotations

import ctypes
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .icons import tinted_icon
from .title_bar import TitleBar

SIDEBAR_CONTAINER = "sidebar"
BOTTOM_CONTAINER = "bottom"
_RAIL_WIDTH = 56
_RESIZE_MARGIN = 6
_MIN_WIDTH = 760
_MIN_HEIGHT = 520


class MainWindow(QWidget):
    """窗口行为（拖动、缩放、最大化、系统菜单）全部自己实现。"""

    close_requested = Signal()

    def __init__(self, translator=None) -> None:
        super().__init__()
        self._t = translator or (lambda text: text)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setObjectName("obox-window")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumSize(_MIN_WIDTH, _MIN_HEIGHT)
        self.resize(980, 680)
        self.setWindowTitle("obox")
        self.setMouseTracking(True)

        self._views: dict[str, QWidget] = {}
        self._rail_entries: list[tuple[QPushButton, QWidget, str]] = []
        self._icon_muted = "#6f6b64"
        self._icon_active = "#5b7f95"
        self._resize_edges = 0
        self._resize_origin: QPoint | None = None
        self._resize_geometry: QRect | None = None
        self._dwm_ready = False

        self._title_bar = TitleBar("obox", "", self)
        self._title_bar.minimize_requested.connect(self.showMinimized)
        self._title_bar.maximize_requested.connect(self.toggle_maximized)
        self._title_bar.close_requested.connect(self.close)

        self._home = self._build_home()
        self._stack = QStackedWidget()
        self._stack.addWidget(self._home)
        self._stack.currentChanged.connect(self._refresh_rail_icons)
        self._rail = self._build_rail()
        self._bottom = self._build_bottom()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._title_bar)
        outer.addWidget(self._build_body(), 1)

    # ---------- 窗口行为 ----------
    def set_window_icon(self, icon_path: str) -> None:
        if icon_path and Path(icon_path).exists():
            self._title_bar.set_icon(icon_path)
            self.setWindowIcon(QIcon(icon_path))

    def toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._title_bar.set_maximized(self.isMaximized())

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._dwm_ready:
            self._dwm_ready = True
            self._apply_dwm_shadow()

    def _apply_dwm_shadow(self) -> None:
        """Windows 上补阴影与圆角；失败就退回普通无边框。"""
        try:
            hwnd = int(self.winId())

            class Margins(ctypes.Structure):
                _fields_ = [("left", ctypes.c_int), ("right", ctypes.c_int), ("top", ctypes.c_int), ("bottom", ctypes.c_int)]

            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(Margins(1, 1, 1, 1)))
            preference = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
            )
        except Exception:
            return

    def _edge_at(self, position: QPoint) -> int:
        edges = 0
        if position.x() <= _RESIZE_MARGIN:
            edges |= 1
        if position.x() >= self.width() - _RESIZE_MARGIN:
            edges |= 2
        if position.y() <= _RESIZE_MARGIN:
            edges |= 4
        if position.y() >= self.height() - _RESIZE_MARGIN:
            edges |= 8
        return edges

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            edges = self._edge_at(event.position().toPoint())
            if edges:
                self._resize_edges = edges
                self._resize_origin = event.globalPosition().toPoint()
                self._resize_geometry = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._resize_edges and self._resize_origin is not None and self._resize_geometry is not None:
            self._resize_to(event.globalPosition().toPoint())
            return
        self._update_cursor(self._edge_at(event.position().toPoint()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._resize_edges = 0
        self._resize_origin = None
        self._resize_geometry = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def _update_cursor(self, edges: int) -> None:
        if edges in (1 | 4, 2 | 8):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges in (2 | 4, 1 | 8):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edges & (1 | 2):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges & (4 | 8):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _resize_to(self, global_position: QPoint) -> None:
        origin, base = self._resize_origin, self._resize_geometry
        if origin is None or base is None:
            return
        delta = global_position - origin
        rect = QRect(base)
        if self._resize_edges & 1:
            rect.setLeft(min(rect.right() - _MIN_WIDTH, base.left() + delta.x()))
        if self._resize_edges & 2:
            rect.setRight(max(rect.left() + _MIN_WIDTH, base.right() + delta.x()))
        if self._resize_edges & 4:
            rect.setTop(min(rect.bottom() - _MIN_HEIGHT, base.top() + delta.y()))
        if self._resize_edges & 8:
            rect.setBottom(max(rect.top() + _MIN_HEIGHT, base.bottom() + delta.y()))
        self.setGeometry(rect)

    # ---------- 界面 ----------
    def _build_home(self) -> QWidget:
        page = QFrame()
        page.setObjectName("obox-home")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        title = QLabel("obox", page)
        title.setObjectName("obox-home-title")
        layout.addWidget(title)
        hint = QLabel(self._t("{{i18n.home.hint}}"), page)
        hint.setWordWrap(True)
        hint.setObjectName("obox-home-hint")
        self._hint_label = hint
        layout.addWidget(hint)
        layout.addStretch(1)
        return page

    def _build_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName("obox-rail")
        rail.setFixedWidth(_RAIL_WIDTH)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._rail_layout = layout
        return rail

    def _build_bottom(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("obox-bottom")
        bar.setFixedHeight(46)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        layout.addStretch(1)
        self._bottom_layout = layout
        bar.hide()
        return bar

    def _build_body(self) -> QWidget:
        body = QFrame()
        body.setObjectName("obox-body")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        middle = QFrame(body)
        middle_layout = QHBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        middle_layout.addWidget(self._rail)
        middle_layout.addWidget(self._stack, 1)
        layout.addWidget(middle, 1)
        layout.addWidget(self._bottom)
        return body

    def add_view(
        self,
        view_id: str,
        title: str,
        widget: QWidget,
        container: str = SIDEBAR_CONTAINER,
        icon_path: str = "",
    ) -> None:
        if view_id in self._views:
            return
        self._views[view_id] = widget
        if container == BOTTOM_CONTAINER:
            self._bottom_layout.insertWidget(self._bottom_layout.count() - 1, widget)
            self._bottom.show()
            return
        self._stack.addWidget(widget)
        button = self._make_rail_button(title, widget, icon_path)
        self._rail_entries.append((button, widget, icon_path))
        self._rail_layout.addWidget(button)
        self._refresh_rail_icons()

    def current_view_id(self) -> str:
        """当前栈里的视图 id；停在内页或空栈时返回空串。"""
        current = self._stack.currentWidget()
        for view_id, widget in self._views.items():
            if widget is current:
                return view_id
        return ""

    def remove_view(self, view_id: str) -> bool:
        """摘掉一个视图与它的侧栏按钮；当前视图被摘时回到首页。"""
        widget = self._views.pop(view_id, None)
        if widget is None:
            return False
        was_current = self._stack.currentWidget() is widget
        if widget in [item for _button, item, _icon in self._rail_entries]:
            for entry in list(self._rail_entries):
                button, item, _icon = entry
                if item is widget:
                    self._rail_entries.remove(entry)
                    self._rail_layout.removeWidget(button)
                    button.setParent(None)
        else:
            self._bottom_layout.removeWidget(widget)
            if self._bottom_layout.count() <= 1:
                self._bottom.hide()
        self._stack.removeWidget(widget)
        widget.setParent(None)
        widget.close()
        if was_current:
            self._stack.setCurrentWidget(self._home)
        self._refresh_rail_icons()
        return True

    def clear_views(self) -> None:
        for widget in self._views.values():
            self._stack.removeWidget(widget)
            widget.setParent(None)
            widget.close()
        self._views.clear()
        self._rail_entries.clear()
        while self._rail_layout.count():
            item = self._rail_layout.takeAt(0)
            button = item.widget()
            if button is not None:
                button.setParent(None)
        while self._bottom_layout.count() > 1:
            item = self._bottom_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.close()
        self._bottom.hide()
        self._stack.setCurrentWidget(self._home)

    def _make_rail_button(self, title: str, widget: QWidget, icon_path: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName(f"rail-{title}")
        button.setToolTip(title)
        button.setFixedSize(40, 40)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            "QPushButton { border: none; border-radius: 10px; }"
            "QPushButton:hover { background: rgba(0, 0, 0, 0.05); }"
        )
        if icon_path and Path(icon_path).exists():
            button.setIcon(tinted_icon(icon_path, self._icon_muted))
            button.setIconSize(button.sizeHint())
            button.setIconSize(button.iconSize())
        else:
            button.setText(title[:1].upper())
        button.clicked.connect(lambda: self._stack.setCurrentWidget(widget))
        return button

    def retranslate(self) -> None:
        self._hint_label.setText(self._t("{{i18n.home.hint}}"))

    def set_title_button_colors(self, muted: str, active: str, danger: str = "#d93026") -> None:
        self._title_bar.set_button_colors(muted, active, danger)

    def set_icon_colors(self, muted: str, active: str) -> None:
        self._icon_muted = muted
        self._icon_active = active
        self._refresh_rail_icons()

    def _refresh_rail_icons(self, *_args) -> None:
        current = self._stack.currentWidget()
        for button, widget, icon_path in self._rail_entries:
            if not icon_path or not Path(icon_path).exists():
                continue
            color = self._icon_active if widget is current else self._icon_muted
            button.setIcon(tinted_icon(icon_path, color))

    def notify_warning(self, title: str, content: str) -> None:
        """轻提示：贴在标题栏下的浮层，几秒后自动收起。"""
        toast = QFrame(self)
        toast.setObjectName("obox-toast")
        toast.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(toast)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        headline = QLabel(title, toast)
        headline.setObjectName("obox-toast-title")
        layout.addWidget(headline)
        body = QLabel(content, toast)
        body.setObjectName("obox-toast-body")
        body.setWordWrap(True)
        layout.addWidget(body)
        toast.adjustSize()
        toast.setFixedWidth(320)
        toast.move((self.width() - toast.width()) // 2, self._title_bar.height() + 20)
        toast.show()
        toast.raise_()
        QTimer.singleShot(4000, toast.close)

    def allow_close(self) -> None:
        self._close_allowed = True

    def show_view(self, view_id: str) -> bool:
        widget = self._views.get(view_id)
        for button, candidate, _ in self._rail_entries:
            if candidate is widget:
                button.click()
                return True
        return False

    def closeEvent(self, event) -> None:  # noqa: N802
        if getattr(self, "_close_allowed", False):
            event.accept()
            return
        event.ignore()
        self.close_requested.emit()

    def view_ids(self) -> list[str]:
        return sorted(self._views)

    def rail_buttons(self) -> list[QPushButton]:
        return [
            self._rail_layout.itemAt(index).widget()
            for index in range(self._rail_layout.count())
            if isinstance(self._rail_layout.itemAt(index).widget(), QPushButton)
        ]
