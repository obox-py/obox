"""注入给扩展的上下文。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..api.i18n import I18nRegisterMessage
from ..api.message import Message
from ..api.request import Request
from ..core.bus import MessageBus
from .contributions import CommandRegistry, ViewDefinition, ViewRegistry
from .manifest import Manifest


class ExtensionContext:
    """扩展可见的全部能力；注销时统一释放。"""

    def __init__(
        self,
        manifest: Manifest,
        storage_dir: Path,
        bus: MessageBus,
        commands: CommandRegistry,
        views: ViewRegistry,
    ) -> None:
        self.extension_id = manifest.extension_id
        self.assets_dir = manifest.assets_dir
        self.storage_dir = storage_dir
        self._bus = bus
        self._commands = commands
        self._views = views
        self.subscriptions: list[Callable[[], None]] = []

    def register_command(self, command_id: str, handler: Callable[..., Any]) -> None:
        self._commands.register(self.extension_id, command_id, handler)

    def register_view(self, view_id: str, source: str, container: str = "sidebar", title: str = "") -> None:
        """source 可以是相对扩展目录的 .oml 路径，也可以是一段内联片段。"""
        self._views.register(
            ViewDefinition(
                view_id=view_id,
                extension_id=self.extension_id,
                container=container,
                html_source=source,
                title=title or view_id,
            )
        )

    def register_i18n(self, entry_id: str, values: dict[str, str], name: str = "") -> None:
        """注册一条多语言文案；扩展只能以自己的标识注册。"""
        target = name or self.extension_id
        if target != self.extension_id:
            raise ValueError("扩展只能注册自己的 i18n")
        self._bus.send(
            I18nRegisterMessage(src=self.extension_id, entry_id=entry_id, values=values)
        )

    def read_asset(self, relative_path: str) -> str:
        target = (self.assets_dir / relative_path).resolve()
        if self.assets_dir.resolve() not in target.parents:
            raise ValueError(f"资产路径越出 assets：{relative_path}")
        return target.read_text(encoding="utf-8")

    def on(self, msg_id: str, handler: Callable[[Message], Any]) -> None:
        def _filtered(message: Message) -> None:
            if message.is_broadcast or message.dst == self.extension_id:
                handler(message)

        self.subscriptions.append(self._bus.on(msg_id, _filtered))

    def send(self, message: Message) -> None:
        self._bus.send(message)

    def request(self, message: Message, timeout: float = 5.0) -> Request:
        return self._bus.request(message, timeout)

    def dispose(self) -> None:
        for unsubscribe in self.subscriptions:
            unsubscribe()
        self.subscriptions.clear()
        self._commands.unregister_owner(self.extension_id)
        self._views.unregister_owner(self.extension_id)
