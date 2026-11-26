"""应用窗体：自绘标题栏 + 可滚动内容区。"""

from __future__ import annotations

import ctypes

from obox.qt import Qt
from obox.qt import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from .title_bar import TitleBar


class AppWindow(QWidget):
    """扩展提供的界面在这个窗口里渲染。"""

    def __init__(self, title: str, parent: QWidget | None = None, persistent: bool = False) -> None:
        super().__init__(parent)
        self._persistent = persistent
        self._closed_by_user = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setObjectName("obox-window")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle(title)
        self.resize(720, 520)
        self.setMinimumSize(480, 360)
        self._has_content = False

        self._title_bar = TitleBar(title, "", self)
        self._title_bar.close_requested.connect(self.close)
        self._title_bar.minimize_requested.connect(self.showMinimized)
        self._title_bar.maximize_requested.connect(self._toggle)

        scroll = QScrollArea()
        scroll.setObjectName("obox-view-scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "#obox-view-scroll { background: transparent; }"
            " QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(20, 20, 20, 20)
        self._content_layout.setSpacing(12)
        scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._title_bar)
        outer.addWidget(scroll, 1)

    def _toggle(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._title_bar.set_maximized(self.isMaximized())

    def set_content(self, widget: QWidget) -> None:
        self._clear()
        self._content_layout.addWidget(widget)
        self._has_content = True

    def show_message(self, text: str) -> None:
        self._clear()
        label = QLabel(text, self._content)
        label.setObjectName("obox-home-hint")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(label)
        self._has_content = True

    def has_content(self) -> bool:
        return self._has_content

    def is_closed_by_user(self) -> bool:
        return self._closed_by_user

    def reopen(self) -> None:
        self._closed_by_user = False
        self.show()
        self.raise_()
        self.activateWindow()

    def force_close(self) -> None:
        self._persistent = False
        self.close()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._persistent:
            self._closed_by_user = True
            self.hide()
            event.ignore()
            return
        super().closeEvent(event)

    def _clear(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        try:
            hwnd = int(self.winId())

            class Margins(ctypes.Structure):
                _fields_ = [("left", ctypes.c_int), ("right", ctypes.c_int), ("top", ctypes.c_int), ("bottom", ctypes.c_int)]

            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(Margins(1, 1, 1, 1)))
            preference = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference))
        except Exception:
            return
