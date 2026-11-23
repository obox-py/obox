"""组件绘制用的调色板；由 app 在应用主题时注入，组件只读这里的值。"""

from __future__ import annotations

from typing import Any

DEFAULTS: dict[str, Any] = {
    "BACKGROUND": "#f4f5f7",
    "SURFACE": "#ffffff",
    "SURFACE_MUTED": "#f7f8fa",
    "TEXT": "#1d2129",
    "TEXT_MUTED": "#86909c",
    "LINE": "#e2e5eb",
    "ACCENT": "#2f6bee",
    "ACCENT_TEXT": "#ffffff",
    "ACCENT_SOFT": "#eaf1fe",
    "CARD_SURFACE": "#ffffff",
    "CARD_BORDER": "#e2e5eb",
    "DANGER": "#d93026",
    "SUCCESS": "#00b42a",
    "WARNING": "#ff7d00",
    "INPUT_BORDER": "#d9dfe8",
    "PLACEHOLDER": "#a0a2a5",
    "RADIUS_CONTROL": 2,
    "RADIUS_CARD": 2,
    "CONTROL_HEIGHT": 32,
    "FONT_FAMILY": "HarmonyOS Sans SC",
}
_ACTIVE: dict[str, Any] = dict(DEFAULTS)


def set_active(values: dict[str, Any] | None) -> None:
    """应用一套主题的调色板；未知键忽略，缺省键保留默认值。"""
    _ACTIVE.clear()
    _ACTIVE.update(DEFAULTS)
    for key, value in (values or {}).items():
        if key in DEFAULTS and value is not None:
            _ACTIVE[key] = value


def reset() -> None:
    set_active(None)


def current() -> dict[str, Any]:
    return dict(_ACTIVE)


def __getattr__(name: str) -> Any:
    if name in _ACTIVE:
        return _ACTIVE[name]
    raise AttributeError(name)
