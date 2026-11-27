"""storage 命名空间：globalState 与 workspaceState 的键值状态。"""

from __future__ import annotations

from typing import Any

from .extensions import HOST_ID
from .message import Message, request

STORAGE_GET_MSG = "STORAGE_GET_MSG"
STORAGE_UPDATE_MSG = "STORAGE_UPDATE_MSG"
STORAGE_KEYS_MSG = "STORAGE_KEYS_MSG"

GLOBAL_SCOPE = "global"
WORKSPACE_SCOPE = "workspace"
_SCOPES = (GLOBAL_SCOPE, WORKSPACE_SCOPE)

REQUEST_TIMEOUT = 30.0


def storage_get_message(
    src: str, scope: str, key: str, defaultValue: Any = None
) -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=STORAGE_GET_MSG,
        payload={"scope": scope, "key": key, "default": defaultValue},
    )


def storage_update_message(src: str, scope: str, key: str, value: Any) -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=STORAGE_UPDATE_MSG,
        payload={"scope": scope, "key": key, "value": value},
    )


def storage_keys_message(src: str, scope: str) -> Message:
    return Message(
        src=src, dst=HOST_ID, msg_id=STORAGE_KEYS_MSG, payload={"scope": scope}
    )


class Memento:
    """一个作用域的状态视图；get 未命中返回 defaultValue。"""

    def __init__(self, scope: str) -> None:
        if scope not in _SCOPES:
            raise ValueError(f"未知状态作用域：{scope}")
        self.scope = scope

    def get(self, ctx: Any, key: str, defaultValue: Any = None) -> Any:
        payload = request(
            ctx,
            HOST_ID,
            STORAGE_GET_MSG,
            {"scope": self.scope, "key": key, "default": defaultValue},
            REQUEST_TIMEOUT,
        )
        return payload.get("value", defaultValue)

    def update(self, ctx: Any, key: str, value: Any) -> None:
        request(
            ctx,
            HOST_ID,
            STORAGE_UPDATE_MSG,
            {"scope": self.scope, "key": key, "value": value},
            REQUEST_TIMEOUT,
        )

    def keys(self, ctx: Any) -> list[str]:
        payload = request(
            ctx,
            HOST_ID,
            STORAGE_KEYS_MSG,
            {"scope": self.scope},
            REQUEST_TIMEOUT,
        )
        keys = payload.get("keys") or []
        return [str(key) for key in keys]


globalState = Memento(GLOBAL_SCOPE)
workspaceState = Memento(WORKSPACE_SCOPE)
