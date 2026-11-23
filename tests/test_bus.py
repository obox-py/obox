from __future__ import annotations

import pytest

from obox.api.component import ComponentModifyMessage, ComponentStateMessage
from obox.api.errors import BroadcastReply, RequestTimeout
from obox.api.message import Message
from obox.core.bus import MessageBus


class FakeTransport:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, data: dict) -> None:
        self.sent.append(data)


def test_local_dispatch() -> None:
    bus = MessageBus("obox")
    seen = []
    bus.on("PING", seen.append)
    bus.send(Message(src="obox", dst="obox", msg_id="PING"))
    assert len(seen) == 1


def test_remote_message_uses_transport() -> None:
    bus = MessageBus("obox")
    transport = FakeTransport()
    bus.attach_transport(transport)
    bus.send(Message(src="obox", dst="demo.obox", msg_id="PING"))
    assert transport.sent[0]["dst"] == "demo.obox"


def test_broadcast_hits_local_and_transport() -> None:
    bus = MessageBus("obox")
    transport = FakeTransport()
    bus.attach_transport(transport)
    seen = []
    bus.on("PING", seen.append)
    bus.send(Message(src="obox", dst="", msg_id="PING"))
    assert len(seen) == 1 and len(transport.sent) == 1


def test_request_reply_correlation() -> None:
    bus = MessageBus("demo.obox")
    transport = FakeTransport()
    bus.attach_transport(transport)
    message = ComponentStateMessage(src="demo.obox", dst="obox", component_id="inp", state_type="value")
    request = bus.request(message, timeout=1)
    sent = transport.sent[0]
    bus.receive(
        {
            "src": "obox",
            "dst": "demo.obox",
            "msg_id": "COMPONENT_STATE_MSG",
            "payload": {"id": "inp", "state_type": "value", "value": "hello"},
            "reply": True,
            "correlation_id": sent["correlation_id"],
        }
    )
    assert request.result() == {"id": "inp", "state_type": "value", "value": "hello"}
    assert bus.pending_count() == 0


def test_request_timeout_clears_table() -> None:
    bus = MessageBus("demo.obox")
    bus.attach_transport(FakeTransport())
    message = ComponentModifyMessage(
        src="demo.obox", dst="obox", component_id="inp", state_type="value", value=1
    )
    request = bus.request(message, timeout=0.05)
    with pytest.raises(RequestTimeout):
        request.result()
    assert bus.pending_count() == 0


def test_broadcast_reply_rejected() -> None:
    bus = MessageBus("obox")
    broadcast = Message(src="obox", dst="", msg_id="PING")
    with pytest.raises(BroadcastReply):
        bus.reply(broadcast, {"ok": True})
