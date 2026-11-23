from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget

from obox.app import OboxApp
from obox.ui.main_window import MainWindow
from tests.fake_provider import build_provider

ROOT = Path(__file__).resolve().parent.parent


def test_main_window_sections(qapp) -> None:
    window = MainWindow()
    window.show()
    assert window.rail_buttons() == []
    assert not window._bottom.isVisible()
    window.add_view("demo.main", "示范", QWidget(), "sidebar", "")
    window.add_view("demo.bottom", "底栏", QWidget(), "bottom", "")
    assert len(window.rail_buttons()) == 1
    assert window._bottom.isVisible()
    window.clear_views()
    assert window.rail_buttons() == []
    window.close()


def test_assemble_view_with_provider(qapp) -> None:
    obox = OboxApp(ROOT, provider=build_provider())
    html = '<Div id="root"><Text id="title" text="hi" /></Div>'
    root, ids = obox.assemble_view("demo.obox", html)
    assert ids
    assert root is not None
    assert set(ids) == {"root", "title"}
    assert obox.registry.lookup("demo.obox", "title").text() == "hi"