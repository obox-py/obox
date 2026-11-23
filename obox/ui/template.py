"""视图句柄：数据、绑定与 o-for / o-if 的局部更新。"""

from __future__ import annotations

import re
from typing import Any

from .expr import evaluate, format_value, is_truthy

_BINDING = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def resolve_text(source: str, scope: dict[str, Any]) -> str:
    """把 {{expr}} 换成求值结果；解析不了的保持原样（i18n 已在此之前替换）。"""

    def replace(match: re.Match[str]) -> str:
        expression = match.group(1).strip()
        if expression.startswith("i18n."):
            return match.group(0)
        try:
            return format_value(evaluate(expression, scope))
        except Exception:
            return match.group(0)

    return _BINDING.sub(replace, source)


def has_binding(source: str) -> bool:
    return bool(_BINDING.search(source or ""))


class Binding:
    """一个文本或图片路径绑定，数据更新时原地改写。"""

    def __init__(
        self,
        component: Any,
        kind: str,
        expression: str,
        scope: dict[str, Any],
        setter: str = "",
    ) -> None:
        self.component = component
        self.kind = kind
        self.expression = expression
        self.scope = dict(scope)
        self.setter = setter
        self.view: ViewHandle | None = None

    def apply(self) -> None:
        merged = {**self.scope}
        if self.view is not None:
            merged = {**self.view.data, **self.scope}
        try:
            value = evaluate(self.expression, merged)
        except Exception:
            return
        if self.kind == "text":
            self.component.set_text(format_value(value))
        elif self.kind == "path":
            self.component.set_path(format_value(value))
        elif self.kind in ("value", "checked") and self.setter:
            if self.kind == "checked":
                target = getattr(self.component, self.setter)
                target(bool(value))
            else:
                getattr(self.component, self.setter)(format_value(value))


class Region:
    """o-for 或 o-if 作用的一块区域；数据变化时只重建这一块。"""

    def __init__(self, builder: Any, layout: Any, node: Any, scope: dict[str, Any]) -> None:
        self.builder = builder
        self.layout = layout
        self.node = node
        self.scope = dict(scope)
        self.view: ViewHandle | None = None
        self._widgets: list[Any] = []
        self._components: list[Any] = []
        self._nested_regions: list[Region] = []
        self._nested_bindings: list[Any] = []
        self._signature: Any = object()

    def _merged(self) -> dict[str, Any]:
        data = self.view.data if self.view is not None else self.builder.data
        return {**data, **self.scope}

    def _signature_of(self) -> Any:
        attrs = self.node.attrs
        condition = attrs.get("o-if")
        if condition is not None:
            try:
                active = is_truthy(evaluate(condition, self._merged()))
            except Exception:
                active = False
            if not active:
                return ("if", False)
        loop = attrs.get("o-for")
        if loop:
            _, _, list_expression = loop.partition(" in ")
            try:
                items = evaluate(list_expression.strip(), self._merged()) or []
            except Exception:
                items = []
            if isinstance(items, dict):
                items = list(items.values())
            if not isinstance(items, (list, tuple)):
                items = []
            return ("for", tuple(repr(item) for item in items))
        return ("plain",)

    def build(self) -> None:
        self._clear()
        signature = self._signature_of()
        self._signature = signature
        if signature == ("if", False):
            return
        attrs = self.node.attrs
        loop = attrs.get("o-for")
        before = len(self.builder._created)
        before_regions = len(self.builder._regions)
        before_bindings = len(self.builder._bindings)
        if loop:
            variable, _, list_expression = loop.partition(" in ")
            variable = variable.strip() or "item"
            try:
                items = evaluate(list_expression.strip(), self._merged()) or []
            except Exception:
                items = []
            if isinstance(items, dict):
                items = list(items.values())
            for index, item in enumerate(items):
                scope = {**self.scope, variable: item, "index": index}
                widget = self.builder._build_node(self.node, scope)
                if widget is not None:
                    self._add(widget)
        else:
            widget = self.builder._build_node(self.node, self.scope)
            if widget is not None:
                self._add(widget)
        self._components = list(self.builder._created[before:])
        self._nested_regions = list(self.builder._regions[before_regions:])
        self._nested_bindings = list(self.builder._bindings[before_bindings:])

    def _add(self, widget: Any) -> None:
        grow = self.node.attrs.get("grow")
        if grow is not None:
            widget.setProperty("flex_grow", resolve_text(str(grow), self._merged()))
        self.layout.addWidget(widget)
        self._widgets.append(widget)

    def refresh(self) -> None:
        if self._signature_of() != self._signature:
            self.build()

    def _clear(self) -> None:
        for region in self._nested_regions:
            if region in self.builder._regions:
                self.builder._regions.remove(region)
        self._nested_regions.clear()
        for binding in self._nested_bindings:
            if binding in self.builder._bindings:
                self.builder._bindings.remove(binding)
        self._nested_bindings.clear()
        for component in self._components:
            self.builder.registry.unregister(component.owner, component.id)
            if component in self.builder._created:
                self.builder._created.remove(component)
        self._components.clear()
        for widget in self._widgets:
            self.layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self._widgets.clear()


class ViewHandle:
    """一棵视图的运行时：数据、绑定与区域。"""

    def __init__(self, builder: Any, root: Any, data: dict[str, Any]) -> None:
        self.builder = builder
        self.root = root
        self.data = dict(data)
        self.bindings: list[Binding] = []
        self.regions: list[Region] = []

    def attach(self, bindings: list[Binding], regions: list[Region]) -> None:
        for binding in bindings:
            binding.view = self
            self.bindings.append(binding)
        for region in regions:
            region.view = self
            self.regions.append(region)

    def set_data(self, updates: dict[str, Any]) -> None:
        self.data.update(updates or {})
        self.refresh()

    def refresh(self) -> None:
        for region in list(self.regions):
            region.refresh()
        for binding in list(self.bindings):
            binding.apply()