"""注销组件时释放挂在窗口上的控件。"""

from __future__ import annotations

from obox.ui.registry import ComponentRegistry


class FakeComponent:
    def __init__(self) -> None:
        self.detached = False

    def detach(self) -> None:
        self.detached = True


def test_unregister_owner_detaches(qapp=None) -> None:
    registry = ComponentRegistry()
    component = FakeComponent()
    registry.register("demo.obox", "x", component)
    registry.unregister_owner("demo.obox")
    assert component.detached


def test_unregister_detaches(qapp=None) -> None:
    registry = ComponentRegistry()
    component = FakeComponent()
    registry.register("demo.obox", "x", component)
    registry.unregister("demo.obox", "x")
    assert component.detached
