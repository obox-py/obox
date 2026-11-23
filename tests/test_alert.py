"""提醒条：类型、位置与偏移。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QWidget

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider

TOP = '<Alert id="a" type="info" position="top" offset="24" text="信息" />'
BOTTOM = '<Alert id="a" type="warn" position="bottom" offset="40" text="注意" />'


def _build(qapp, html: str):
    provider = build_provider()
    registry = ComponentRegistry()
    builder = Builder("demo.obox", registry, provider.component_types)
    host = QWidget()
    host.resize(600, 400)
    root = builder.build(parse_fragment(html))
    root.setParent(host)
    root.resize(600, 400)
    return registry.lookup("demo.obox", "a"), host


def test_top_offset(qapp) -> None:
    alert, host = _build(qapp, TOP)
    alert.set_visible(True)
    assert alert.widget.y() == 24
    assert alert.widget.width() <= host.width()


def test_bottom_offset(qapp) -> None:
    alert, host = _build(qapp, BOTTOM)
    alert.set_visible(True)
    height = alert.widget.height()
    assert alert.widget.y() == host.height() - height - 40


def test_type_colors(qapp) -> None:
    alert, _ = _build(qapp, '<Alert id="a" type="error" position="top" offset="16" text="错了" />')
    style = alert.widget.styleSheet()
    assert "#fde8e7" in style and "#d93026" in style


def test_invalid_type_rejected(qapp) -> None:
    provider = build_provider()
    builder = Builder("demo.obox", ComponentRegistry(), provider.component_types)
    with pytest.raises(ValueError):
        builder.build(parse_fragment('<Alert id="a" type="bogus" />'))
