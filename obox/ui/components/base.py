"""组件基类：声明能力表，提供控件与宿主的通用行为。

能力表是 kit 与 obox 之间的契约：状态走 state_accessors，事件走 event_methods。
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import QLayout, QWidget

EventCallback = Callable[[dict[str, Any]], None]


class Component:
    """所有组件的共同部分；子类给出控件与类型化方法。"""

    tag = ""
    supported_states: tuple[str, ...] = ()
    state_accessors: dict[str, tuple[str, str]] = {}
    supported_events: tuple[str, ...] = ()
    event_methods: dict[str, str] = {}

    def __init__(self, component_id: str, owner: str, attrs: dict[str, str]) -> None:
        self.id = component_id
        self.owner = owner
        self.attrs = attrs
        self.widget = self.build_widget(attrs)
        self.widget.setObjectName(component_id)

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        raise NotImplementedError

    def detach(self) -> None:
        """视图销毁或换语言时释放挂在窗口上的控件；默认没有额外资源。"""

    def attach(self, host: QWidget) -> None:
        """装配完成后挂到视图根控件；需要宿主的组件重写。"""

    def container_layout(self) -> QLayout | None:
        return None

    # 通用状态：可见与可用，所有组件共有
    def is_visible(self) -> bool:
        return self.widget.isVisible()

    def set_visible(self, value: Any) -> None:
        self.widget.setVisible(bool(value))

    def is_enabled(self) -> bool:
        return self.widget.isEnabled()

    def set_enabled(self, value: Any) -> None:
        self.widget.setEnabled(bool(value))
BORDER_SIDES = {"all", "none", "top", "right", "bottom", "left"}


def border_css(attrs: dict[str, str], default: str = "all", color: str = "rgba(0,0,0,0.12)") -> str:
    """按片段的 border 属性生成边框声明：all、none 或逗号分隔的边。"""
    value = (attrs.get("border") or default).strip()
    if value == "none":
        return "border: none;"
    sides = [item.strip() for item in value.split(",") if item.strip()]
    if not sides:
        sides = ["all"]
    invalid = [side for side in sides if side not in BORDER_SIDES]
    if invalid:
        raise ValueError(f"border 取值非法：{', '.join(invalid)}；可选：all、none、top、right、bottom、left")
    if "all" in sides:
        return f"border: 1px solid {color};"
    return " ".join(f"border-{side}: 1px solid {color};" for side in sides)

def color(value: str):
    """把 rgba()/rgb()/hex 字符串转成 QColor；绘制时用。"""
    from PySide6.QtGui import QColor

    text = value.strip()
    if text.startswith("rgba(") or text.startswith("rgb("):
        body = text[text.index("(") + 1 : text.rindex(")")]
        parts = [part.strip() for part in body.split(",")]
        channels = [int(float(part)) for part in parts[:3]]
        alpha = int(float(parts[3]) * 255) if len(parts) > 3 else 255
        return QColor(channels[0], channels[1], channels[2], alpha)
    return QColor(text)
def animate(widget, prop: bytes, start: float, end: float, duration: int = 160):
    """对自定义 Qt 属性做一次 OutCubic 过渡；动画结束自动回收。"""
    from PySide6.QtCore import QEasingCurve, QPropertyAnimation

    animation = QPropertyAnimation(widget, prop, widget)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation
