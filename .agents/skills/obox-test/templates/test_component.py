"""组件测试骨架：用假 provider + Builder，不启动窗口。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider


def test_widget_behavior(qapp) -> None:
    provider = build_provider()
    registry = ComponentRegistry()
    events: list = []
    builder = Builder("demo.obox", registry, provider.component_types, events.append)
    root = builder.build(parse_fragment('<Button id="go" text="点我" on_click="true" />'))
    assert root is not None

    button = registry.lookup("demo.obox", "go")
    QTest.mouseClick(button.widget, Qt.MouseButton.LeftButton)
    assert events and events[-1].event == "click"
