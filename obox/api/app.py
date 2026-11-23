"""应用开窗消息。"""

from __future__ import annotations

from .message import OB_BOX, Message

APP_LAUNCH_MSG = "APP_LAUNCH_MSG"
APP_OPEN_MSG = "APP_OPEN_MSG"
APP_UI_MSG = "APP_UI_MSG"
APP_LIST_MSG = "APP_LIST_MSG"
APP_VIEW_DATA_MSG = "APP_VIEW_DATA_MSG"


def app_view_data_message(src: str, view_id: str, apps: list[dict]):
    from .message import OB_BOX, Message

    return Message(
        src=src,
        dst=OB_BOX,
        msg_id=APP_VIEW_DATA_MSG,
        payload={"view_id": view_id, "apps": list(apps)},
    )


def app_launch_message(src: str, app_id: str):
    from .message import Message

    return Message(src=src, dst=OB_BOX, msg_id=APP_LAUNCH_MSG, payload={"app_id": app_id})


def app_open_message(app_id: str, window_id: str, dst: str) -> Message:
    return Message(
        src=OB_BOX,
        dst=dst,
        msg_id=APP_OPEN_MSG,
        payload={"app_id": app_id, "window_id": window_id},
    )


def app_ui_message(src: str, window_id: str, oml: str = "", html: str = "") -> Message:
    return Message(
        src=src,
        dst=OB_BOX,
        msg_id=APP_UI_MSG,
        payload={"window_id": window_id, "oml": oml, "html": html},
    )
