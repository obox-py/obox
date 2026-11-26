"""把解析后的节点树装配成原生控件树，并支持 o-for / o-if 与值绑定。"""

from __future__ import annotations

import re
from typing import Any, Callable

from obox.qt import QFrame, QVBoxLayout, QWidget

from ..api.component import ComponentEventMessage
from ..api.errors import OboxError
from ..api.message import OB_BOX
from .parser import Node
from .registry import ComponentRegistry
from .template import Binding, Region, has_binding, resolve_text

DIRECTIVES = ("o-for", "o-if")
_SINGLE = re.compile(r"^\{\{\s*([^{}]+?)\s*\}\}$")


class BuildError(OboxError):
    code = "E_BUILD"


EventSender = Callable[[ComponentEventMessage], None]


class Builder:
    """负责装配、登记组件，并按片段的 on_ 属性订阅事件。"""

    def __init__(
        self,
        owner: str,
        registry: ComponentRegistry,
        component_types: dict[str, type],
        event_sender: EventSender | None = None,
        spacing: dict[str, int] | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.owner = owner
        self.registry = registry
        self.component_types = component_types
        self.event_sender = event_sender
        self.spacing = spacing or {}
        self.data: dict[str, Any] = dict(data or {})
        self._created: list[Any] = []
        self._bindings: list[Binding] = []
        self._regions: list[Region] = []

    @property
    def created_ids(self) -> list[str]:
        return [component.id for component in self._created]

    @property
    def bindings(self) -> list[Binding]:
        return self._bindings

    @property
    def regions(self) -> list[Region]:
        return self._regions

    def build(self, nodes: list[Node]) -> QWidget:
        self._created = []
        self._bindings = []
        self._regions = []
        root = QFrame()
        root.setObjectName("obox-view-root")
        margin = int(self.spacing.get("margin", 20))
        gap = int(self.spacing.get("gap", 16))
        layout = QVBoxLayout(root)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(gap)
        scope = dict(self.data)
        try:
            for node in nodes:
                self._build_into(node, layout, scope, "")
        except Exception:
            for component in self._created:
                self.registry.unregister(component.owner, component.id)
            self._created.clear()
            raise
        for component in self._created:
            component.attach(root)
        layout.addStretch(1)
        return root

    def _build_into(self, node: Node, layout: Any, scope: dict[str, Any], parent_tag: str) -> None:
        if any(name in node.attrs for name in DIRECTIVES):
            region = Region(self, layout, node, self._loop_scope(scope))
            region.build()
            self._regions.append(region)
            return
        widget = self._build_node(node, scope)
        if widget is None:
            return
        if parent_tag in ("flex", "choice") and node.attrs.get("grow") is not None:
            widget.setProperty("flex_grow", resolve_text(str(node.attrs["grow"]), scope))
        layout.addWidget(widget)

    def _build_node(self, node: Node, scope: dict[str, Any]) -> QWidget | None:
        tag = node.tag.lower()
        component_type = self.component_types.get(tag)
        if component_type is None:
            raise BuildError(f"第 {node.line} 行第 {node.col} 列：未注册的组件标签 {node.tag}")
        attrs = {
            key: value if key in DIRECTIVES else resolve_text(str(value), scope)
            for key, value in node.attrs.items()
        }
        component_id = attrs.get("id") or node.component_id
        if not component_id:
            raise BuildError(f"第 {node.line} 行第 {node.col} 列：{node.tag} 缺少 id")
        attrs.setdefault("children", resolve_text(node.text(), scope))
        component = component_type(component_id, self.owner, attrs)
        self.registry.register(self.owner, component.id, component)
        self._created.append(component)
        if self.event_sender is not None:
            self._bind_events(component, node)
        self._maybe_binding(component, attrs, node, scope)
        layout = component.container_layout()
        if layout is not None:
            for child in node.children:
                if isinstance(child, Node):
                    self._build_into(child, layout, scope, tag)
        return component.widget

    def _maybe_binding(self, component: Any, attrs: dict[str, str], node: Node, scope: dict[str, Any]) -> None:
        text = str(node.attrs.get("text") or node.attrs.get("children") or "")
        if has_binding(text) and hasattr(component, "set_text"):
            expression = _single_expression(text)
            if expression:
                self._bindings.append(Binding(component, "text", expression, self._loop_scope(scope)))
        source = str(node.attrs.get("src") or "")
        for attribute, kind in (("value", "value"), ("checked", "checked")):
            raw = str(node.attrs.get(attribute) or "")
            if not has_binding(raw):
                continue
            expression = _single_expression(raw)
            if not expression:
                continue
            pair = getattr(component, "state_accessors", {}).get(attribute)
            if not pair:
                continue
            try:
                self._bindings.append(
                    Binding(component, kind, expression, self._loop_scope(scope), setter=pair[1])
                )
            except Exception:
                continue
        if has_binding(source) and hasattr(component, "set_path"):
            expression = _single_expression(source)
            if expression:
                self._bindings.append(Binding(component, "path", expression, self._loop_scope(scope)))

    def _loop_scope(self, scope: dict[str, Any]) -> dict[str, Any]:
        """绑定与区域只保留循环变量；数据从 ViewHandle.data 实时取。"""
        return {key: value for key, value in scope.items() if key not in self.data}

    def _bind_events(self, component: Any, node: Node) -> None:
        declared = set(component.event_methods.values())
        for attribute in node.attrs:
            if attribute.startswith("on_") and attribute not in declared:
                raise BuildError(
                    f"第 {node.line} 行第 {node.col} 列：{node.tag} 不支持事件属性 {attribute}"
                )
        for event, method_name in component.event_methods.items():
            if method_name not in node.attrs:
                continue
            handler = getattr(component, method_name)

            def _callback(payload: dict[str, Any] | None = None, _event: str = event) -> None:
                self._on_event(component, _event, payload or {})

            handler(_callback)

    def _on_event(self, component: Any, event: str, payload: dict[str, Any]) -> None:
        if self.event_sender is None:
            return
        self.event_sender(
            ComponentEventMessage(
                src=OB_BOX,
                dst=self.owner,
                component_id=component.id,
                event=event,
                payload=payload,
            )
        )


def _single_expression(text: str) -> str:
    match = _SINGLE.match(text.strip())
    return match.group(1).strip() if match else ""