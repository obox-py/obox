"""主窗口状态栏：左右两区，按 priority 从高到低排列，点击项触发命令。

状态栏只负责呈现与发信号，命令执行交给 app；配色来自 obox.ui.palette，
套件切换后由 app 调用 apply_palette() 重刷。
"""

from __future__ import annotations

from obox.qt import Qt, Signal
from obox.qt import QFrame, QHBoxLayout, QLabel, QWidget

from . import palette

LEFT = "left"
RIGHT = "right"
ALIGNMENTS = (LEFT, RIGHT)
HEIGHT = 24


class StatusBarItem(QWidget):
    """一项状态栏内容；command 为空时不可点击。"""

    activated = Signal(str)

    def __init__(
        self,
        text: str = "",
        alignment: str = LEFT,
        priority: int = 0,
        tooltip: str = "",
        command: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._alignment = alignment if alignment in ALIGNMENTS else LEFT
        self._priority = int(priority)
        self._command = str(command or "")
        self._label = QLabel(str(text), self)
        self._label.setObjectName("obox-statusbar-text")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._label)
        self.setToolTip(str(tooltip or ""))
        self._sync_cursor()
        self.apply_palette()

    @property
    def alignment(self) -> str:
        return self._alignment

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def command(self) -> str:
        return self._command

    def text(self) -> str:
        return self._label.text()

    def set_text(self, text: str) -> None:
        self._label.setText(str(text or ""))

    def set_tooltip(self, tooltip: str) -> None:
        self.setToolTip(str(tooltip or ""))

    def set_command(self, command: str) -> None:
        self._command = str(command or "")
        self._sync_cursor()

    def activate(self) -> None:
        """单击等价动作：有命令才发出信号。"""
        if self._command:
            self.activated.emit(self._command)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if event.button() == Qt.MouseButton.LeftButton:
            self.activate()
        super().mouseReleaseEvent(event)

    def apply_palette(self) -> None:
        color = palette.TEXT if self._command else palette.TEXT_MUTED
        self._label.setStyleSheet(
            f"color: {color}; font-size: 12px; font-family: '{palette.FONT_FAMILY}';"
            " background: transparent;"
        )

    def _sync_cursor(self) -> None:
        cursor = Qt.CursorShape.PointingHandCursor if self._command else Qt.CursorShape.ArrowCursor
        self.setCursor(cursor)


class StatusBar(QFrame):
    """左右两区容器；左侧靠左、右侧靠右，各自按 priority 排序。"""

    command_triggered = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("obox-statusbar")
        self.setFixedHeight(HEIGHT)
        self._items: list[StatusBarItem] = []

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 0, 10, 0)
        outer.setSpacing(16)
        self._left = QWidget(self)
        self._left_layout = QHBoxLayout(self._left)
        self._left_layout.setContentsMargins(0, 0, 0, 0)
        self._left_layout.setSpacing(12)
        self._left_layout.addStretch(1)
        self._right = QWidget(self)
        self._right_layout = QHBoxLayout(self._right)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(12)
        self._right_layout.addStretch(1)
        outer.addWidget(self._left, 1)
        outer.addWidget(self._right, 0)
        self.apply_palette()

    def add_item(
        self,
        text: str = "",
        alignment: str = LEFT,
        priority: int = 0,
        tooltip: str = "",
        command: str = "",
    ) -> StatusBarItem:
        if alignment not in ALIGNMENTS:
            raise ValueError(f"alignment 只能是 left 或 right：{alignment!r}")
        parent = self._left if alignment == LEFT else self._right
        item = StatusBarItem(text, alignment, priority, tooltip, command, parent)
        item.activated.connect(self.command_triggered.emit)
        self._items.append(item)
        self._reorder()
        return item

    def remove_item(self, item: StatusBarItem) -> bool:
        if item not in self._items:
            return False
        layout = self._left_layout if item.alignment == LEFT else self._right_layout
        layout.removeWidget(item)
        self._items.remove(item)
        item.setParent(None)
        item.deleteLater()
        self._reorder()
        return True

    def items(self, alignment: str | None = None) -> list[StatusBarItem]:
        """按显示顺序返回；同 priority 保持加入顺序。"""
        selected = [item for item in self._items if alignment is None or item.alignment == alignment]
        return sorted(selected, key=lambda item: -item.priority)

    def clear(self) -> None:
        for item in list(self._items):
            self.remove_item(item)

    def apply_palette(self) -> None:
        self.setStyleSheet(
            "QFrame#obox-statusbar { "
            f"background: {palette.SURFACE_MUTED}; border-top: 1px solid {palette.LINE}; }}"
        )
        for item in self._items:
            item.apply_palette()

    def _reorder(self) -> None:
        for item in self._items:
            layout = self._left_layout if item.alignment == LEFT else self._right_layout
            layout.removeWidget(item)
        for alignment, layout in ((LEFT, self._left_layout), (RIGHT, self._right_layout)):
            offset = 0 if alignment == LEFT else 1
            for index, item in enumerate(self.items(alignment)):
                layout.insertWidget(index + offset, item)
