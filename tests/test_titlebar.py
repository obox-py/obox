"""自绘标题栏：按钮、最大化切换与边缘判定。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QPushButton, QWidget

from obox.ui.main_window import MainWindow


def test_title_bar_has_three_buttons(qapp) -> None:
    window = MainWindow()
    bar = window._title_bar
    assert bar._min_button.objectName() == "obox-min"
    assert bar._max_button.objectName() == "obox-max"
    assert bar._close_button.objectName() == "obox-close"
    assert (bar._min_button.width(), bar._min_button.height()) == (40, 30)
    window.close()


def test_maximize_toggles_icon(qapp) -> None:
    window = MainWindow()
    window.show()
    window.toggle_maximized()
    maximized = window.isMaximized()
    assert window._title_bar._max_button._kind == ("restore" if maximized else "max")
    window.toggle_maximized()
    assert not window.isMaximized()
    assert window._title_bar._max_button._kind == "max"
    window.close()


def test_edge_detection(qapp) -> None:
    window = MainWindow()
    window.resize(800, 600)
    assert window._edge_at(QPoint(2, 300)) & 1
    assert window._edge_at(QPoint(798, 300)) & 2
    assert window._edge_at(QPoint(400, 2)) & 4
    assert window._edge_at(QPoint(400, 598)) & 8
    assert window._edge_at(QPoint(400, 300)) == 0
    window.close()


def test_add_view_registers_rail(qapp) -> None:
    window = MainWindow()
    window.show()
    window.add_view("demo.main", "示范", QWidget(), "sidebar", "")
    assert len(window.rail_buttons()) == 1
    window.clear_views()
    assert window.rail_buttons() == []
    window.close()

def test_app_icon_asset_loads(qapp) -> None:
    icon = QIcon(str(Path(__file__).resolve().parent.parent / "obox" / "assets" / "obox.ico"))
    sizes = [size.width() for size in icon.availableSizes()]
    assert sizes and max(sizes) >= 256


SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">'
    '<rect x="0" y="0" width="32" height="32" fill="#ff8800"/></svg>'
)


def test_title_bar_icon_keeps_color(tmp_path: Path, qapp) -> None:
    path = tmp_path / "obox.svg"
    path.write_text(SVG, encoding="utf-8")
    window = MainWindow()
    window.set_window_icon(str(path))
    pixmap = window._title_bar._icon_label.pixmap()
    assert pixmap is not None and not pixmap.isNull()
    image = pixmap.toImage()
    center = QColor.fromRgba(image.pixel(image.width() // 2, image.height() // 2))
    assert center.name() == "#ff8800"
    window.close()

def test_title_bar_has_no_language_switch(qapp) -> None:
    window = MainWindow()
    bar = window._title_bar
    names = [button.objectName() for button in bar.findChildren(QPushButton)]
    assert names == ["obox-min", "obox-max", "obox-close"]
    assert not hasattr(window, "set_languages")
    window.close()
