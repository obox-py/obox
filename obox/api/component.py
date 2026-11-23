"""组件消息三件套：三者都不可继承，方向由语义决定。

事件由 obox 发往创建组件的扩展；状态查询与状态修改由扩展发往 obox；
应答复用同一种消息类型，把 reply 置为真并沿用请求的 correlation_id。
"""

from __future__ import annotations

from typing import Any

from .errors import ForbiddenOwner, MessageFormatError
from .events import ALL_EVENTS
from .message import (
    COMPONENT_EVENT_MSG,
    COMPONENT_MODIFY_MSG,
    COMPONENT_STATE_MSG,
    OB_BOX,
    Message,
)
from .states import ALL_STATES


def _require_component_id(component_id: str) -> str:
    if not isinstance(component_id, str) or not component_id.strip():
        raise MessageFormatError("组件 id 不能为空")
    return component_id


def _require_event(event: str) -> str:
    if event not in ALL_EVENTS:
        raise MessageFormatError(f"未知事件：{event!r}")
    return event


def _require_state(state_type: str) -> str:
    if state_type not in ALL_STATES:
        raise MessageFormatError(f"未知状态类型：{state_type!r}")
    return state_type


class ComponentEventMessage(Message):
    """组件交互事件。"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError("ComponentEventMessage 不可继承")

    def __init__(
        self,
        *,
        src: str,
        dst: str,
        component_id: str,
        event: str,
        payload: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> None:
        if src != OB_BOX:
            raise ForbiddenOwner("组件事件只能由 obox 发出")
        if not dst or dst == OB_BOX:
            raise ForbiddenOwner("组件事件必须有接收方扩展")
        data = dict(payload or {})
        data.update({"id": _require_component_id(component_id), "event": _require_event(event)})
        super().__init__(
            src=src,
            dst=dst,
            msg_id=COMPONENT_EVENT_MSG,
            payload=data,
            correlation_id=correlation_id,
        )

    @property
    def id(self) -> str:
        return str(self.payload["id"])

    @property
    def event(self) -> str:
        return str(self.payload["event"])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentEventMessage":
        base = _as_base(data, COMPONENT_EVENT_MSG)
        return cls(
            src=base.src,
            dst=base.dst,
            component_id=str(base.payload.get("id", "")),
            event=str(base.payload.get("event", "")),
            payload=base.payload,
            correlation_id=base.correlation_id,
        )


class ComponentStateMessage(Message):
    """组件状态查询；返程时携带状态值。"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError("ComponentStateMessage 不可继承")

    def __init__(
        self,
        *,
        src: str,
        dst: str,
        component_id: str,
        state_type: str,
        value: Any = None,
        reply: bool = False,
        correlation_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        _check_direction(src, dst, reply, "状态查询")
        data = dict(payload or {})
        data.update({"id": _require_component_id(component_id), "state_type": _require_state(state_type)})
        if value is not None:
            data["value"] = value
        super().__init__(
            src=src,
            dst=dst,
            msg_id=COMPONENT_STATE_MSG,
            payload=data,
            reply=reply,
            correlation_id=correlation_id,
        )

    @property
    def id(self) -> str:
        return str(self.payload["id"])

    @property
    def state_type(self) -> str:
        return str(self.payload["state_type"])

    @property
    def value(self) -> Any:
        return self.payload.get("value")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentStateMessage":
        base = _as_base(data, COMPONENT_STATE_MSG)
        return cls(
            src=base.src,
            dst=base.dst,
            component_id=str(base.payload.get("id", "")),
            state_type=str(base.payload.get("state_type", "")),
            value=base.payload.get("value"),
            reply=base.reply,
            correlation_id=base.correlation_id,
            payload=base.payload,
        )


class ComponentModifyMessage(Message):
    """组件状态修改。"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError("ComponentModifyMessage 不可继承")

    def __init__(
        self,
        *,
        src: str,
        dst: str,
        component_id: str,
        state_type: str,
        value: Any = None,
        reply: bool = False,
        correlation_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        _check_direction(src, dst, reply, "状态修改")
        data = dict(payload or {})
        data.update({"id": _require_component_id(component_id), "state_type": _require_state(state_type)})
        data["value"] = value
        super().__init__(
            src=src,
            dst=dst,
            msg_id=COMPONENT_MODIFY_MSG,
            payload=data,
            reply=reply,
            correlation_id=correlation_id,
        )

    @property
    def id(self) -> str:
        return str(self.payload["id"])

    @property
    def state_type(self) -> str:
        return str(self.payload["state_type"])

    @property
    def value(self) -> Any:
        return self.payload.get("value")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentModifyMessage":
        base = _as_base(data, COMPONENT_MODIFY_MSG)
        return cls(
            src=base.src,
            dst=base.dst,
            component_id=str(base.payload.get("id", "")),
            state_type=str(base.payload.get("state_type", "")),
            value=base.payload.get("value"),
            reply=base.reply,
            correlation_id=base.correlation_id,
            payload=base.payload,
        )


_COMPONENT_TYPES = {
    COMPONENT_EVENT_MSG: ComponentEventMessage,
    COMPONENT_STATE_MSG: ComponentStateMessage,
    COMPONENT_MODIFY_MSG: ComponentModifyMessage,
}


def _as_base(data: dict[str, Any], expected: str) -> Message:
    base = Message.from_dict(data)
    if base.msg_id != expected:
        raise MessageFormatError(f"msg_id 应为 {expected}，实际是 {base.msg_id}")
    return base


def _check_direction(src: str, dst: str, reply: bool, label: str) -> None:
    if reply:
        if src != OB_BOX:
            raise ForbiddenOwner(f"{label}的应答只能由 obox 发出")
        if not dst or dst == OB_BOX:
            raise ForbiddenOwner(f"{label}的应答必须有接收方扩展")
        return
    if dst != OB_BOX:
        raise ForbiddenOwner(f"{label}必须以 obox 为目的地")


def decode_message(data: dict[str, Any]) -> Message:
    """按 msg_id 还原成对应的消息类型。"""
    msg_id = data.get("msg_id") if isinstance(data, dict) else None
    message_type = _COMPONENT_TYPES.get(msg_id)
    if message_type is None:
        return Message.from_dict(data)
    return message_type.from_dict(data)
