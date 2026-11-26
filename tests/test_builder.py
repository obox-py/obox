from __future__ import annotations

import pytest
from obox.qt import Qt
from obox.qt import QTest

from obox.api.errors import ComponentConflict
from obox.ui.builder import BuildError, Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider

HTML = """
<Div id="root">
  <Text id="title" text="标题" />
  <Button id="go" text="走" on_click="true" />
</Div>
"""


def _builder(registry: ComponentRegistry, sink=None) -> Builder:
    return Builder("demo.obox", registry, build_provider().component_types, sink)


def test_build_registers_components(qapp) -> None:
    registry = ComponentRegistry()
    builder = _builder(registry)
    root = builder.build(parse_fragment(HTML))
    assert root is not None
    assert registry.lookup("demo.obox", "go").text() == "走"
    assert sorted(builder.created_ids) == ["go", "root", "title"]


def test_unknown_tag_reports_position(qapp) -> None:
    with pytest.raises(BuildError) as error:
        _builder(ComponentRegistry()).build(parse_fragment('<Fancy id="x" />'))
    assert "fancy" in str(error.value)
    assert "第 1 行" in str(error.value)


def test_missing_id_rejected(qapp) -> None:
    with pytest.raises(BuildError):
        _builder(ComponentRegistry()).build(parse_fragment("<Div></Div>"))


def test_conflict_rolls_back(qapp) -> None:
    registry = ComponentRegistry()
    builder = _builder(registry)
    builder.build(parse_fragment('<Div id="root"></Div>'))
    with pytest.raises(ComponentConflict):
        builder.build(parse_fragment('<Div id="root"></Div>'))
    assert registry.count("demo.obox") == 1


def test_click_emits_event(qapp) -> None:
    registry = ComponentRegistry()
    events = []
    builder = _builder(registry, events.append)
    root = builder.build(parse_fragment(HTML))
    assert root is not None
    button = registry.lookup("demo.obox", "go")
    QTest.mouseClick(button.widget, Qt.MouseButton.LeftButton)
    assert events and events[0].event == "click"
    assert events[0].dst == "demo.obox"
