"""选择容器与卡片。"""

from __future__ import annotations

import pytest
from obox.qt import Qt
from obox.qt import QTest

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider

MULTI = """
<Choice id="pick" mode="multiple" direction="row" gap="8" on_change="true">
  <Card id="a" value="甲"><Text id="ta" text="甲项" /></Card>
  <Card id="b" value="乙"><Text id="tb" text="乙项" /></Card>
</Choice>
"""

SINGLE = """
<Choice id="pick" mode="single" direction="row" gap="8" on_change="true">
  <Card id="a" value="甲"><Text id="ta" text="甲项" /></Card>
  <Card id="b" value="乙"><Text id="tb" text="乙项" /></Card>
</Choice>
"""


def _build(qapp, html: str):
    provider = build_provider()
    registry = ComponentRegistry()
    events: list = []
    builder = Builder("demo.obox", registry, provider.component_types, events.append)
    root = builder.build(parse_fragment(html))
    return root, registry, events


def test_multiple_select_toggles(qapp) -> None:
    root, registry, events = _build(qapp, MULTI)
    assert root is not None
    choice = registry.lookup("demo.obox", "pick")
    QTest.mouseClick(registry.lookup("demo.obox", "a").widget, Qt.MouseButton.LeftButton)
    QTest.mouseClick(registry.lookup("demo.obox", "b").widget, Qt.MouseButton.LeftButton)
    assert choice.value() == ["乙", "甲"]
    assert events and events[-1].event == "change"
    assert events[-1].payload["value"] == ["乙", "甲"]
    QTest.mouseClick(registry.lookup("demo.obox", "a").widget, Qt.MouseButton.LeftButton)
    assert choice.value() == ["乙"]


def test_single_select_can_clear(qapp) -> None:
    root, registry, events = _build(qapp, SINGLE)
    assert root is not None
    choice = registry.lookup("demo.obox", "pick")
    QTest.mouseClick(registry.lookup("demo.obox", "a").widget, Qt.MouseButton.LeftButton)
    assert choice.value() == ["甲"]
    QTest.mouseClick(registry.lookup("demo.obox", "b").widget, Qt.MouseButton.LeftButton)
    assert choice.value() == ["乙"]
    QTest.mouseClick(registry.lookup("demo.obox", "b").widget, Qt.MouseButton.LeftButton)
    assert choice.value() == []


def test_set_value_updates_selection(qapp) -> None:
    root, registry, _ = _build(qapp, MULTI)
    assert root is not None
    choice = registry.lookup("demo.obox", "pick")
    choice.set_value(["甲"])
    assert choice.value() == ["甲"]


def test_invalid_mode_rejected(qapp) -> None:
    provider = build_provider()
    builder = Builder("demo.obox", ComponentRegistry(), provider.component_types)
    with pytest.raises(ValueError):
        builder.build(parse_fragment('<Choice id="c" mode="bogus"><Card id="a" /></Choice>'))
