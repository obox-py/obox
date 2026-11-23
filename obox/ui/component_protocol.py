"""组件协议：kit 与 obox 之间唯一的契约。

kit 的组件类声明能力表，obox 按表调用类型化方法，不 import 任何具体组件实现。
"""

from __future__ import annotations

from typing import Any, Protocol

from ..api.errors import OboxError

REQUIRED_TAGS = (
    "div",
    "text",
    "button",
    "input",
    "textarea",
    "checkbox",
    "radio",
    "switch",
    "select",
    "slider",
    "tag",
    "table",
    "tabs",
    "modal",
    "notification",
    "flex",
    "card",
    "choice",
    "alert",
    "image",
    "navitem",
)


class KitContractError(OboxError):
    code = "E_KIT_CONTRACT"


class ComponentLike(Protocol):
    """一个组件实例必须提供的全部能力。"""

    supported_states: tuple[str, ...]
    state_accessors: dict[str, tuple[str, str]]
    supported_events: tuple[str, ...]
    event_methods: dict[str, str]
    widget: Any

    def attach(self, host: Any) -> None: ...
    def container_layout(self) -> Any: ...


def validate_component_class(tag: str, component_type: type) -> None:
    """校验组件类声明的映射与具名方法是否自洽。"""
    states = getattr(component_type, "supported_states", None)
    accessors = getattr(component_type, "state_accessors", None)
    events = getattr(component_type, "supported_events", None)
    methods = getattr(component_type, "event_methods", None)
    if not isinstance(states, tuple) or not isinstance(accessors, dict):
        raise KitContractError(f"{tag} 缺少 supported_states 或 state_accessors")
    if set(states) != set(accessors):
        raise KitContractError(f"{tag} 的状态与映射不一致：{states} 对 {tuple(accessors)}")
    for state, pair in accessors.items():
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise KitContractError(f"{tag} 的状态 {state} 必须映射到读取与写入两个方法名")
        for method_name in pair:
            if not callable(getattr(component_type, method_name, None)):
                raise KitContractError(f"{tag} 的 {state} 映射到不存在的方法 {method_name}")
    if not isinstance(events, tuple) or not isinstance(methods, dict):
        raise KitContractError(f"{tag} 缺少 supported_events 或 event_methods")
    if set(events) != set(methods):
        raise KitContractError(f"{tag} 的事件与映射不一致：{events} 对 {tuple(methods)}")
    for event, method_name in methods.items():
        if not method_name.startswith("on_"):
            raise KitContractError(f"{tag} 的事件 {event} 注册方法必须以 on_ 开头")
        if not callable(getattr(component_type, method_name, None)):
            raise KitContractError(f"{tag} 的事件 {event} 映射到不存在的方法 {method_name}")


def validate_component_table(component_types: dict[str, Any]) -> None:
    """校验宿主组件表：21 个既有标签必须齐备且能力表合法。"""
    if not isinstance(component_types, dict):
        raise KitContractError("组件表必须是字典")
    missing = [tag for tag in REQUIRED_TAGS if tag not in component_types]
    if missing:
        raise KitContractError(f"组件表缺少组件：{', '.join(missing)}")
    for tag in REQUIRED_TAGS:
        validate_component_class(tag, component_types[tag])


def validate_provider(provider: Any) -> None:
    """校验 kit 工厂返回的 provider：主题只提供样式与调色板。"""
    for attribute in ("name", "version", "mode", "stylesheet"):
        if not hasattr(provider, attribute):
            raise KitContractError(f"provider 缺少 {attribute}")
    if not isinstance(provider.stylesheet, str) or not provider.stylesheet.strip():
        raise KitContractError("provider.stylesheet 必须是非空字符串")
    palette = getattr(provider, "palette", None)
    if not isinstance(palette, dict) or not palette:
        raise KitContractError("provider.palette 必须是非空字典")
