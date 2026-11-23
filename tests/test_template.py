"""o-for / o-if 与局部更新。"""

from __future__ import annotations

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from obox.ui.template import ViewHandle
from tests.fake_provider import build_provider

GRID = """
<Div id="root">
  <Text id="title" text="{{label}}" />
  <Text id="empty" o-if="!apps.length" text="空" />
  <Div id="grid">
    <Card id="card-{{app.id}}" value="{{app.id}}" o-for="app in apps">
      <Text id="name-{{app.id}}" text="{{app.title}}" />
    </Card>
  </Div>
</Div>
"""


def _render(data):
    provider = build_provider()
    registry = ComponentRegistry()
    builder = Builder("demo.obox", registry, provider.component_types, data=data)
    root = builder.build(parse_fragment(GRID))
    handle = ViewHandle(builder, root, data)
    handle.attach(builder.bindings, builder.regions)
    return registry, handle, root


def test_for_renders_cards(qapp) -> None:
    data = {"label": "应用", "apps": [{"id": "a", "title": "A"}, {"id": "b", "title": "B"}]}
    registry, handle, _ = _render(data)
    assert registry.lookup("demo.obox", "card-a") is not None
    assert registry.lookup("demo.obox", "name-b").text() == "B"


def test_set_data_rebuilds_region_only(qapp) -> None:
    data = {"label": "应用", "apps": [{"id": "a", "title": "A"}]}
    registry, handle, _ = _render(data)
    title = registry.lookup("demo.obox", "title")
    handle.set_data({"apps": [{"id": "b", "title": "B"}, {"id": "c", "title": "C"}]})
    assert registry.lookup("demo.obox", "card-b") is not None
    assert registry.lookup("demo.obox", "name-c").text() == "C"
    assert registry.lookup("demo.obox", "title") is title


def test_if_toggles(qapp) -> None:
    data = {"label": "x", "apps": []}
    registry, handle, _ = _render(data)
    assert registry.lookup("demo.obox", "empty") is not None
    handle.set_data({"apps": [{"id": "a", "title": "A"}]})
    assert all(component != "empty" for component in [])
    assert "card-a" in [component.id for component in registry._by_owner["demo.obox"].values()]


def test_text_binding_updates_in_place(qapp) -> None:
    data = {"label": "旧", "apps": []}
    registry, handle, _ = _render(data)
    title = registry.lookup("demo.obox", "title")
    handle.set_data({"label": "新"})
    assert title.text() == "新"
    assert registry.lookup("demo.obox", "title") is title
