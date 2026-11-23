"""间距参数：provider 暴露、装配器读取。"""

from __future__ import annotations

from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider


def test_provider_exposes_spacing(qapp) -> None:
    spacing = build_provider().spacing
    assert spacing["margin"] == 20
    assert spacing["gap"] == 16
    assert 28 <= spacing["control_height"] <= 36


def test_builder_uses_spacing(qapp) -> None:
    provider = build_provider()
    builder = Builder(
        "demo.obox",
        ComponentRegistry(),
        provider.component_types,
        spacing=provider.spacing,
    )
    root = builder.build(parse_fragment('<Div id="root"><Text id="t" text="x" /></Div>'))
    layout = root.layout()
    margins = layout.contentsMargins()
    assert margins.left() == 20
    assert layout.spacing() == 16
