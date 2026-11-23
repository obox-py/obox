from __future__ import annotations

from obox.ui.qss import filter_stylesheet

SOURCE = """
#a { color: red; }
#b { color: blue; }
* { margin: 0; }
QPushButton { padding: 2px; }
#a:hover { color: green; }
"""


def test_keeps_own_selectors() -> None:
    kept, rejected = filter_stylesheet(SOURCE, {"a"})
    assert "#a {" in kept
    assert "#a:hover" in kept
    assert "#b" not in kept
    assert set(rejected) == {"#b", "*", "QPushButton"}


def test_empty_when_nothing_allowed() -> None:
    kept, rejected = filter_stylesheet(SOURCE, set())
    assert kept == ""
    assert len(rejected) == 5
