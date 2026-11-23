"""托盘菜单结构。"""

from __future__ import annotations

from PySide6.QtGui import QIcon

from obox.ui.tray import TrayIcon


def _tray() -> TrayIcon:
    tray = TrayIcon(QIcon())
    tray.set_theme_options([("light", "浅色"), ("dark", "深色")], "light")
    tray.set_language_options([("zh-CN", "简体中文"), ("en-US", "English")], "zh-CN")
    return tray


def test_menu_has_three_groups(qapp) -> None:
    menu = _tray().menu()
    texts = [action.text() for action in menu.actions()]
    assert texts[0] == "打开 obox 窗口"
    for name in ("切换主题", "切换语言", "刷新扩展", "打开扩展目录", "设置", "退出"):
        assert name in texts
    assert texts[-2:] == ["设置", "退出"]
    assert sum(1 for action in menu.actions() if action.isSeparator()) == 2


def test_theme_submenu_checks_current(qapp) -> None:
    tray = TrayIcon(QIcon())
    tray.set_theme_options([("light", "浅色"), ("dark", "深色")], "dark")
    submenu = next(a for a in tray.menu().actions() if a.text() == "切换主题").menu()
    assert {action.text(): action.isChecked() for action in submenu.actions()} == {
        "浅色": False,
        "深色": True,
    }


def test_disable_keeps_window_and_quit(qapp) -> None:
    tray = _tray()
    tray.set_enabled(False)
    states = {action.text(): action.isEnabled() for action in tray.menu().actions() if action.text()}
    assert states["打开 obox 窗口"] is True
    assert states["设置"] is True
    assert states["退出"] is True
    assert states["刷新扩展"] is False


def test_reload_and_open_dir_emit(qapp, tmp_path) -> None:
    tray = _tray()
    fired: list[str] = []
    tray.reload_requested.connect(lambda: fired.append("reload"))
    tray.open_extensions_requested.connect(lambda: fired.append("open"))
    for action in tray.menu().actions():
        if action.text() == "刷新扩展":
            action.trigger()
        if action.text() == "打开扩展目录":
            action.trigger()
    assert fired == ["reload", "open"]

def test_stylesheet_reaches_menu_and_submenus(qapp) -> None:
    tray = _tray()
    tray.apply_stylesheet("#obox-tray-menu { background: #1f2024; }")
    assert tray.menu().styleSheet()
    submenu = next(a for a in tray.menu().actions() if a.text() == "切换主题").menu()
    assert submenu.styleSheet()
