"""系统扩展：扩展管理（安装、禁用与卸载）。"""

from __future__ import annotations

from obox.api.events import CLICK, INPUT
from obox.api.extensions import (
    EXTENSIONS_LIST_MSG,
    extensions_manage_message,
)
from obox.api.message import COMPONENT_EVENT_MSG
from obox.api.view import view_data_message

_SOURCE_LABELS = {"user": "用户安装", "system": "内置", "source": "源码"}
_REMOVE_PREFIX = "ext-remove-"
_TOGGLE_PREFIX = "ext-toggle-"


def _origin_label(origin: str) -> str:
    return _SOURCE_LABELS.get(origin, origin or "源码")


def _view_item(item: dict) -> dict:
    enabled = bool(item.get("enabled", True))
    origin = str(item.get("origin") or "source")
    status = "已禁用" if not enabled else ("激活" if item.get("status") == "active" else "失败")
    meta = " · ".join(
        part
        for part in (
            str(item.get("publisher") or ""),
            str(item.get("version") or ""),
            _origin_label(origin),
        )
        if part
    )
    return {
        "id": str(item.get("id") or ""),
        "title": str(item.get("name") or item.get("id") or ""),
        "meta": meta,
        "status": status,
        "removable": origin == "user",
        "toggle": "启用" if not enabled else "禁用",
    }


def filter_extensions(items: list[dict], query: str) -> list[dict]:
    """按名称、作者、描述做大小写不敏感的子串过滤；空查询返回全部。"""
    text = (query or "").strip().casefold()
    if not text:
        return [_view_item(item) for item in items]

    def hit(item: dict) -> bool:
        return any(
            text in str(item.get(field, "")).casefold()
            for field in ("name", "publisher", "description", "id")
        )

    return [_view_item(item) for item in items if hit(item)]


def _confirm_remove(context, extension_id: str) -> None:
    """用新的 window.showMessageBox 做卸载确认。"""
    request = context.request(
        context.window.showMessageBox(
            context,
            {
                "type": "warning",
                "message": f"卸载扩展 {extension_id}？",
                "detail": "卸载后扩展目录会从数据目录移除。",
                "buttons": ["卸载", "取消"],
                "defaultId": 1,
                "cancelId": 1,
            },
        ),
        timeout=120,
    )

    def _done(req) -> None:
        try:
            result = req.result(0)
        except Exception:
            return
        if int(result.get("response", 1)) == 0:
            context.send(extensions_manage_message(context.extension_id, "remove", extension_id))

    request.add_done_callback(_done)


def activate(context) -> None:
    state = {"items": [], "query": ""}

    context.register_view("extensions.main", "views/main.oml", "sidebar", "扩展")

    def _push() -> None:
        context.send(
            view_data_message(
                context.extension_id,
                "extensions.main",
                {"items": filter_extensions(state["items"], state["query"])},
            )
        )

    def _on_list(message) -> None:
        state["items"] = list((message.payload or {}).get("items") or [])
        _push()

    def _on_event(message) -> None:
        component_id = str(getattr(message, "id", "") or "")
        payload = message.payload or {}
        if message.event == INPUT and component_id == "ext-search":
            state["query"] = str(payload.get("value") or "")
            _push()
            return
        if message.event != CLICK:
            return
        if component_id == "ext-install":
            context.send(extensions_manage_message(context.extension_id, "install"))
            return
        if component_id.startswith(_REMOVE_PREFIX):
            extension_id = component_id[len(_REMOVE_PREFIX):]
            _confirm_remove(context, extension_id)
            return
        if component_id.startswith(_TOGGLE_PREFIX):
            extension_id = component_id[len(_TOGGLE_PREFIX):]
            current = next((item for item in state["items"] if item.get("id") == extension_id), None)
            if current is None:
                return
            enabled = not bool(current.get("enabled", True))
            context.send(
                extensions_manage_message(context.extension_id, "toggle", extension_id, enabled)
            )

    context.on(EXTENSIONS_LIST_MSG, _on_list)
    context.on(COMPONENT_EVENT_MSG, _on_event)


def deactivate(context) -> None:
    context.subscriptions.clear()