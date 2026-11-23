"""i18n 注册消息。"""

from __future__ import annotations

from typing import Any

from .message import OB_BOX, Message

I18N_REGISTER_MSG = "I18N_REGISTER_MSG"


class I18nRegisterMessage(Message):
    """扩展向 obox 注册一条多语言文案。"""

    def __init__(
        self,
        src: str,
        entry_id: str,
        values: dict[str, str],
        name: str = "",
        reply: bool = False,
        correlation_id: str = "",
        dst: str = OB_BOX,
    ) -> None:
        payload: dict[str, Any] = {
            "name": name or src,
            "id": entry_id,
            "values": dict(values),
        }
        super().__init__(
            src=src,
            dst=dst,
            msg_id=I18N_REGISTER_MSG,
            payload=payload,
            reply=reply,
            correlation_id=correlation_id,
        )
