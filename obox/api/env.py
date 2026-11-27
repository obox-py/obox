"""env 命名空间：应用信息、剪贴板与 shell 打开。

六个应用信息都是属性请求，共用 ENV_INFO_MSG，用 payload.property 区分。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .message import OB_BOX, Message

if TYPE_CHECKING:
    from ..extensions.context import OboxContext

ENV_INFO_MSG = "ENV_INFO_MSG"
ENV_CLIPBOARD_READ_MSG = "ENV_CLIPBOARD_READ_MSG"
ENV_CLIPBOARD_WRITE_MSG = "ENV_CLIPBOARD_WRITE_MSG"
ENV_OPEN_EXTERNAL_MSG = "ENV_OPEN_EXTERNAL_MSG"
ENV_OPEN_PATH_MSG = "ENV_OPEN_PATH_MSG"

APP_INFO_FIELDS = ("appName", "appVersion", "language", "appHost", "platform", "arch")


def _request(ctx: OboxContext, msg_id: str, payload: dict[str, Any] | None = None) -> Message:
    return Message(src=ctx.extension_id, dst=OB_BOX, msg_id=msg_id, payload=dict(payload or {}))


def _info(ctx: OboxContext, field: str) -> Message:
    if field not in APP_INFO_FIELDS:
        raise ValueError(f"未知的应用信息：{field!r}")
    return _request(ctx, ENV_INFO_MSG, {"property": field})


def appName(ctx: OboxContext) -> Message:
    return _info(ctx, "appName")


def appVersion(ctx: OboxContext) -> Message:
    return _info(ctx, "appVersion")


def language(ctx: OboxContext) -> Message:
    return _info(ctx, "language")


def appHost(ctx: OboxContext) -> Message:
    return _info(ctx, "appHost")


def platform(ctx: OboxContext) -> Message:
    return _info(ctx, "platform")


def arch(ctx: OboxContext) -> Message:
    return _info(ctx, "arch")


class Clipboard:
    """剪贴板命名空间：clipboard.readText(ctx) / clipboard.writeText(ctx, text)。"""

    @staticmethod
    def readText(ctx: OboxContext) -> Message:
        return _request(ctx, ENV_CLIPBOARD_READ_MSG)

    @staticmethod
    def writeText(ctx: OboxContext, text: str = "") -> Message:
        return _request(ctx, ENV_CLIPBOARD_WRITE_MSG, {"text": str(text)})


clipboard = Clipboard()


def openExternal(ctx: OboxContext, uri: str) -> Message:
    value = str(uri or "").strip()
    if not value:
        raise ValueError("uri 不能为空")
    return _request(ctx, ENV_OPEN_EXTERNAL_MSG, {"uri": value})


def openPath(ctx: OboxContext, path: str) -> Message:
    value = str(path or "").strip()
    if not value:
        raise ValueError("path 不能为空")
    return _request(ctx, ENV_OPEN_PATH_MSG, {"path": value})


__all__ = [
    "APP_INFO_FIELDS",
    "Clipboard",
    "ENV_CLIPBOARD_READ_MSG",
    "ENV_CLIPBOARD_WRITE_MSG",
    "ENV_INFO_MSG",
    "ENV_OPEN_EXTERNAL_MSG",
    "ENV_OPEN_PATH_MSG",
    "appHost",
    "appName",
    "appVersion",
    "arch",
    "clipboard",
    "language",
    "openExternal",
    "openPath",
    "platform",
]