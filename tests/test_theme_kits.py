"""两套 kit 的契约一致性。"""

from __future__ import annotations

import pytest

from obox.ui.component_protocol import REQUIRED_TAGS, validate_component_table, validate_provider
from obox.ui.components import COMPONENT_TYPES
from theme.dark import create_ui_provider as create_dark
from theme.light import create_ui_provider as create_light


@pytest.mark.parametrize("factory,mode", [(create_light, "light"), (create_dark, "dark")])
def test_provider_valid(qapp, factory, mode: str) -> None:
    provider = factory()
    validate_provider(provider)
    assert provider.mode == mode
    assert "{{" not in provider.stylesheet
    assert set(REQUIRED_TAGS) <= set(COMPONENT_TYPES)
    validate_component_table(COMPONENT_TYPES)


def test_both_kits_share_tags_and_states(qapp) -> None:
    light = create_light()
    dark = create_dark()
    assert light.stylesheet != dark.stylesheet
    assert light.palette["ACCENT"] != dark.palette["ACCENT"]


def test_input_value_maps_to_text_method(qapp) -> None:
    field = COMPONENT_TYPES["input"]("i1", "demo.obox", {"value": "hi"})
    getter, setter = field.state_accessors["value"]
    assert getattr(field, getter)() == "hi"
    getattr(field, setter)("yo")
    assert getattr(field, getter)() == "yo"

def test_stylesheet_comes_from_qss_file(qapp) -> None:
    from pathlib import Path

    from theme.light import create_ui_provider

    qss = Path("theme/light/styles.qss")
    assert qss.is_file()
    assert "{{ACCENT}}" in qss.read_text(encoding="utf-8")
    provider = create_ui_provider()
    assert "#2f6bee" in provider.stylesheet
