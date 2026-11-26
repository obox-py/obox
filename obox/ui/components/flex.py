"""Flex 容器：按 CSS flex 的常用子集排布子组件。"""

from __future__ import annotations

from obox.qt import QRect, QSize, Qt
from obox.qt import QLayout, QLayoutItem, QWidget

from .base import Component

_DIRECTIONS = {"row", "row-reverse", "column", "column-reverse"}
_WRAPS = {"nowrap", "wrap", "wrap-reverse"}
_JUSTIFY = {"start", "center", "end", "space-between", "space-around", "space-evenly"}
_ALIGN = {"start", "center", "end", "stretch"}


class FlexLayout(QLayout):
    """一个按主轴排布、可换行、可按剩余空间伸缩的布局。"""

    def __init__(self, attrs: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.direction = _pick(attrs, "direction", _DIRECTIONS, "row")
        self.wrap = _pick(attrs, "wrap", _WRAPS, "nowrap")
        self.justify = _pick(attrs, "justify", _JUSTIFY, "start")
        self.align_items = _pick(attrs, "align", _ALIGN, "start")
        self.gap = int(attrs.get("gap", "12"))
        self.setContentsMargins(0, 0, 0, 0)
        self._items: list[QLayoutItem] = []

    def addItem(self, item: QLayoutItem) -> None:  # noqa: N802 - Qt 接口
        self._items.append(item)
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:  # noqa: N802
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int) -> QLayoutItem | None:  # noqa: N802
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self) -> Qt.Orientation:  # noqa: N802
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return self.direction.startswith("row")

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        if not self.direction.startswith("row"):
            return self.sizeHint().height()
        return self._arrange(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._arrange(rect, apply=True)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self._natural_size()

    def minimumSize(self) -> QSize:  # noqa: N802
        return self._natural_size()

    def _natural_size(self) -> QSize:
        """不换行时的自然尺寸：主轴求和、交叉轴取最大。"""
        if not self._items:
            return QSize(0, 0)
        sizes = [_size_of(item) for item in self._items]
        gap = self.gap * (len(sizes) - 1)
        if self.direction.startswith("row"):
            if self.wrap != "nowrap":
                widest = max(size.width() for size in sizes)
                return QSize(widest, self._arrange(QRect(0, 0, widest, 0), apply=False))
            return QSize(
                sum(size.width() for size in sizes) + gap,
                max(size.height() for size in sizes),
            )
        return QSize(
            max(size.width() for size in sizes),
            sum(size.height() for size in sizes) + gap,
        )

    def _grow(self, item: QLayoutItem) -> int:
        widget = item.widget()
        if widget is None:
            return 0
        value = widget.property("flex_grow")
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return 0

    def _arrange(self, rect: QRect, apply: bool) -> int:
        horizontal = self.direction.startswith("row")
        reverse_main = self.direction.endswith("reverse")
        items = list(self._items)
        if reverse_main:
            items.reverse()
        main_start = rect.x() if horizontal else rect.y()
        main_limit = rect.width() if horizontal else rect.height()
        lines: list[list[QLayoutItem]] = []
        line_sizes: list[int] = []
        line_thickness: list[int] = []
        current: list[QLayoutItem] = []
        used = 0
        for item in items:
            size = _size_of(item)
            main_size = size.width() if horizontal else size.height()
            needed = main_size + (self.gap if current else 0)
            if self.wrap != "nowrap" and current and used + needed > main_limit:
                lines.append(current)
                line_sizes.append(used)
                line_thickness.append(max((self._cross(i) for i in current), default=0))
                current, used = [], 0
                needed = main_size
            current.append(item)
            used += needed
        if current:
            lines.append(current)
            line_sizes.append(used)
            line_thickness.append(max((self._cross(i) for i in current), default=0))

        cross_limit = rect.height() if horizontal else rect.width()
        if len(lines) == 1 and self.wrap == "nowrap" and cross_limit > 0:
            line_thickness = [cross_limit]
        total = sum(line_thickness) + self.gap * max(len(lines) - 1, 0)
        offset = 0
        for index, line in enumerate(lines):
            self._place_line(line, line_sizes[index], line_thickness[index], main_start, offset, rect, horizontal, apply)
            offset += line_thickness[index] + self.gap
        return total

    def _cross(self, item: QLayoutItem) -> int:
        size = _size_of(item)
        return size.height() if self.direction.startswith("row") else size.width()

    def _place_line(self, line, used, thickness, main_start, offset, rect, horizontal, apply) -> None:
        remaining = (rect.width() if horizontal else rect.height()) - used
        grows = sum(self._grow(item) for item in line)
        extras = [0] * len(line)
        if grows:
            share = max(remaining, 0)
            for i, item in enumerate(line):
                extras[i] = share * self._grow(item) // grows
        start_offset = 0
        if not grows and self.justify == "center":
            start_offset = max(remaining, 0) // 2
        elif not grows and self.justify == "end":
            start_offset = max(remaining, 0)

        cursor = main_start + start_offset
        for index, item in enumerate(line):
            size = _size_of(item)
            main_size = (size.width() if horizontal else size.height()) + extras[index]
            cross_size = size.height() if horizontal else size.width()
            cross_offset = offset
            if self.align_items == "center":
                cross_offset = offset + max((thickness - cross_size) // 2, 0)
            elif self.align_items == "end":
                cross_offset = offset + max(thickness - cross_size, 0)
            elif self.align_items == "stretch":
                cross_size = thickness
            if horizontal:
                target = QRect(cursor, rect.y() + cross_offset, main_size, cross_size)
            else:
                target = QRect(rect.x() + cross_offset, cursor, cross_size, main_size)
            if apply:
                item.setGeometry(target)
            cursor += main_size
            if grows == 0 and self.justify == "space-between" and index < len(line) - 1:
                step = remaining // max(len(line) - 1, 1)
                cursor += max(step, 0)
            elif grows == 0 and self.justify == "space-around":
                step = remaining // max(len(line), 1)
                cursor += max(step // 2, 0) if index == 0 else max(step, 0)
            else:
                cursor += self.gap


class FlexComponent(Component):
    tag = "flex"
    supported_states: tuple[str, ...] = ()
    state_accessors: dict[str, tuple[str, str]] = {}
    supported_events: tuple[str, ...] = ()
    event_methods: dict[str, str] = {}

    def build_widget(self, attrs: dict[str, str]) -> QWidget:
        widget = QWidget()
        self._layout = FlexLayout(attrs, widget)
        return widget

    def container_layout(self) -> QLayout:
        return self._layout


def _size_of(item: QLayoutItem) -> QSize:
    """取 sizeHint 与 minimumSize 的较大者，避免滑块这类最小宽度被忽略。"""
    return item.sizeHint().expandedTo(item.minimumSize())


def _pick(attrs: dict[str, str], key: str, allowed: set[str], default: str) -> str:
    value = attrs.get(key, default)
    if value not in allowed:
        raise ValueError(f"{key} 取值非法：{value}；可选：{', '.join(sorted(allowed))}")
    return value