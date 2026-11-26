"""选择容器：单选或多选，里面放 Card。"""

from __future__ import annotations

from typing import Any

from obox.qt import QWidget

from .base import Component
from .card import CardWidget, card_value
from .flex import FlexLayout

_MODES = {"single", "multiple"}


class ChoiceLayout(FlexLayout):
    """在 Flex 排布之上把 Card 的点击接到容器。"""

    def __init__(self, attrs: dict[str, str], parent: QWidget, on_card) -> None:
        super().__init__(attrs, parent)
        self._on_card = on_card

    def addWidget(self, widget: QWidget) -> None:  # noqa: N802 - Qt 接口
        super().addWidget(widget)
        if isinstance(widget, CardWidget):
            widget.clicked.connect(lambda w=widget: self._on_card(w))


class ChoiceComponent(Component):
    tag = "choice"
    supported_states = ("value",)
    state_accessors = {"value": ("value", "set_value")}
    supported_events = ("change",)
    event_methods = {"change": "on_change"}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        mode = attrs.get("mode", "single")
        if mode not in _MODES:
            raise ValueError(f"mode 取值非法：{mode}；可选：single、multiple")
        self.mode = mode
        self._selected: set[str] = set()
        self._callback = None
        initial = (attrs.get("value") or "").strip()
        if initial:
            self._selected = {item.strip() for item in initial.split(",") if item.strip()}
        widget = QWidget()
        self._layout = ChoiceLayout(attrs, widget, self._on_card_clicked)
        return widget

    def container_layout(self) -> ChoiceLayout:
        return self._layout

    def _on_card_clicked(self, widget: QWidget) -> None:
        value = card_value(widget)
        if self.mode == "single":
            self._selected = set() if value in self._selected else {value}
        elif value in self._selected:
            self._selected.discard(value)
        else:
            self._selected.add(value)
        self._refresh_cards()
        if self._callback is not None:
            self._callback({"value": sorted(self._selected)})

    def _refresh_cards(self) -> None:
        for index in range(self._layout.count()):
            item = self._layout.itemAt(index)
            widget = item.widget() if item is not None else None
            if isinstance(widget, CardWidget):
                widget.set_selected(card_value(widget) in self._selected)

    def value(self) -> list[str]:
        return sorted(self._selected)

    def set_value(self, value: Any) -> None:
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
        else:
            items = [str(item) for item in (value or [])]
        if self.mode == "single":
            items = items[:1]
        self._selected = set(items)
        self._refresh_cards()

    def on_change(self, callback) -> None:
        self._callback = callback
