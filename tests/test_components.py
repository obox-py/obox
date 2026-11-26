from __future__ import annotations

import pytest
from obox.qt import QEvent, QPoint, QPointF, Qt
from obox.qt import QColor, QMouseEvent
from obox.qt import QTest
from obox.qt import QApplication, QWidget

from obox.ui.builder import Builder
from obox.ui.component_protocol import REQUIRED_TAGS, validate_provider
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider
from obox.ui.components.button import ButtonWidget


def test_every_tag_is_registered(qapp) -> None:
    provider = build_provider()
    validate_provider(provider)
    assert len(provider.component_types) == 23
    assert set(REQUIRED_TAGS) <= set(provider.component_types)
    assert "chart" in provider.component_types


@pytest.mark.parametrize("tag", REQUIRED_TAGS)
def test_component_instantiable(qapp, tag: str) -> None:
    provider = build_provider()
    attrs = {"text": "标题", "options": "甲,乙", "items": "概览,详情", "columns": "名称,数量"}
    component = provider.component_types[tag](f"{tag}-1", "demo.obox", attrs)
    assert component.id == f"{tag}-1"


def test_input_value_via_accessors(qapp) -> None:
    field = build_provider().component_types["input"]("i1", "demo.obox", {"value": "x"})
    getter, setter = field.state_accessors["value"]
    assert getattr(field, getter)() == "x"
    getattr(field, setter)("y")
    assert getattr(field, getter)() == "y"


def test_checkbox_checked(qapp) -> None:
    check = build_provider().component_types["checkbox"]("c1", "demo.obox", {"checked": "true"})
    getter, setter = check.state_accessors["checked"]
    assert getattr(check, getter)() is True
    getattr(check, setter)(False)
    assert getattr(check, getter)() is False


def test_table_round_trip(qapp) -> None:
    table = build_provider().component_types["table"]("tb1", "demo.obox", {"columns": "名称,数量"})
    getter, setter = table.state_accessors["value"]
    getattr(table, setter)([["a", "1"], ["b", "2"]])
    assert getattr(table, getter)() == [["a", "1"], ["b", "2"]]


def test_modal_visibility(qapp) -> None:
    modal = build_provider().component_types["modal"]("m1", "demo.obox", {"text": "hi"})
    getter, setter = modal.state_accessors["visible"]
    assert getattr(modal, getter)() is False

def _modal(fragment: str):
    provider = build_provider()
    registry = ComponentRegistry()
    events: list = []
    builder = Builder("demo.obox", registry, provider.component_types, events.append)
    root = builder.build(parse_fragment(fragment))
    root.resize(600, 400)
    root.show()
    QTest.qWait(10)
    return registry.lookup("demo.obox", "m"), root, registry, events


def _card(modal) -> QWidget:
    card = modal.widget.findChild(QWidget, "obox-modal-card")
    assert card is not None
    return card


def test_modal_accepts_children_and_routes_buttons(qapp) -> None:
    modal, _root, registry, _events = _modal(
        '<Modal id="m" title="标题"><Text id="t" text="正文" /><Button id="ok" text="确定" /></Modal>'
    )
    modal.set_visible(True)
    QTest.qWait(10)
    card = _card(modal)
    text = registry.lookup("demo.obox", "t").widget
    button = registry.lookup("demo.obox", "ok").widget
    assert card.isAncestorOf(text) and card.isAncestorOf(button)
    assert button.mapTo(card, QPoint(0, 0)).y() > text.mapTo(card, QPoint(0, 0)).y()


def test_modal_footer_button_closes_with_value(qapp) -> None:
    modal, _root, registry, events = _modal(
        '<Modal id="m" title="标题" on_close="true"><Text id="t" text="正文" />'
        '<Button id="ok" text="保存" /></Modal>'
    )
    modal.set_visible(True)
    QTest.qWait(10)
    button = registry.lookup("demo.obox", "ok").widget
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    QTest.qWait(10)
    assert events[-1].payload["reason"] == "button"
    assert events[-1].payload["value"] == "保存"


def test_modal_esc_closes_with_reason(qapp) -> None:
    modal, _root, _registry, events = _modal('<Modal id="m" text="内容" on_close="true" />')
    modal.set_visible(True)
    QTest.qWait(10)
    QTest.keyClick(modal.widget, Qt.Key.Key_Escape)
    QTest.qWait(10)
    assert events and events[-1].event == "close"
    assert events[-1].payload["reason"] == "esc"


def test_modal_overlay_click_needs_opt_in(qapp) -> None:
    modal, _root, _registry, events = _modal('<Modal id="m" text="内容" on_close="true" />')
    modal.set_visible(True)
    QTest.qWait(10)
    QTest.mouseClick(modal.widget, Qt.MouseButton.LeftButton, pos=QPoint(2, 2))
    assert not events
    modal.set_visible(False)

    opted, _root2, _registry2, events2 = _modal(
        '<Modal id="m" text="内容" close_on_overlay="true" on_close="true" />'
    )
    opted.set_visible(True)
    QTest.qWait(10)
    QTest.mouseClick(opted.widget, Qt.MouseButton.LeftButton, pos=QPoint(2, 2))
    QTest.qWait(10)
    assert events2 and events2[-1].payload["reason"] == "overlay"


def test_modal_old_attrs_render_default_button(qapp) -> None:
    modal, _root, _registry, events = _modal(
        '<Modal id="m" title="提示" text="旧写法" on_close="true" />'
    )
    modal.set_visible(True)
    QTest.qWait(10)
    buttons = modal.widget.findChildren(ButtonWidget)
    assert [button.text() for button in buttons] == ["知道了"]
    QTest.mouseClick(buttons[0], Qt.MouseButton.LeftButton)
    QTest.qWait(10)
    payload = events[-1].payload
    assert payload["reason"] == "button"
    assert payload["value"] == "知道了"


def test_modal_size_defaults_and_clamp(qapp) -> None:
    default_modal, _root, _registry, _events = _modal('<Modal id="m" text="内容" />')
    default_modal.set_visible(True)
    QTest.qWait(10)
    assert _card(default_modal).width() == 420

    narrow, _root2, _registry2, _events2 = _modal('<Modal id="m" text="内容" width="100" />')
    narrow.set_visible(True)
    QTest.qWait(10)
    assert _card(narrow).width() == 320

    wide, _root3, _registry3, _events3 = _modal('<Modal id="m" text="内容" width="5000" />')
    wide.set_visible(True)
    QTest.qWait(10)
    assert _card(wide).width() == int(600 * 0.9)


def test_modal_drag_resize_clamps_to_minimum(qapp) -> None:
    modal, _root, _registry, _events = _modal('<Modal id="m" text="内容" width="500" />')
    modal.set_visible(True)
    QTest.qWait(10)
    card = _card(modal)
    start = QPointF(card.width() - 4, card.height() - 4)
    target = QPointF(card.width() - 400, card.height() - 300)
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress, start, start, Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(card, press)
    move = QMouseEvent(
        QEvent.Type.MouseMove, target, target, Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(card, move)
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease, target, target, Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(card, release)
    assert card.width() == 320
    assert card.height() == 160


def test_modal_variant_recolors_first_button(qapp) -> None:
    modal, _root, _registry, _events = _modal(
        '<Modal id="m" variant="danger" title="危险"><Button id="ok" text="删除" /></Modal>'
    )
    modal.set_visible(True)
    QTest.qWait(10)
    button = modal.widget.findChildren(ButtonWidget)[0]
    image = button.grab().toImage()
    assert QColor.fromRgba(image.pixel(3, image.height() // 2)).name() == "#d93026"


def test_button_set_variant_repaints(qapp) -> None:
    button = build_provider().component_types["button"]("b1", "demo.obox", {"text": "确定"}).widget
    button.resize(120, 32)
    button.show()
    QTest.qWait(10)
    plain = QColor.fromRgba(button.grab().toImage().pixel(36, 16)).name()
    button.set_variant("primary")
    QTest.qWait(10)
    picked = QColor.fromRgba(button.grab().toImage().pixel(36, 16)).name()
    assert plain != picked
    tint = QColor(picked)
    assert tint.blue() > 200 and tint.red() < 90