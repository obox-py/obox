"""视图锚点：消息、控制器与 sticky 装配。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from obox.api.component import decode_message
from obox.api.view import (
    ANCHOR_CHANGED_MSG,
    VIEW_SCROLL_MSG,
    anchor_changed_message,
    view_scroll_message,
)
from obox.ui.anchor import AnchorController

ROOT = Path(__file__).resolve().parent.parent


def _scene() -> tuple[QScrollArea, QWidget, dict[str, QWidget]]:
    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    sections: dict[str, QWidget] = {}
    for name in ("a", "b", "c"):
        box = QWidget()
        box.setObjectName(name)
        box.setFixedHeight(300)
        layout.addWidget(box)
        sections[name] = box
    layout.addStretch(1)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(content)
    area.resize(400, 400)
    area.show()
    QTest.qWait(10)
    return area, content, sections


def test_messages_round_trip() -> None:
    message = view_scroll_message("settings.obox", "settings.main", "section-about", 64, 600)
    assert message.msg_id == VIEW_SCROLL_MSG
    assert message.payload["anchor"] == "section-about"
    decoded = decode_message(message.to_dict())
    assert decoded.payload["offset"] == 64
    changed = anchor_changed_message("settings.main", "section-about", "settings.obox")
    assert changed.msg_id == ANCHOR_CHANGED_MSG
    assert decode_message(changed.to_dict()).payload["anchor"] == "section-about"


def test_scroll_to_anchor_applies_offset(qapp) -> None:
    area, content, sections = _scene()
    controller = AnchorController(area, content, offset=64, duration=1)
    assert controller.scroll_to("b")
    QTest.qWait(80)
    assert area.verticalScrollBar().value() == sections["b"].y() - 64


def test_scroll_clamps_to_bounds(qapp) -> None:
    area, content, _sections = _scene()
    controller = AnchorController(area, content, offset=0, duration=1)
    assert controller.scroll_to("c")
    QTest.qWait(80)
    assert area.verticalScrollBar().value() == area.verticalScrollBar().maximum()


def test_current_anchor_top_middle_bottom(qapp) -> None:
    area, content, sections = _scene()
    controller = AnchorController(area, content, offset=64)
    bar = area.verticalScrollBar()
    bar.setValue(0)
    assert controller.current_anchor() == "a"
    bar.setValue(sections["b"].y() - 10)
    assert controller.current_anchor() == "b"
    bar.setValue(bar.maximum())
    assert controller.current_anchor() == "c"


def test_anchor_signal_only_on_change(qapp) -> None:
    area, content, _sections = _scene()
    controller = AnchorController(area, content, offset=64)
    seen: list[str] = []
    controller.anchor_changed.connect(seen.append)
    bar = area.verticalScrollBar()
    bar.setValue(0)
    controller._refresh()
    bar.setValue(5)
    controller._refresh()
    assert seen == ["a"]


def test_unknown_anchor_returns_false(qapp) -> None:
    area, content, _sections = _scene()
    controller = AnchorController(area, content)
    assert not controller.scroll_to("missing")

def test_mount_extracts_sticky_and_routes_scroll(qapp, tmp_path) -> None:
    from obox.app import OboxApp
    from obox.api.message import Message
    from tests.fake_provider import build_provider

    obox = OboxApp(ROOT, provider=build_provider(), data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    directory = tmp_path / "ext"
    (directory / "views").mkdir(parents=True)
    (directory / "views" / "main.oml").write_text(
        '<Div id="root">'
        '<Div id="head" sticky="true"><Text id="head-text" text="目录" /></Div>'
        '<Div id="a"><Text id="a-text" text="A" /></Div>'
        '<Div id="b"><Text id="b-text" text="B" /></Div>'
        "</Div>",
        encoding="utf-8",
    )
    obox._extension_dirs["ext.obox"] = directory
    spec = {
        "view_id": "ext.main",
        "extension_id": "ext.obox",
        "html": "views/main.oml",
        "directory": str(directory),
        "container": "sidebar",
        "title": "测试",
    }
    assert obox._mount_view(spec) is not None
    wrapper = obox.window._views["ext.main"]
    assert wrapper.objectName() == "obox-view-with-sticky"
    scroll = wrapper.findChild(QScrollArea)
    assert scroll is not None
    head = obox.registry.lookup("ext.obox", "head").widget
    assert head.parent() is wrapper
    assert scroll.widget() is not head

    _owner, controller = obox._anchors["ext.main"]
    calls: list[tuple[str, int, int]] = []
    controller.scroll_to = lambda anchor, offset=None, duration=None: calls.append(
        (anchor, int(offset or 0), int(duration or 0))
    ) or True
    obox._on_view_scroll(Message(
        src="ext.obox",
        dst="obox",
        msg_id=VIEW_SCROLL_MSG,
        payload={"view_id": "ext.main", "anchor": "b", "offset": 0, "duration": 1},
    ))
    assert calls == [("b", 0, 1)]
    obox.shutdown()