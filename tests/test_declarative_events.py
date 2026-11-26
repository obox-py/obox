"""声明式事件订阅：写了 on_ 才绑定。"""

from __future__ import annotations

import pytest
from obox.qt import Qt
from obox.qt import QTest

from obox.ui.builder import BuildError, Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider

WITH_CLICK = '<Div id="root"><Button id="go" text="走" on_click="true" /></Div>'
WITHOUT_CLICK = '<Div id="root"><Button id="go" text="走" /></Div>'


def _build(qapp, html: str):
    provider = build_provider()
    registry = ComponentRegistry()
    events: list = []
    builder = Builder("demo.obox", registry, provider.component_types, events.append)
    root = builder.build(parse_fragment(html))
    return root, registry, events


def test_declared_event_emits(qapp) -> None:
    root, registry, events = _build(qapp, WITH_CLICK)
    assert root is not None
    QTest.mouseClick(registry.lookup("demo.obox", "go").widget, Qt.MouseButton.LeftButton)
    assert events and events[0].event == "click"


def test_undeclared_event_is_silent(qapp) -> None:
    root, registry, events = _build(qapp, WITHOUT_CLICK)
    assert root is not None
    QTest.mouseClick(registry.lookup("demo.obox", "go").widget, Qt.MouseButton.LeftButton)
    assert events == []


def test_unknown_event_attribute_rejected(qapp) -> None:
    provider = build_provider()
    builder = Builder(
        "demo.obox", ComponentRegistry(), provider.component_types, lambda message: None
    )
    with pytest.raises(BuildError) as error:
        builder.build(parse_fragment('<Button id="go" on_dblclick="true" />'))
    assert "on_dblclick" in str(error.value)
