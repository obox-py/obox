"""命令与视图注册表。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..api.errors import OboxError


class ContributionError(OboxError):
    code = "E_CONTRIBUTION"


@dataclass(frozen=True)
class ViewDefinition:
    view_id: str
    extension_id: str
    container: str
    html_source: str
    title: str = ""


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, tuple[str, Callable[..., Any]]] = {}

    def register(self, extension_id: str, command_id: str, handler: Callable[..., Any]) -> None:
        if command_id in self._commands:
            raise ContributionError(f"命令已注册：{command_id}")
        self._commands[command_id] = (extension_id, handler)

    def invoke(self, command_id: str, *args: Any) -> Any:
        entry = self._commands.get(command_id)
        if entry is None:
            raise ContributionError(f"命令不存在：{command_id}")
        return entry[1](*args)

    def ids(self) -> list[str]:
        return sorted(self._commands)

    def unregister_owner(self, extension_id: str) -> None:
        for command_id in [key for key, value in self._commands.items() if value[0] == extension_id]:
            self._commands.pop(command_id, None)


class ViewRegistry:
    def __init__(self) -> None:
        self._views: dict[str, ViewDefinition] = {}

    def register(self, view: ViewDefinition) -> None:
        if view.view_id in self._views:
            raise ContributionError(f"视图已注册：{view.view_id}")
        self._views[view.view_id] = view

    def get(self, view_id: str) -> ViewDefinition:
        view = self._views.get(view_id)
        if view is None:
            raise ContributionError(f"视图不存在：{view_id}")
        return view

    def ids(self) -> list[str]:
        return sorted(self._views)

    def all(self) -> list[ViewDefinition]:
        return [self._views[key] for key in sorted(self._views)]

    def unregister_owner(self, extension_id: str) -> None:
        for view_id in [key for key, value in self._views.items() if value.extension_id == extension_id]:
            self._views.pop(view_id, None)
