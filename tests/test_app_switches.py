"""启动落点与切换后的位置保持。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget

from obox.app import OboxApp

ROOT = Path(__file__).resolve().parent.parent


def _app(tmp_path, language: str = "zh-CN") -> OboxApp:
    obox = OboxApp(ROOT, language=language, data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    return obox


def _spec() -> dict:
    return {
        "view_id": "demo.main",
        "extension_id": "demo.obox",
        "html": "views/main.oml",
        "directory": str(ROOT / "extensions/demo"),
        "container": "sidebar",
        "title": "示范",
    }


def test_current_view_id(qapp, tmp_path) -> None:
    obox = _app(tmp_path)
    assert obox.window.current_view_id() == ""
    obox.window.add_view("demo.main", "示范", QWidget(), "sidebar", "")
    assert obox.window.show_view("demo.main")
    assert obox.window.current_view_id() == "demo.main"
    obox.shutdown()


def test_language_switch_keeps_view(qapp, tmp_path) -> None:
    obox = _app(tmp_path)
    spec = _spec()
    obox._view_specs["demo.main"] = spec
    assert obox._mount_view(spec) is not None
    assert obox.window.show_view("demo.main")
    assert obox.switch_language("en-US")
    assert obox.window.current_view_id() == "demo.main"
    obox.shutdown()


def test_tray_theme_switch_refreshes_menu(qapp, tmp_path) -> None:
    obox = _app(tmp_path)
    refreshed: list[int] = []
    obox._refresh_tray = lambda: refreshed.append(1)
    obox.switch_theme = lambda name: True
    obox._settings = {}
    obox._save_settings = lambda: None
    obox._switch_theme_from_tray("dark")
    assert refreshed == [1]
    obox.shutdown()


def test_startup_opens_app_page(qapp, tmp_path) -> None:
    obox = _app(tmp_path)
    obox.window.add_view("app.main", "应用", QWidget(), "sidebar", "")
    obox._on_extensions_ready({"i18n": {}, "extensions": [], "views": []})
    assert obox.window.current_view_id() == "app.main"
    obox.shutdown()


def test_startup_without_app_page_stays_home(qapp, tmp_path) -> None:
    obox = _app(tmp_path)
    obox._on_extensions_ready({"i18n": {}, "extensions": [], "views": []})
    assert obox.window.current_view_id() == ""
    obox.shutdown()