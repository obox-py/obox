"""系统扩展：设置页（外观、语言、扩展配置、关于）。"""

from __future__ import annotations

from obox.api.events import CHANGE, CHECKED_CHANGE, CLICK, INPUT
from obox.api.message import COMPONENT_EVENT_MSG
from obox.api.settings import SETTINGS_LIST_MSG, settings_set_message
from obox.api.view import view_data_message


def filter_groups(groups: list[dict], query: str) -> list[dict]:
    """按分类标题与条目标题/描述做大小写不敏感的子串过滤。"""
    text = (query or "").strip().casefold()
    if not text:
        return list(groups)
    result = []
    for group in groups:
        if text in str(group.get("title", "")).casefold():
            result.append(group)
            continue
        items = [
            item
            for item in group.get("items", [])
            if text in str(item.get("title", "")).casefold()
            or text in str(item.get("description", "")).casefold()
        ]
        if items:
            result.append({**group, "items": items})
    return result


def _key_of(component_id: str) -> str:
    for prefix in ("item-bool-", "item-enum-", "item-string-"):
        if component_id.startswith(prefix):
            return component_id[len(prefix):]
    return ""


def activate(context) -> None:
    state = {"groups": [], "current": "", "query": ""}
    context.register_view("settings.main", "views/main.oml", "sidebar", "设置")

    def _push() -> None:
        groups = filter_groups(state["groups"], state["query"])
        ids = {group["id"] for group in groups}
        current = state["current"] if state["current"] in ids else (groups[0]["id"] if groups else "")
        groups = [
            {**group, "selected": "true" if group["id"] == current else "false"}
            for group in groups
        ]
        items = next((group["items"] for group in groups if group["id"] == current), [])
        current_title = next((group["title"] for group in groups if group["id"] == current), "")
        context.send(
            view_data_message(
                context.extension_id,
                "settings.main",
                {"groups": groups, "items": items, "currentTitle": current_title},
            )
        )

    def _on_list(message) -> None:
        state["groups"] = list((message.payload or {}).get("groups") or [])
        state["current"] = state["current"] or (state["groups"][0]["id"] if state["groups"] else "")
        _push()

    def _on_event(message) -> None:
        component_id = str(getattr(message, "id", "") or "")
        payload = message.payload or {}
        if component_id == "settings-search":
            state["query"] = str(payload.get("value") or "")
            _push()
            return
        if message.event == CLICK and component_id.startswith("group-"):
            state["current"] = str(payload.get("value") or component_id[len("group-"):])
            _push()
            return
        if message.event in (INPUT, CHANGE, CHECKED_CHANGE):
            key = _key_of(component_id)
            if key:
                value = payload.get("checked", payload.get("value"))
                context.send(settings_set_message(context.extension_id, key, value))

    context.on(SETTINGS_LIST_MSG, _on_list)
    context.on(COMPONENT_EVENT_MSG, _on_event)


def deactivate(context) -> None:
    context.subscriptions.clear()
