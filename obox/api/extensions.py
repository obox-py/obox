"""扩展安装、卸载与启用停用的控制消息。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .message import OB_BOX, Message

if TYPE_CHECKING:
    from ..extensions.context import OboxContext

HOST_ID = "host.obox"

EXT_INSTALL_MSG = "EXT_INSTALL_MSG"
EXT_REMOVE_MSG = "EXT_REMOVE_MSG"
EXT_ENABLE_MSG = "EXT_ENABLE_MSG"
EXTENSIONS_CHANGED_MSG = "EXTENSIONS_CHANGED_MSG"
EXTENSIONS_LIST_MSG = "EXTENSIONS_LIST_MSG"
EXTENSIONS_MANAGE_MSG = "EXTENSIONS_MANAGE_MSG"
EXTENSIONS_RESULT_MSG = "EXTENSIONS_RESULT_MSG"
DEV_EXTENSION_ADD_MSG = "DEV_EXTENSION_ADD_MSG"
DEV_EXTENSION_REMOVE_MSG = "DEV_EXTENSION_REMOVE_MSG"

EXTENSIONS_ALL_MSG = "EXTENSIONS_ALL_MSG"
EXTENSIONS_GET_MSG = "EXTENSIONS_GET_MSG"
EXTENSIONS_ON_CHANGE_MSG = "EXTENSIONS_ON_CHANGE_MSG"


def install_extension_message(package: str) -> Message:
    return Message(src=OB_BOX, dst=HOST_ID, msg_id=EXT_INSTALL_MSG, payload={"package": package})


def remove_extension_message(extension_id: str) -> Message:
    return Message(src=OB_BOX, dst=HOST_ID, msg_id=EXT_REMOVE_MSG, payload={"id": extension_id})


def enable_extension_message(extension_id: str, enabled: bool) -> Message:
    return Message(
        src=OB_BOX,
        dst=HOST_ID,
        msg_id=EXT_ENABLE_MSG,
        payload={"id": extension_id, "enabled": bool(enabled)},
    )


def extensions_changed_message(
    removed: list[str],
    changed: list[str],
    views: list[dict[str, Any]],
    commands: list[str],
    extensions: list[dict[str, Any]],
    i18n: dict[str, dict[str, dict[str, str]]] | None = None,
) -> Message:
    return Message(
        src=HOST_ID,
        dst=OB_BOX,
        msg_id=EXTENSIONS_CHANGED_MSG,
        payload={
            "removed": list(removed),
            "changed": list(changed),
            "views": list(views),
            "commands": list(commands),
            "extensions": list(extensions),
            "i18n": dict(i18n or {}),
        },
    )


def extensions_result_message(action: str, extension_id: str, ok: bool, error: str = "") -> Message:
    return Message(
        src=HOST_ID,
        dst=OB_BOX,
        msg_id=EXTENSIONS_RESULT_MSG,
        payload={"action": action, "id": extension_id, "ok": bool(ok), "error": error},
    )


def extensions_list_message(items: list[dict[str, Any]]) -> Message:
    return Message(
        src=OB_BOX,
        dst="extensions.obox",
        msg_id=EXTENSIONS_LIST_MSG,
        payload={"items": list(items)},
    )


def extensions_manage_message(src: str, action: str, extension_id: str = "", enabled: bool = False) -> Message:
    return Message(
        src=src,
        dst=OB_BOX,
        msg_id=EXTENSIONS_MANAGE_MSG,
        payload={"action": action, "id": extension_id, "enabled": bool(enabled)},
    )

def dev_extension_add_message(path: str) -> Message:
    return Message(src=OB_BOX, dst=OB_BOX, msg_id=DEV_EXTENSION_ADD_MSG, payload={"path": str(path)})


def dev_extension_remove_message(path: str) -> Message:
    return Message(src=OB_BOX, dst=OB_BOX, msg_id=DEV_EXTENSION_REMOVE_MSG, payload={"path": str(path)})

def _api_message(
    ctx: OboxContext, msg_id: str, payload: dict[str, Any] | None = None
) -> Message:
    return Message(src=ctx.extension_id, dst=HOST_ID, msg_id=msg_id, payload=dict(payload or {}))


def all(ctx: OboxContext) -> Message:
    """属性请求：列出全部扩展（id/name/version/directory/storagePath/status/origin）。"""
    return _api_message(ctx, EXTENSIONS_ALL_MSG)


def getExtension(ctx: OboxContext, id: str) -> Message:
    extension_id = str(id or "").strip()
    if not extension_id:
        raise ValueError("扩展 id 不能为空")
    return _api_message(ctx, EXTENSIONS_GET_MSG, {"id": extension_id})


def onDidChange(
    ctx: OboxContext, listener: Callable[[dict[str, Any]], None] | None = None
) -> Message:
    """订阅扩展增删与状态变化；listener 由扩展运行时在本进程注册。"""
    if listener is not None and not callable(listener):
        raise TypeError("listener 必须是可调用对象")
    return _api_message(ctx, EXTENSIONS_ON_CHANGE_MSG, {"subscribe": True})


__all__ = [
    "DEV_EXTENSION_ADD_MSG",
    "DEV_EXTENSION_REMOVE_MSG",
    "EXTENSIONS_ALL_MSG",
    "EXTENSIONS_CHANGED_MSG",
    "EXTENSIONS_GET_MSG",
    "EXTENSIONS_LIST_MSG",
    "EXTENSIONS_MANAGE_MSG",
    "EXTENSIONS_ON_CHANGE_MSG",
    "EXTENSIONS_RESULT_MSG",
    "EXT_ENABLE_MSG",
    "EXT_INSTALL_MSG",
    "EXT_REMOVE_MSG",
    "HOST_ID",
    "all",
    "dev_extension_add_message",
    "dev_extension_remove_message",
    "enable_extension_message",
    "extensions_changed_message",
    "extensions_list_message",
    "extensions_manage_message",
    "extensions_result_message",
    "getExtension",
    "install_extension_message",
    "onDidChange",
    "remove_extension_message",
]