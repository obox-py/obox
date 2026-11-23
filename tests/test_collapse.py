"""折叠面板：标题、开合与子组件装配。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])

from obox.app import OboxApp  # noqa: E402
from tests.fake_provider import build_provider  # noqa: E402


def _assemble(oml: str, data: dict | None = None):
    obox = OboxApp(__import__("pathlib").Path(".").resolve(), provider=build_provider(), data_dir="tmp/probe-collapse", language="zh-CN")
    handle = {}
    obox.assemble_view("demo.obox", oml, data=data or {}, handle_out=handle)
    return obox, handle


def test_open_shows_body_and_toggles(qapp) -> None:
    obox, _ = _assemble('<Div id="r"><Collapse id="c1" title="账号" open="true"><Text id="t1" text="用户名" /></Collapse></Div>')
    panel = obox.registry.lookup("demo.obox", "c1")
    assert panel.is_open() is True
    assert panel.widget.findChild(type(panel._body)) is not None
    panel.toggle()
    assert panel.is_open() is False
    panel.set_open(True)
    assert panel.is_open() is True
    obox.shutdown()


def test_child_components_built(qapp) -> None:
    obox, _ = _assemble('<Div id="r"><Collapse id="c2" title="显示" open="false"><Input id="i1" value="{{v}}" /></Collapse></Div>', {"v": "abc"})
    field = obox.registry.lookup("demo.obox", "i1")
    assert field.text() == "abc"
    assert obox.registry.lookup("demo.obox", "c2").is_open() is False
    obox.shutdown()


def test_title_state(qapp) -> None:
    obox, _ = _assemble('<Div id="r"><Collapse id="c3" title="旧" /></Div>')
    panel = obox.registry.lookup("demo.obox", "c3")
    panel.set_title("新标题")
    assert panel.title() == "新标题"
    obox.shutdown()