from __future__ import annotations

import pytest

from obox.api.message import Message, is_identity


def test_round_trip() -> None:
    message = Message(src="obox", dst="demo.obox", msg_id="PING", payload={"n": 1})
    restored = Message.from_dict(message.to_dict())
    assert restored == message


def test_broadcast_when_dst_empty() -> None:
    assert Message(src="obox", dst="", msg_id="PING").is_broadcast


@pytest.mark.parametrize("bad", ["", "demo", "demo.", ".obox", "a.b.c"])
def test_rejects_bad_src(bad: str) -> None:
    assert not is_identity(bad)
    with pytest.raises(ValueError):
        Message(src=bad, dst="obox", msg_id="PING")


def test_reply_requires_correlation() -> None:
    with pytest.raises(ValueError):
        Message(src="obox", dst="demo.obox", msg_id="PING", reply=True)


def test_reply_cannot_be_broadcast() -> None:
    with pytest.raises(ValueError):
        Message(src="obox", dst="", msg_id="PING", reply=True, correlation_id="abc")


def test_from_dict_requires_fields() -> None:
    with pytest.raises(ValueError):
        Message.from_dict({"src": "obox", "dst": "demo.obox"})
