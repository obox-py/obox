"""控件过渡：切换后属性随时间变化。"""

from __future__ import annotations

from obox.qt import Qt
from obox.qt import QTest

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider


def _build(html: str):
    provider = build_provider()
    registry = ComponentRegistry()
    builder = Builder("demo.obox", registry, provider.component_types)
    root = builder.build(parse_fragment(html))
    return root, registry


def test_switch_knob_animates(qapp) -> None:
    root, registry = _build('<Switch id="s" />')
    assert root is not None
    switch = registry.lookup("demo.obox", "s").widget
    assert switch.knob == 0.0
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert switch.isChecked()
    QTest.qWait(260)
    assert switch.knob == 1.0


def test_checkbox_progress_animates(qapp) -> None:
    root, registry = _build('<Checkbox id="c" text="复选" />')
    assert root is not None
    box = registry.lookup("demo.obox", "c").widget
    QTest.mouseClick(box, Qt.MouseButton.LeftButton)
    QTest.qWait(220)
    assert box.progress == 1.0
