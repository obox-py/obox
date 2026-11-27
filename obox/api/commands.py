"""commands 命名空间：命令注册、执行与列举的消息构造。

函数第一个参数是扩展上下文 ctx，返回发往扩展宿主（HOST_ID）的 Message。命令表
由宿主持有，所以注册、执行、列举都在宿主侧处理；registerCommand 的 callback 由
扩展运行时在本进程注册（payload 必须能 JSON 序列化，不携带回调）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .extensions import HOST_ID
from .message import Message

if TYPE_CHECKING:
    from ..extensions.context import OboxContext

COMMANDS_REGISTER_MSG = "COMMANDS_REGISTER_MSG"
COMMANDS_EXECUTE_MSG = "COMMANDS_EXECUTE_MSG"
COMMANDS_GET_MSG = "COMMANDS_GET_MSG"


def _request(ctx: OboxContext, msg_id: str, payload: dict[str, Any] | None = None) -> Message:
    return Message(src=ctx.extension_id, dst=HOST_ID, msg_id=msg_id, payload=dict(payload or {}))


def _command_id(commandId: Any) -> str:
    value = str(commandId or "").strip()
    if not value:
        raise ValueError("commandId 不能为空")
    return value


def registerCommand(
    ctx: OboxContext,
    commandId: str,
    callback: Callable[..., Any],
    thisArg: Any = None,
) -> Message:
    """注册命令；callback 留在扩展进程内，消息只同步命令 id 与 thisArg。"""
    if not callable(callback):
        raise TypeError("callback 必须是可调用对象")
    register = getattr(ctx, "register_command", None)
    if callable(register):
        register(commandId, callback)
    return _request(
        ctx,
        COMMANDS_REGISTER_MSG,
        {"command": _command_id(commandId), "thisArg": thisArg},
    )


def executeCommand(ctx: OboxContext, commandId: str, *args: Any) -> Message:
    return _request(
        ctx,
        COMMANDS_EXECUTE_MSG,
        {"command": _command_id(commandId), "args": list(args)},
    )


def getCommands(ctx: OboxContext, filterInternal: bool = False) -> Message:
    return _request(ctx, COMMANDS_GET_MSG, {"filterInternal": bool(filterInternal)})


__all__ = [
    "COMMANDS_EXECUTE_MSG",
    "COMMANDS_GET_MSG",
    "COMMANDS_REGISTER_MSG",
    "executeCommand",
    "getCommands",
    "registerCommand",
]