"""视图数据回注（任意 owner 的任意键）。"""

from __future__ import annotations

from typing import Any

from .message import OB_BOX, Message

VIEW_DATA_MSG = "VIEW_DATA_MSG"
VIEW_SCROLL_MSG = "VIEW_SCROLL_MSG"
ANCHOR_CHANGED_MSG = "ANCHOR_CHANGED_MSG"


def view_data_message(src: str, view_id: str, data: dict[str, Any]) -> Message:
    return Message(
        src=src,
        dst=OB_BOX,
        msg_id=VIEW_DATA_MSG,
        payload={"view_id": view_id, "data": dict(data)},
    )


def view_scroll_message(
    src: str, view_id: str, anchor: str, offset: int = 64, duration: int = 600
) -> Message:
    return Message(
        src=src,
        dst=OB_BOX,
        msg_id=VIEW_SCROLL_MSG,
        payload={
            "view_id": view_id,
            "anchor": anchor,
            "offset": int(offset),
            "duration": int(duration),
        },
    )


def anchor_changed_message(view_id: str, anchor: str, dst: str) -> Message:
    return Message(
        src=OB_BOX,
        dst=dst,
        msg_id=ANCHOR_CHANGED_MSG,
        payload={"view_id": view_id, "anchor": anchor},
    )
