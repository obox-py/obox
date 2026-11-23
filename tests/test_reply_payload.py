from __future__ import annotations

import pytest

from obox.api.component import ComponentModifyMessage, decode_message
from obox.core.bus import MessageBus


class FakeTransport:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, data: dict) -> None:
        self.sent.append(data)


def test_error_survives_reply_encoding() -> None:
    client = MessageBus("demo.obox")
    outbox = FakeTransport()
    client.attach_transport(outbox)
    request = client.request(
        ComponentModifyMessage(
            src="demo.obox", dst="obox", component_id="inp", state_type="value", value=1
        ),
        timeout=1,
    )

    server = MessageBus("obox")
    inbox = FakeTransport()
    server.attach_transport(inbox)
    server.reply(decode_message(outbox.sent[0]), {"error": "E_FORBIDDEN_OWNER", "message": "越权"})

    client.receive(inbox.sent[0])
    with pytest.raises(RuntimeError) as error:
        request.result()
    assert "E_FORBIDDEN_OWNER" in str(error.value)


def test_decode_keeps_extra_payload() -> None:
    decoded = decode_message(
        {
            "src": "obox",
            "dst": "demo.obox",
            "msg_id": "COMPONENT_MODIFY_MSG",
            "payload": {
                "id": "a",
                "state_type": "value",
                "value": 1,
                "error": "E_X",
                "message": "m",
            },
            "reply": True,
            "correlation_id": "c",
        }
    )
    assert decoded.payload["error"] == "E_X"
    assert decoded.payload["message"] == "m"
