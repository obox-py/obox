"""dark 主题套件：深色外观，与 light 同契约。

提供 create_ui_provider 作为 pyd 入口，obox 加载后按组件映射与样式渲染界面。
"""

from __future__ import annotations

from .provider import DarkProvider


def create_ui_provider() -> DarkProvider:
    return DarkProvider()
