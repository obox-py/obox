"""组件协议校验。"""

from __future__ import annotations

import pytest

from obox.ui.component_protocol import KitContractError, validate_component_class, validate_provider


class Good:
    supported_states = ("text",)
    state_accessors = {"text": ("text", "set_text")}
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def text(self) -> str:
        return ""

    def set_text(self, value) -> None:
        pass

    def on_click(self, callback) -> None:
        pass


def test_good_component_passes() -> None:
    validate_component_class("text", Good)


def test_missing_method_rejected() -> None:
    class Bad(Good):
        state_accessors = {"text": ("text", "set_missing")}

    with pytest.raises(KitContractError):
        validate_component_class("text", Bad)


def test_state_mapping_mismatch_rejected() -> None:
    class Bad(Good):
        supported_states = ("text", "value")

    with pytest.raises(KitContractError):
        validate_component_class("text", Bad)


def test_event_method_must_be_on_prefixed() -> None:
    class Bad(Good):
        event_methods = {"click": "click_handler"}

    with pytest.raises(KitContractError):
        validate_component_class("text", Bad)


def test_provider_requires_all_tags() -> None:
    class Provider:
        name = "p"
        version = "1"
        mode = "light"
        component_types = {"text": Good}
        stylesheet = "x"

    with pytest.raises(KitContractError):
        validate_provider(Provider)


def test_provider_requires_stylesheet() -> None:
    from tests.fake_provider import build_provider

    provider = build_provider()
    provider.stylesheet = ""
    with pytest.raises(KitContractError):
        validate_provider(provider)
