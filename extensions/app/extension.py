"""系统扩展：应用网格与搜索。"""

from __future__ import annotations

from obox.api.app import APP_LIST_MSG, app_launch_message, app_view_data_message
from obox.api.events import CLICK, INPUT
from obox.api.message import COMPONENT_EVENT_MSG


def filter_apps(apps: list[dict], query: str) -> list[dict]:
    """按标题、描述、作者做大小写不敏感的子串过滤；空查询返回全部。"""
    text = (query or "").strip().casefold()
    if not text:
        return list(apps)

    def hit(app: dict) -> bool:
        return any(text in str(app.get(field, "")).casefold() for field in ("title", "description", "author"))

    return [app for app in apps if hit(app)]


def activate(context) -> None:
    state = {"apps": [], "query": ""}
    context.register_view("app.main", "views/main.oml", "main", "{{i18n.app.title}}")

    def _push() -> None:
        context.send(
            app_view_data_message(
                context.extension_id, "app.main", filter_apps(state["apps"], state["query"])
            )
        )

    def _on_list(message) -> None:
        state["apps"] = list((message.payload or {}).get("apps") or [])
        _push()

    def _on_event(message) -> None:
        if message.event == INPUT:
            state["query"] = str((message.payload or {}).get("value") or "")
            _push()
        elif message.event == CLICK:
            app_id = str((message.payload or {}).get("value") or "")
            if app_id:
                context.send(app_launch_message(context.extension_id, app_id))

    context.on(APP_LIST_MSG, _on_list)
    context.on(COMPONENT_EVENT_MSG, _on_event)


def deactivate(context) -> None:
    context.subscriptions.clear()
