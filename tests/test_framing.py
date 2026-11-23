from __future__ import annotations

import pytest

from obox.api.errors import FrameError
from obox.core.ipc.framing import FrameDecoder, encode_frame


def test_round_trip() -> None:
    decoder = FrameDecoder()
    frames = decoder.feed(encode_frame({"a": 1, "名字": "值"}))
    assert frames == [{"a": 1, "名字": "值"}]


def test_half_packet() -> None:
    payload = encode_frame({"a": 1})
    decoder = FrameDecoder()
    assert decoder.feed(payload[:3]) == []
    assert decoder.feed(payload[3:]) == [{"a": 1}]


def test_multiple_frames() -> None:
    decoder = FrameDecoder()
    frames = decoder.feed(encode_frame({"n": 1}) + encode_frame({"n": 2}))
    assert [frame["n"] for frame in frames] == [1, 2]


def test_oversized_frame_rejected() -> None:
    decoder = FrameDecoder(max_frame_bytes=8)
    with pytest.raises(FrameError):
        decoder.feed(encode_frame({"payload": "x" * 64}))


def test_invalid_json_rejected() -> None:
    decoder = FrameDecoder()
    with pytest.raises(FrameError):
        decoder.feed(b"\x00\x00\x00\x03abc")
