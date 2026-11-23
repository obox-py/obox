from __future__ import annotations

import pytest

from obox.api.component import (
    COMPONENT_EVENT_MSG,
    COMPONENT_MODIFY_MSG,
    COMPONENT_STATE_MSG,
    ComponentEventMessage,
    ComponentModifyMessage,
    ComponentStateMessage,
    decode_message,
)
from obox.api.errors import ForbiddenOwner


def test_fixed_msg_ids() -> None:
    event = ComponentEventMessage(src="obox", dst="demo.obox", component_id="btn", event="click")
    state = ComponentStateMessage(src="demo.obox", dst="obox", component_id="inp", state_type="value")
    modify = ComponentModifyMessage(
        src="demo.obox", dst="obox", component_id="inp", state_type="value", value="x"
    )
    assert event.msg_id == COMPONENT_EVENT_MSG
    assert state.msg_id == COMPONENT_STATE_MSG
    assert modify.msg_id == COMPONENT_MODIFY_MSG


@pytest.mark.parametrize("base", [ComponentEventMessage, ComponentStateMessage, ComponentModifyMessage])
def test_component_messages_are_sealed(base) -> None:
    with pytest.raises(TypeError):
        type("Child", (base,), {})


def test_event_must_come_from_obox() -> None:
    with pytest.raises(ForbiddenOwner):
        ComponentEventMessage(src="demo.obox", dst="obox", component_id="btn", event="click")


def test_state_request_targets_obox() -> None:
    with pytest.raises(ForbiddenOwner):
        ComponentStateMessage(src="demo.obox", dst="other.x", component_id="inp", state_type="value")


def test_reply_targets_extension() -> None:
    reply = ComponentStateMessage(
        src="obox",
        dst="demo.obox",
        component_id="inp",
        state_type="value",
        value="hi",
        reply=True,
        correlation_id="c1",
    )
    assert reply.value == "hi"
    assert reply.reply


def test_unknown_event_rejected() -> None:
    with pytest.raises(ValueError):
        ComponentEventMessage(src="obox", dst="demo.obox", component_id="btn", event="unknown")


def test_decode_dispatch() -> None:
    message = ComponentModifyMessage(
        src="demo.obox", dst="obox", component_id="inp", state_type="value", value=3
    )
    decoded = decode_message(message.to_dict())
    assert isinstance(decoded, ComponentModifyMessage)
    assert decoded.value == 3
