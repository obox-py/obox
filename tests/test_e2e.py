from __future__ import annotations

from pathlib import Path

from obox.qt import Qt
from obox.qt import QTest

import pytest

from obox.app import OboxApp

ROOT = Path(__file__).resolve().parent.parent
PYP = ROOT / ".theme" / "light" / "light.pyd"

pytestmark = pytest.mark.skipif(
    not PYP.exists() or not (ROOT / "extensions" / "demo" / "extension.json").is_file(),
    reason="需要 .theme/light/light.pyd 与 demo 示例扩展",
)


def _start(qtbot) -> OboxApp:
    obox = OboxApp(ROOT, language="zh-CN")
    obox.start()
    qtbot.waitUntil(lambda: "demo.main" in obox.window.view_ids(), timeout=30000)
    return obox


def test_click_reaches_extension_and_updates_state(qtbot) -> None:
    obox = _start(qtbot)
    try:
        status = obox.registry.lookup("demo.obox", "demo-status")
        getter = status.state_accessors["text"][0]
        assert getattr(status, getter)() == "等待点击"
        button = obox.registry.lookup("demo.obox", "demo-btn")
        QTest.mouseClick(button.widget, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: getattr(status, getter)() == "按钮被点击了", timeout=15000)
    finally:
        obox.supervisor.stop()


def test_host_restart_restores_extension(qtbot) -> None:
    obox = _start(qtbot)
    states: list[str] = []
    obox.supervisor.state_changed.connect(lambda state, detail: states.append(state))
    try:
        process = obox.supervisor._process
        process.kill()
        process.waitForFinished(3000)
        qtbot.waitUntil(lambda: "restarting" in states, timeout=15000)
        qtbot.waitUntil(lambda: "ready" in states[states.index("restarting"):], timeout=30000)
        status = obox.registry.lookup("demo.obox", "demo-status")
        getter = status.state_accessors["text"][0]
        button = obox.registry.lookup("demo.obox", "demo-btn")
        QTest.mouseClick(button.widget, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: getattr(status, getter)() == "按钮被点击了", timeout=15000)
    finally:
        obox.supervisor.stop()
