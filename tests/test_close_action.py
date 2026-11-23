"""关闭决策纯函数。"""

from __future__ import annotations

from obox.ui.close_action import decide_close


def test_ask_cancel_keeps_window() -> None:
    assert decide_close("ask", "cancel", False) == ("cancel", None)


def test_ask_tray_remember() -> None:
    assert decide_close("ask", "tray", True) == ("tray", "tray")


def test_ask_quit_without_remember() -> None:
    assert decide_close("ask", "quit", False) == ("quit", None)


def test_direct_actions_ignore_choice() -> None:
    assert decide_close("tray", "quit", True) == ("tray", None)
    assert decide_close("quit", "tray", True) == ("quit", None)


def test_invalid_action_falls_back_to_ask() -> None:
    assert decide_close("bogus", "tray", False) == ("tray", None)
