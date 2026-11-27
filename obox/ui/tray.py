"""系统托盘：分组菜单、主题与语言子菜单、刷新与打开扩展目录。"""

from __future__ import annotations

from typing import Callable

from obox.qt import QObject, Qt, Signal
from obox.qt import QIcon
from obox.qt import QMenu, QSystemTrayIcon

_DEFAULTS = {
    "tray.show": "打开 obox 窗口",
    "tray.theme": "切换主题",
    "tray.language": "切换语言",
    "tray.reload": "刷新扩展",
    "tray.opendir": "打开扩展目录",
    "tray.settings": "设置",
    "tray.quit": "退出",
}


class TrayIcon(QObject):
    show_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    reload_requested = Signal()
    open_extensions_requested = Signal()
    theme_requested = Signal(str)
    language_requested = Signal(str)

    def __init__(
        self,
        icon: QIcon,
        parent: QObject | None = None,
        translator: Callable[[str], str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._translator = translator
        self._tray = QSystemTrayIcon(icon, parent)
        self._tray.setToolTip("obox")
        menu = QMenu()
        menu.setObjectName("obox-tray-menu")
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._show_action = menu.addAction(self._label("tray.show"))
        menu.addSeparator()
        self._theme_menu = menu.addMenu(self._label("tray.theme"))
        self._theme_menu.setObjectName("obox-tray-menu")
        self._language_menu = menu.addMenu(self._label("tray.language"))
        self._language_menu.setObjectName("obox-tray-menu")
        self._reload_action = menu.addAction(self._label("tray.reload"))
        self._open_action = menu.addAction(self._label("tray.opendir"))
        menu.addSeparator()
        self._settings_action = menu.addAction(self._label("tray.settings"))
        self._quit_action = menu.addAction(self._label("tray.quit"))
        self._show_action.triggered.connect(self.show_requested.emit)
        self._reload_action.triggered.connect(self.reload_requested.emit)
        self._open_action.triggered.connect(self.open_extensions_requested.emit)
        self._settings_action.triggered.connect(self.settings_requested.emit)
        self._quit_action.triggered.connect(self.quit_requested.emit)
        self._tray.setContextMenu(menu)
        self._menu = menu
        self._tray.activated.connect(self._on_activated)

    def _label(self, key: str) -> str:
        text = self._translator(key) if self._translator else ""
        if not text or text.startswith("{{"):
            return _DEFAULTS.get(key, key)
        return text

    def retranslate(self) -> None:
        """语言切换后改写常驻菜单项的文案。"""
        self._show_action.setText(self._label("tray.show"))
        self._theme_menu.setTitle(self._label("tray.theme"))
        self._language_menu.setTitle(self._label("tray.language"))
        self._reload_action.setText(self._label("tray.reload"))
        self._open_action.setText(self._label("tray.opendir"))
        self._settings_action.setText(self._label("tray.settings"))
        self._quit_action.setText(self._label("tray.quit"))

    @staticmethod
    def available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def menu(self) -> QMenu:
        return self._menu

    def apply_stylesheet(self, qss: str) -> None:
        for menu in (self._menu, self._theme_menu, self._language_menu):
            menu.setStyleSheet(qss)

    def set_theme_options(self, options: list[tuple[str, str]], current: str) -> None:
        self._fill(self._theme_menu, options, current, self.theme_requested)

    def set_language_options(self, options: list[tuple[str, str]], current: str) -> None:
        self._fill(self._language_menu, options, current, self.language_requested)

    def _fill(self, menu: QMenu, options: list[tuple[str, str]], current: str, signal) -> None:
        menu.clear()
        for code, label in options:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(code == current)
            action.triggered.connect(lambda _checked=False, value=code: signal.emit(value))

    def set_enabled(self, enabled: bool) -> None:
        """重建期间挡住会重入的入口：切主题、切语言、刷新、打开目录。"""
        self._theme_menu.setEnabled(enabled)
        self._language_menu.setEnabled(enabled)
        self._reload_action.setEnabled(enabled)
        self._open_action.setEnabled(enabled)

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()
