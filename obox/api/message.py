"""消息基类与消息标识常量。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

OB_BOX = "obox"

COMPONENT_EVENT_MSG = "COMPONENT_EVENT_MSG"
COMPONENT_STATE_MSG = "COMPONENT_STATE_MSG"
COMPONENT_MODIFY_MSG = "COMPONENT_MODIFY_MSG"

_REQUIRED_FIELDS = ("src", "dst", "msg_id")


def is_identity(value: str) -> bool:
    """判断扩展标识是否合法：obox 或 名称.作者。"""
    if value == OB_BOX:
        return True
    if not value or "." not in value:
        return False
    name, _, author = value.partition(".")
    return bool(name) and bool(author) and "." not in author


@dataclass
class Message:
    """一条跨进程消息；dst 为空表示广播。"""

    src: str
    dst: str
    msg_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    reply: bool = False
    correlation_id: str = ""

    def __post_init__(self) -> None:
        if not is_identity(self.src):
            raise ValueError(f"非法的 src：{self.src!r}")
        if self.dst and not is_identity(self.dst):
            raise ValueError(f"非法的 dst：{self.dst!r}")
        if not self.msg_id:
            raise ValueError("msg_id 不能为空")
        if self.reply and not self.correlation_id:
            raise ValueError("返程消息必须携带 correlation_id")
        if self.reply and not self.dst:
            raise ValueError("广播消息不接受返程")

    @property
    def is_broadcast(self) -> bool:
        return self.dst == ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "src": self.src,
            "dst": self.dst,
            "msg_id": self.msg_id,
            "payload": self.payload,
            "reply": self.reply,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        if not isinstance(data, dict):
            raise ValueError("消息必须是 JSON 对象")
        missing = [key for key in _REQUIRED_FIELDS if key not in data]
        if missing:
            raise ValueError(f"消息缺少字段：{', '.join(missing)}")
        payload = data.get("payload") or {}
        if not isinstance(payload, dict):
            raise ValueError("payload 必须是对象")
        return cls(
            src=str(data["src"]),
            dst=str(data["dst"]),
            msg_id=str(data["msg_id"]),
            payload=payload,
            reply=bool(data.get("reply", False)),
            correlation_id=str(data.get("correlation_id", "")),
        )
