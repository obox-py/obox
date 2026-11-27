"""注入给扩展的上下文：字段只读，订阅袋可追加。"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..api.i18n import I18nRegisterMessage
from ..api.message import Message
from ..api.request import Request
from ..core.bus import MessageBus
from .contributions import CommandRegistry, ViewDefinition, ViewRegistry
from .manifest import Manifest


@dataclass(frozen=True, slots=True)
class ExtensionInfo:
    """扩展清单的只读快照。"""

    id: str
    name: str
    version: str
    publisher: str
    directory: Path
    storage_path: Path
    status: str = "active"
    origin: str = "source"


class SubscriptionBag:
    """只读暴露的订阅袋：允许 append/clear，不允许整体替换。"""

    __slots__ = ("_items",)

    def __init__(self) -> None:
        self._items: list[Callable[[], None]] = []

    def append(self, item: Callable[[], None]) -> None:
        self._items.append(item)

    def extend(self, items: list[Callable[[], None]]) -> None:
        self._items.extend(items)

    def clear(self) -> None:
        self._items.clear()

    def dispose(self) -> None:
        for item in reversed(self._items):
            try:
                item()
            except Exception:
                pass
        self._items.clear()

    def __iter__(self) -> Iterator[Callable[[], None]]:
        return iter(tuple(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> Callable[[], None]:
        return self._items[index]


class _BoundNamespace:
    """把模块函数绑定到 ctx：ctx.window.showInformationMessage(...)。"""

    def __init__(self, ctx: Any, module: Any) -> None:
        self._ctx = ctx
        self._module = module

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._module, name)
        if callable(value):
            def _bound(*args: Any, **kwargs: Any) -> Any:
                return value(self._ctx, *args, **kwargs)

            return _bound
        if hasattr(value, "readText") or hasattr(value, "writeText"):
            return _BoundObject(self._ctx, value)
        return value


class _BoundObject:
    def __init__(self, ctx: Any, target: Any) -> None:
        self._ctx = ctx
        self._target = target

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._target, name)
        if callable(value):
            return lambda *args, **kwargs: value(self._ctx, *args, **kwargs)
        return value


class OboxContext:
    """扩展可见的全部能力；字段只读，subscriptions 只允许追加/清空。"""

    __slots__ = (
        "extension_id",
        "extension",
        "assets_dir",
        "storage_dir",
        "global_storage_dir",
        "log_dir",
        "window_id",
        "subscriptions",
        "_bus",
        "_commands",
        "_views",
        "_frozen",
        "_namespaces",
    )

    def __init__(
        self,
        manifest: Manifest,
        storage_dir: Path,
        bus: MessageBus,
        commands: CommandRegistry,
        views: ViewRegistry,
        window_id: str | None = None,
    ) -> None:
        storage_dir = Path(storage_dir)
        extension = ExtensionInfo(
            id=manifest.extension_id,
            name=manifest.name,
            version=manifest.version,
            publisher=manifest.publisher,
            directory=manifest.directory,
            storage_path=storage_dir,
        )
        object.__setattr__(self, "extension_id", manifest.extension_id)
        object.__setattr__(self, "extension", extension)
        object.__setattr__(self, "assets_dir", manifest.assets_dir)
        object.__setattr__(self, "storage_dir", storage_dir)
        object.__setattr__(self, "global_storage_dir", storage_dir / "global")
        object.__setattr__(self, "log_dir", storage_dir / "logs")
        object.__setattr__(self, "window_id", window_id)
        object.__setattr__(self, "subscriptions", SubscriptionBag())
        object.__setattr__(self, "_bus", bus)
        object.__setattr__(self, "_commands", commands)
        object.__setattr__(self, "_views", views)
        object.__setattr__(self, "_namespaces", {})
        object.__setattr__(self, "_frozen", True)

    def _namespace(self, name: str) -> Any:
        cached = self._namespaces.get(name)
        if cached is not None:
            return cached
        from importlib import import_module

        module = import_module(f"obox.api.{name}")
        bound = _BoundNamespace(self, module)
        self._namespaces[name] = bound
        return bound

    @property
    def window(self):
        return self._namespace("window")

    @property
    def workspace(self):
        return self._namespace("workspace")

    @property
    def commands(self):
        return self._namespace("commands")

    @property
    def env(self):
        return self._namespace("env")

    @property
    def extensions(self):
        return self._namespace("extensions")

    @property
    def storage(self):
        return self._namespace("storage")

    @property
    def network(self):
        return self._namespace("network")

    @property
    def message(self):
        return self._namespace("message")

    @property
    def log(self):
        return self._namespace("log")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("OboxContext 字段只读，状态请用 Memento/订阅袋")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("OboxContext 字段只读")

    @property
    def extension_uri(self) -> Path:
        return self.extension.directory

    @property
    def global_storage_uri(self) -> Path:
        return self.global_storage_dir

    @property
    def storage_uri(self) -> Path:
        return self.storage_dir

    @property
    def log_uri(self) -> Path:
        return self.log_dir

    def as_absolute_path(self, relative_path: str) -> Path:
        base = self.extension.directory.resolve()
        target = (base / relative_path).resolve()
        if target != base and base not in target.parents:
            raise ValueError(f"路径越界：{relative_path}")
        return target

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
        self.subscriptions.dispose()
        self._commands.unregister_owner(self.extension_id)
        self._views.unregister_owner(self.extension_id)

# 兼容旧引用名
ExtensionContext = OboxContext