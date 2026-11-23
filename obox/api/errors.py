"""错误码与异常；错误码会进入消息应答的 payload。"""

from __future__ import annotations


class OboxError(Exception):
    """所有 obox 错误的基类。"""

    code = "E_UNKNOWN"


class MessageFormatError(OboxError, ValueError):
    code = "E_MESSAGE_FORMAT"


class FrameError(OboxError):
    code = "E_FRAME_INVALID"


class ProtocolError(OboxError):
    code = "E_PROTOCOL"


class ComponentError(OboxError):
    code = "E_COMPONENT"


class ComponentNotFound(ComponentError):
    code = "E_COMPONENT_NOT_FOUND"


class ComponentConflict(ComponentError):
    code = "E_COMPONENT_CONFLICT"


class ForbiddenOwner(ComponentError):
    code = "E_FORBIDDEN_OWNER"


class RequestTimeout(OboxError, TimeoutError):
    code = "E_TIMEOUT"


class BroadcastReply(OboxError):
    code = "E_BROADCAST_REPLY"


class ManifestError(OboxError):
    code = "E_MANIFEST_INVALID"


def error_payload(exc: BaseException) -> dict[str, str]:
    """把异常转成应答 payload。"""
    return {"error": getattr(exc, "code", "E_UNKNOWN"), "message": str(exc)}
