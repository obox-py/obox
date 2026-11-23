"""light 主题套件：柔和的浅色外观。

提供 create_ui_provider 作为 pyd 入口，obox 加载后按组件映射与样式渲染界面。
"""

from __future__ import annotations

from .provider import LightProvider


def create_ui_provider() -> LightProvider:
    return LightProvider()
