"""组件注册表：按扩展命名空间隔离组件 id。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api.errors import ComponentConflict, ComponentNotFound

if TYPE_CHECKING:  # 仅类型检查时引入，避免契约层反向依赖表示层
    from .components.base import Component


def _detach(component) -> None:
    """让组件在注销时释放挂在窗口上的控件，避免重建时二次释放。"""
    detach = getattr(component, "detach", None)
    if callable(detach):
        try:
            detach()
        except RuntimeError:
            pass


class ComponentRegistry:
    """owner 是 obox 或 名称.作者；组件 id 只在 owner 内唯一。"""

    def __init__(self) -> None:
        self._by_owner: dict[str, dict[str, "Component"]] = {}

    def register(self, owner: str, component_id: str, component: "Component") -> None:
        bucket = self._by_owner.setdefault(owner, {})
        if component_id in bucket:
            raise ComponentConflict(f"组件 id 冲突：{owner} 已有 {component_id}")
        bucket[component_id] = component

    def lookup(self, owner: str, component_id: str) -> "Component":
        component = self._by_owner.get(owner, {}).get(component_id)
        if component is None:
            raise ComponentNotFound(f"找不到组件：{owner}/{component_id}")
        return component

    def owner_of(self, component_id: str) -> str | None:
        for owner, bucket in self._by_owner.items():
            if component_id in bucket:
                return owner
        return None

    def unregister(self, owner: str, component_id: str) -> None:
        bucket = self._by_owner.get(owner)
        if bucket:
            component = bucket.pop(component_id, None)
            _detach(component)

    def unregister_owner(self, owner: str) -> None:
        bucket = self._by_owner.pop(owner, None) or {}
        for component in bucket.values():
            _detach(component)

    def count(self, owner: str | None = None) -> int:
        if owner is None:
            return sum(len(bucket) for bucket in self._by_owner.values())
        return len(self._by_owner.get(owner, {}))
