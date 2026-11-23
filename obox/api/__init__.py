"""扩展与主程序共享的契约层：消息、组件消息、请求对象与错误。"""

from .component import (
    ComponentEventMessage,
    ComponentModifyMessage,
    ComponentStateMessage,
    decode_message,
)
from .errors import (
    BroadcastReply,
    ComponentConflict,
    ComponentNotFound,
    ForbiddenOwner,
    FrameError,
    ManifestError,
    MessageFormatError,
    OboxError,
    ProtocolError,
    RequestTimeout,
    error_payload,
)
from .message import (
    COMPONENT_EVENT_MSG,
    COMPONENT_MODIFY_MSG,
    COMPONENT_STATE_MSG,
    OB_BOX,
    Message,
    is_identity,
)
from .request import Request

__all__ = [
    "BroadcastReply",
    "COMPONENT_EVENT_MSG",
    "COMPONENT_MODIFY_MSG",
    "COMPONENT_STATE_MSG",
    "ComponentConflict",
    "ComponentEventMessage",
    "ComponentModifyMessage",
    "ComponentNotFound",
    "ComponentStateMessage",
    "ForbiddenOwner",
    "FrameError",
    "ManifestError",
    "Message",
    "MessageFormatError",
    "OB_BOX",
    "OboxError",
    "ProtocolError",
    "Request",
    "RequestTimeout",
    "decode_message",
    "error_payload",
    "is_identity",
]
