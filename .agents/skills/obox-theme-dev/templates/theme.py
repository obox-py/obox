"""__NAME__ 套件的视觉参数。"""

from __future__ import annotations

BACKGROUND = "#f7f6f4"
SURFACE = "#fffefc"
SURFACE_MUTED = "#f0eeea"
TEXT = "#2b2a28"
TEXT_MUTED = "#6f6b64"
LINE = "rgba(43, 42, 40, 0.10)"
ACCENT = "#5b7f95"
ACCENT_TEXT = "#ffffff"
ACCENT_SOFT = "rgba(91, 127, 149, 0.12)"
CARD_SURFACE = "#fffefc"
CARD_BORDER = "rgba(43, 42, 40, 0.22)"
ICON_MUTED = "#6f6b64"
ICON_ACTIVE = "#5b7f95"

RADIUS_CONTROL = 10
RADIUS_CARD = 16
CONTROL_HEIGHT = 38
SPACING = {"margin": 20, "gap": 16, "control_height": CONTROL_HEIGHT}

STYLESHEET = f"""
QWidget {{
    color: {TEXT};
    font-family: "HarmonyOS Sans SC", "Noto Sans SC", "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 14px;
}}
#obox-window {{ background: {BACKGROUND}; }}
#obox-body, #obox-home, #obox-view-root {{ background: {BACKGROUND}; }}
#obox-rail {{ background: {SURFACE_MUTED}; }}
#obox-bottom {{ background: {SURFACE_MUTED}; }}
#obox-bottom-view {{ background: transparent; }}
"""
