"""消息基类与消息标识常量，以及以 ctx 为入口的收发函数。"""

from __future__ import annotations

from collections.abc import Callable
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


class Disposable:
    """一次性的清理句柄；可放进 ctx.subscriptions（SubscriptionBag 调用它）。

    dispose 幂等；`__call__` 让只接受无参回调的订阅袋也能直接回收。
    """

    __slots__ = ("_dispose", "_disposed")

    def __init__(self, dispose: Callable[[], None] | None = None) -> None:
        self._dispose = dispose
        self._disposed = False

    @property
    def disposed(self) -> bool:
        return self._disposed

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        if self._dispose is not None:
            self._dispose()

    def __call__(self) -> None:
        self.dispose()


def send(ctx: Any, target: str, messageId: str, payload: Any = None) -> None:
    """向 target（obox 或扩展标识）单向发送消息。"""
    ctx.send(
        Message(
            src=ctx.extension_id,
            dst=target,
            msg_id=messageId,
            payload=dict(payload or {}),
        )
    )


def request(
    ctx: Any,
    target: str,
    messageId: str,
    payload: Any = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """发送请求并等待应答 payload；超时或应答带 error 时抛异常。"""
    return ctx.request(
        Message(
            src=ctx.extension_id,
            dst=target,
            msg_id=messageId,
            payload=dict(payload or {}),
        ),
        timeout,
    ).result()


def broadcast(ctx: Any, messageId: str, payload: Any = None) -> None:
    """向所有扩展广播；dst 为空。"""
    ctx.send(
        Message(
            src=ctx.extension_id,
            dst="",
            msg_id=messageId,
            payload=dict(payload or {}),
        )
    )


def on(
    ctx: Any,
    messageId: str,
    listener: Callable[[Any, str], None],
) -> Disposable:
    """订阅消息；listener 收到 (payload, src)，返回的 Disposable 只停投递。"""
    active = True

    def _handle(message: Message) -> None:
        if active:
            listener(message.payload, message.src)

    unsubscribe = ctx.on(messageId, _handle)
    unregister = unsubscribe if callable(unsubscribe) else None

    def _stop() -> None:
        nonlocal active
        active = False
        if unregister is not None:
            unregister()

    return Disposable(_stop)
