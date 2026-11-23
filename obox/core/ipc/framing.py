"""帧编解码：4 字节大端长度前缀加 UTF-8 JSON。"""

from __future__ import annotations

import json
import struct
from typing import Any

from ...api.errors import FrameError

HEADER = struct.Struct(">I")
MAX_FRAME_BYTES = 4 * 1024 * 1024


def encode_frame(data: dict[str, Any]) -> bytes:
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_FRAME_BYTES:
        raise FrameError(f"帧过大：{len(body)} 字节")
    return HEADER.pack(len(body)) + body


class FrameDecoder:
    """把字节流切成消息；支持半包与一次多帧。"""

    def __init__(self, max_frame_bytes: int = MAX_FRAME_BYTES) -> None:
        self._buffer = bytearray()
        self._max = max_frame_bytes

    def feed(self, chunk: bytes) -> list[dict[str, Any]]:
        self._buffer.extend(chunk)
        frames: list[dict[str, Any]] = []
        while len(self._buffer) >= HEADER.size:
            (length,) = HEADER.unpack_from(self._buffer, 0)
            if length > self._max:
                self._buffer.clear()
                raise FrameError(f"帧长度 {length} 超过上限 {self._max}")
            if len(self._buffer) < HEADER.size + length:
                break
            body = bytes(self._buffer[HEADER.size : HEADER.size + length])
            del self._buffer[: HEADER.size + length]
            try:
                frames.append(json.loads(body.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise FrameError(f"帧内容不是合法 JSON：{exc}") from exc
        return frames
