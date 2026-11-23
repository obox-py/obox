"""视图生命周期消息。"""

from __future__ import annotations

from .message import OB_BOX, Message

VIEW_MOUNTED_MSG = "VIEW_MOUNTED_MSG"
VIEW_UPDATED_MSG = "VIEW_UPDATED_MSG"
VIEW_UNMOUNTED_MSG = "VIEW_UNMOUNTED_MSG"


def view_message(kind: str, owner: str, view_id: str) -> Message:
    return Message(
        src=OB_BOX,
        dst=owner,
        msg_id=kind,
        payload={"view_id": view_id},
    )
