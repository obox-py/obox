"""测试用的 provider：直接导入 light 套件源码，不依赖 pyd。"""

from __future__ import annotations

from theme.light import create_ui_provider

from obox.ui.components import COMPONENT_TYPES


def build_provider():
    provider = create_ui_provider()
    provider.component_types = COMPONENT_TYPES
    return provider
