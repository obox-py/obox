"""按钮过渡：悬停进度随时间变化。"""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QEnterEvent
from PySide6.QtTest import QTest

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider


def test_button_hover_animates(qapp) -> None:
    provider = build_provider()
    registry = ComponentRegistry()
    builder = Builder("demo.obox", registry, provider.component_types)
    root = builder.build(parse_fragment('<Button id="b" text="悬停" />'))
    button = registry.lookup("demo.obox", "b").widget
    assert root is not None
    assert button.hover == 0.0
    enter = QEnterEvent(QPointF(4, 4), QPointF(4, 4), QPointF(4, 4))
    button.enterEvent(enter)
    QTest.qWait(220)
    assert button.hover == 1.0
