"""light 套件对 obox 暴露的提供者：只提供样式与调色板。"""

from __future__ import annotations

from pathlib import Path

import re

from .theme import (
    DANGER,
    ICON_ACTIVE,
    ICON_MUTED,
    PALETTE,
    SPACING,
    TITLE_ACTIVE,
    TITLE_MUTED,
)

_TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")


def _style_path() -> Path | None:
    """源码态与 pyd 态的目录布局不同，向上找 styles.qss。"""
    parent = Path(__file__).resolve().parent
    for candidate in (parent, *list(parent.parents)[:4]):
        path = candidate / "styles.qss"
        if path.is_file():
            return path
    return None


def load_stylesheet() -> str:
    """读取 styles.qss，把双花括号包裹的调色板键换成实际取值。"""
    path = _style_path()
    if path is None:
        return ""
    try:
        template = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return _TOKEN.sub(lambda match: str(PALETTE.get(match.group(1), match.group(0))), template)


class LightProvider:
    """只依赖 PySide6，不 import obox；组件实现由 obox 提供。"""

    name = "light"
    version = "1.0.0"
    mode = "light"
    contract = 1
    stylesheet = load_stylesheet()
    palette = PALETTE
    font_dir = Path(__file__).resolve().parent / "fonts"
    spacing = SPACING
    icon_muted = ICON_MUTED
    icon_active = ICON_ACTIVE
    title_muted = TITLE_MUTED
    title_active = TITLE_ACTIVE
    danger = DANGER