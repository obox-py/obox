"""卡片：独立使用时的点击事件与内容布局。"""

from __future__ import annotations

from obox.qt import Qt
from obox.qt import QColor
from obox.qt import QTest
from obox.qt import QLabel

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider


def _build(html: str):
    provider = build_provider()
    registry = ComponentRegistry()
    events: list = []
    builder = Builder("demo.obox", registry, provider.component_types, events.append)
    root = builder.build(parse_fragment(html))
    return root, registry, events


def test_standalone_card_click(qapp) -> None:
    root, registry, events = _build(
        '<Card id="free" value="x" on_click="true"><Text id="t" text="内容" /></Card>'
    )
    assert root is not None
    card = registry.lookup("demo.obox", "free")
    QTest.mouseClick(card.widget, Qt.MouseButton.LeftButton)
    assert events and events[-1].id == "free"
    assert events[-1].event == "click"


def test_card_lays_out_children(qapp) -> None:
    root, registry, _ = _build(
        '<Card id="free"><Text id="a" text="第一行" /><Text id="b" text="第二行" /></Card>'
    )
    root.resize(400, 200)
    root.show()
    QTest.qWait(20)
    first = registry.lookup("demo.obox", "a").widget
    second = registry.lookup("demo.obox", "b").widget
    assert first.geometry().y() < second.geometry().y()

def test_selected_card_has_no_check_mark(qapp) -> None:
    root, registry, _ = _build(
        '<Choice id="c" mode="single"><Card id="a" value="甲"><Text id="t" text="甲项" /></Card></Choice>'
    )
    root.resize(400, 200)
    root.show()
    QTest.qWait(20)
    card = registry.lookup("demo.obox", "a")
    card.set_selected(True)
    texts = [label.text() for label in card.widget.findChildren(QLabel)]
    assert "✓" not in texts


def test_selected_card_fill_changes(qapp) -> None:
    root, registry, _ = _build('<Card id="free"><Text id="t" text="内容" /></Card>')
    root.resize(400, 200)
    root.show()
    QTest.qWait(20)
    card = registry.lookup("demo.obox", "free")
    card.set_selected(False)
    plain_image = card.widget.grab().toImage()
    plain = QColor.fromRgba(plain_image.pixel(4, plain_image.height() - 4)).name()
    card.set_selected(True)
    picked_image = card.widget.grab().toImage()
    picked = QColor.fromRgba(picked_image.pixel(4, picked_image.height() - 4)).name()
    assert plain == "#ffffff"
    assert picked == "#eaf1fe"
