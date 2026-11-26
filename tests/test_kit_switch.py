"""运行中切换主题：失败要保留原套件；清空视图不留残影。"""

from __future__ import annotations

from pathlib import Path

from obox.qt import QWidget

from obox.app import OboxApp
from obox.ui.main_window import MainWindow
from tests.fake_provider import build_provider

ROOT = Path(__file__).resolve().parent.parent


def test_switch_to_missing_theme_keeps_current(qapp) -> None:
    obox = OboxApp(ROOT, provider=build_provider())
    before = obox.provider
    try:
        assert obox.switch_theme("nope") is False
        assert obox.provider is before
    finally:
        obox.shutdown()


def test_clear_views_removes_rail_and_bottom(qapp) -> None:
    window = MainWindow()
    window.show()
    window.add_view("demo.main", "示范", QWidget(), "sidebar", "")
    window.add_view("demo.bottom", "底栏", QWidget(), "bottom", "")
    assert len(window.rail_buttons()) == 1
    window.clear_views()
    assert window.rail_buttons() == []
    assert window.view_ids() == []
    window.close()