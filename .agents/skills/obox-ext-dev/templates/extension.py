"""__TITLE__：示例扩展入口。"""

from __future__ import annotations

from obox.api.component import ComponentModifyMessage
from obox.api.events import CLICK
from obox.api.message import COMPONENT_EVENT_MSG, OB_BOX


def activate(context) -> None:
    context.register_view("__NAME__.main", "views/main.oml", "sidebar", "__TITLE__")
    context.register_command("__NAME__.hello", lambda: _set(context, "hello-title", "来自命令"))

    def _on_event(message) -> None:
        if message.event != CLICK:
            return
        if message.id == "hello-btn":
            _set(context, "hello-title", "按钮被点击了")

    context.on(COMPONENT_EVENT_MSG, _on_event)


def _set(context, component_id: str, value: str) -> None:
    context.request(
        ComponentModifyMessage(
            src=context.extension_id,
            dst=OB_BOX,
            component_id=component_id,
            state_type="text",
            value=value,
        ),
        timeout=2.0,
    )


def deactivate(context) -> None:
    context.subscriptions.clear()
