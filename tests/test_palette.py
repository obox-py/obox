"""调色板：默认值、注入与回退。"""

from __future__ import annotations

from obox.ui import palette


def test_defaults_present() -> None:
    palette.reset()
    assert palette.ACCENT == "#2f6bee"
    assert palette.RADIUS_CARD == 2
    assert palette.CONTROL_HEIGHT == 32


def test_set_active_overrides_known_keys() -> None:
    palette.reset()
    palette.set_active({"ACCENT": "#5b8def", "TEXT": "#f2f3f5", "UNKNOWN": "#000000"})
    assert palette.ACCENT == "#5b8def"
    assert palette.TEXT == "#f2f3f5"
    assert not hasattr(palette, "UNKNOWN")


def test_set_active_none_restores_defaults() -> None:
    palette.set_active({"ACCENT": "#000000"})
    palette.set_active(None)
    assert palette.ACCENT == "#2f6bee"


def test_current_returns_copy() -> None:
    palette.reset()
    snapshot = palette.current()
    snapshot["ACCENT"] = "#000000"
    assert palette.ACCENT == "#2f6bee"
