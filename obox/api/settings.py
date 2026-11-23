"""设置列表下发与设置写入消息。"""

from __future__ import annotations

from typing import Any

from .message import OB_BOX, Message

SETTINGS_LIST_MSG = "SETTINGS_LIST_MSG"
SETTINGS_SET_MSG = "SETTINGS_SET_MSG"
EXTENSION_CONFIG_MSG = "EXTENSION_CONFIG_MSG"


def settings_list_message(groups: list[dict[str, Any]]) -> Message:
    return Message(src=OB_BOX, dst="settings.obox", msg_id=SETTINGS_LIST_MSG, payload={"groups": groups})


def settings_set_message(src: str, key: str, value: Any) -> Message:
    return Message(src=src, dst=OB_BOX, msg_id=SETTINGS_SET_MSG, payload={"key": key, "value": value})

def extension_config_message(src: str, extension_id: str, values: dict, defaults: dict):
    return Message(
        src=src,
        dst=extension_id,
        msg_id=EXTENSION_CONFIG_MSG,
        payload={"values": dict(values), "defaults": dict(defaults)},
    )
