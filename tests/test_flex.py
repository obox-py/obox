"""Flex 容器的排布规则。"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QWidget

from obox.ui.components.flex import FlexLayout


class Item(QWidget):
    """带固定 sizeHint 的测试子项；不用 setFixedSize，否则 grow 会被夹住。"""

    def __init__(self, width: int, height: int, parent: QWidget, grow: str | None = None) -> None:
        super().__init__(parent)
        self._hint = QSize(width, height)
        if grow is not None:
            self.setProperty("flex_grow", grow)

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt 接口
        return self._hint


def _layout(attrs: dict[str, str], parent: QWidget) -> FlexLayout:
    layout = FlexLayout(attrs, parent)
    parent.setLayout(layout)
    return layout


def test_row_gap_and_alignment(qapp) -> None:
    host = QWidget()
    host.resize(300, 60)
    layout = _layout({"direction": "row", "gap": "10", "align": "center"}, host)
    first = Item(40, 20, host)
    second = Item(40, 20, host)
    layout.addWidget(first)
    layout.addWidget(second)
    layout.setGeometry(QRect(0, 0, 300, 60))
    assert first.geometry().x() == 0
    assert second.geometry().x() == 50
    assert first.geometry().y() == 20


def test_wrap_creates_second_line(qapp) -> None:
    host = QWidget()
    host.resize(100, 120)
    layout = _layout({"direction": "row", "wrap": "wrap", "gap": "10"}, host)
    widgets = [Item(40, 20, host) for _ in range(3)]
    for widget in widgets:
        layout.addWidget(widget)
    layout.setGeometry(QRect(0, 0, 100, 120))
    assert widgets[0].geometry().y() == 0
    assert widgets[2].geometry().y() >= 20


def test_grow_takes_remaining_space(qapp) -> None:
    host = QWidget()
    host.resize(300, 40)
    layout = _layout({"direction": "row", "gap": "10"}, host)
    fixed = Item(40, 20, host)
    growing = Item(40, 20, host, grow="1")
    tail = Item(40, 20, host)
    for widget in (fixed, growing, tail):
        layout.addWidget(widget)
    layout.setGeometry(QRect(0, 0, 300, 40))
    assert growing.geometry().width() > 40
    assert fixed.geometry().width() == 40


def test_invalid_attribute_rejected(qapp) -> None:
    host = QWidget()
    with pytest.raises(ValueError) as error:
        FlexLayout({"justify": "bogus"}, host)
    assert "justify" in str(error.value)


def test_column_direction(qapp) -> None:
    host = QWidget()
    host.resize(80, 200)
    layout = _layout({"direction": "column", "gap": "8"}, host)
    first = Item(30, 20, host)
    second = Item(30, 20, host)
    layout.addWidget(first)
    layout.addWidget(second)
    layout.setGeometry(QRect(0, 0, 80, 200))
    assert first.geometry().y() == 0
    assert second.geometry().y() == 28