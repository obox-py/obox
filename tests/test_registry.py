from __future__ import annotations

import pytest

from obox.api.errors import ComponentConflict, ComponentNotFound
from obox.ui.registry import ComponentRegistry


class FakeComponent:
    def __init__(self, owner: str, component_id: str) -> None:
        self.owner = owner
        self.id = component_id


def test_conflict_within_owner() -> None:
    registry = ComponentRegistry()
    registry.register("demo.obox", "btn", FakeComponent("demo.obox", "btn"))
    with pytest.raises(ComponentConflict):
        registry.register("demo.obox", "btn", FakeComponent("demo.obox", "btn"))


def test_same_id_across_owners() -> None:
    registry = ComponentRegistry()
    registry.register("demo.obox", "btn", FakeComponent("demo.obox", "btn"))
    registry.register("other.x", "btn", FakeComponent("other.x", "btn"))
    assert registry.count() == 2


def test_lookup_missing() -> None:
    with pytest.raises(ComponentNotFound):
        ComponentRegistry().lookup("demo.obox", "nope")


def test_unregister_owner() -> None:
    registry = ComponentRegistry()
    registry.register("demo.obox", "btn", FakeComponent("demo.obox", "btn"))
    registry.unregister_owner("demo.obox")
    assert registry.count() == 0
