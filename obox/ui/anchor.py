"""视图滚动锚点：平滑滚动到章节，并按视口计算当前章节。"""

from __future__ import annotations

from obox.qt import QEasingCurve, QObject, QPropertyAnimation, Signal
from obox.qt import QScrollArea, QWidget

DEFAULT_OFFSET = 64
DEFAULT_DURATION = 600


class AnchorController(QObject):
    """一个滚动区对应一个控制器；章节是内容里的直接子组件（id 即锚点）。"""

    anchor_changed = Signal(str)

    def __init__(
        self,
        scroll_area: QScrollArea,
        content: QWidget,
        offset: int = DEFAULT_OFFSET,
        duration: int = DEFAULT_DURATION,
        parent: QObject | None = None,
        sections_root: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._area = scroll_area
        self._content = content
        self._sections_root = sections_root or content
        self._offset = offset
        self._duration = duration
        self._animation = QPropertyAnimation(scroll_area.verticalScrollBar(), b"value", self)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._last_anchor = ""
        scroll_area.verticalScrollBar().valueChanged.connect(self._refresh)

    def sections(self) -> list[QWidget]:
        layout = self._sections_root.layout()
        if layout is None:
            return []
        widgets: list[QWidget] = []
        for index in range(layout.count()):
            item = layout.itemAt(index)
            widget = item.widget() if item is not None else None
            if widget is not None and widget.objectName():
                widgets.append(widget)
        return widgets

    def scroll_to(self, anchor: str, offset: int | None = None, duration: int | None = None) -> bool:
        target = next((item for item in self.sections() if item.objectName() == anchor), None)
        if target is None:
            return False
        offset = self._offset if offset is None else int(offset)
        duration = self._duration if duration is None else int(duration)
        bar = self._area.verticalScrollBar()
        top = target.mapTo(self._content, target.rect().topLeft()).y()
        destination = max(0, min(bar.maximum(), top - offset))
        self._animation.stop()
        self._animation.setDuration(max(0, duration))
        self._animation.setStartValue(bar.value())
        self._animation.setEndValue(destination)
        self._animation.start()
        return True

    def current_anchor(self) -> str:
        widget = self._anchor_at(self._area.verticalScrollBar().value())
        return widget.objectName() if widget is not None else ""

    def _anchor_at(self, scroll_top: int) -> QWidget | None:
        sections = self.sections()
        if not sections:
            return None
        bar = self._area.verticalScrollBar()
        if bar.maximum() > 0 and scroll_top >= bar.maximum():
            return sections[-1]
        threshold = scroll_top + self._offset
        chosen = sections[0]
        for widget in sections:
            top = widget.mapTo(self._content, widget.rect().topLeft()).y()
            if top <= threshold:
                chosen = widget
            else:
                break
        return chosen

    def _refresh(self) -> None:
        widget = self._anchor_at(self._area.verticalScrollBar().value())
        anchor = widget.objectName() if widget is not None else ""
        if anchor == self._last_anchor:
            return
        self._last_anchor = anchor
        self.anchor_changed.emit(anchor)