"""侧栏图标：单色重染与选中变色。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QWidget

from obox.ui.icons import tinted_pixmap
from obox.ui.main_window import MainWindow

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">'
    '<rect x="4" y="4" width="24" height="24" fill="#ff0000"/></svg>'
)


def _write_svg(tmp_path: Path) -> Path:
    path = tmp_path / "icon.svg"
    path.write_text(SVG, encoding="utf-8")
    return path


def test_tint_replaces_color(tmp_path: Path, qapp) -> None:
    path = _write_svg(tmp_path)
    image: QImage = tinted_pixmap(path, "#123456").toImage()
    center = QColor.fromRgba(image.pixel(image.width() // 2, image.height() // 2))
    assert center.name() == "#123456"
    corner = QColor.fromRgba(image.pixel(0, 0))
    assert corner.alpha() == 0


def test_rail_icon_changes_when_selected(tmp_path: Path, qapp) -> None:
    path = _write_svg(tmp_path)
    window = MainWindow()
    window.set_icon_colors("#808080", "#0055ff")
    window.add_view("a", "A", QWidget(), "sidebar", str(path))
    window.add_view("b", "B", QWidget(), "sidebar", str(path))
    first, second = window.rail_buttons()
    window._stack.setCurrentWidget(window._views["a"])
    selected = first.icon().pixmap(22, 22).toImage()
    unselected = second.icon().pixmap(22, 22).toImage()
    assert QColor.fromRgba(selected.pixel(11, 11)).name() == "#0055ff"
    assert QColor.fromRgba(unselected.pixel(11, 11)).name() == "#808080"
    window.close()