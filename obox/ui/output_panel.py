"""输出面板：按通道缓存日志文本，一次只显示一个通道。

宿主把通道日志 append 进来、由 show_channel 打开面板；配色来自
obox.ui.palette，套件切换后由 app 调用 apply_palette() 重刷。
"""

from __future__ import annotations

from obox.qt import Qt
from obox.qt import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextCursor,
    QVBoxLayout,
    QWidget,
)

from . import palette

MAX_LINES = 5000
MAX_CHARS = 1_000_000
_TRIM_SLACK = 256


class OutputPanel(QFrame):
    """底部输出面板：标题栏选通道 + 只读文本区。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("obox-output-panel")
        self._buffers: dict[str, str] = {}
        self._lines: dict[str, int] = {}
        self._current = ""

        self._header = QFrame(self)
        self._header.setObjectName("obox-output-header")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(10, 4, 10, 4)
        header_layout.setSpacing(8)
        self._title = QLabel("输出", self._header)
        self._title.setObjectName("obox-output-title")
        self._channels = QComboBox(self._header)
        self._channels.setObjectName("obox-output-channels")
        self._channels.setMinimumWidth(160)
        self._clear = QPushButton("清空", self._header)
        self._clear.setObjectName("obox-output-clear")
        self._clear.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self._title)
        header_layout.addWidget(self._channels)
        header_layout.addStretch(1)
        header_layout.addWidget(self._clear)

        self._text = QPlainTextEdit(self)
        self._text.setObjectName("obox-output-text")
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(MAX_LINES)
        self._text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._text, 1)

        self._channels.currentTextChanged.connect(self._on_channel_changed)
        self._clear.clicked.connect(self.clear_current)
        self.apply_palette()
        # 与 VS Code 一致：append 不弹面板，show_channel 才打开
        self.hide()

    # ---------- 通道 ----------
    def create_channel(self, name: str) -> str:
        channel = str(name or "").strip()
        if not channel:
            raise ValueError("输出通道名不能为空")
        if channel not in self._buffers:
            self._buffers[channel] = ""
            self._lines[channel] = 0
            self._channels.addItem(channel)
        if not self._current:
            self._select(channel)
        return channel

    def channels(self) -> list[str]:
        return list(self._buffers)

    def has_channel(self, name: str) -> bool:
        return str(name or "").strip() in self._buffers

    def current_channel(self) -> str:
        return self._current

    def show_channel(self, name: str = "", preserveFocus: bool = False) -> str:
        """打开面板并切换到指定通道；空名沿用当前通道。"""
        channel = str(name or "").strip()
        if channel and channel not in self._buffers:
            self.create_channel(channel)
        if not channel:
            channel = self._current or next(iter(self._buffers), "")
        if channel:
            self._select(channel)
        self.show()
        self.raise_()
        if not preserveFocus:
            self._text.setFocus()
        return channel

    # ---------- 文本 ----------
    def append(self, name: str, text: str) -> None:
        channel = self.create_channel(name)
        chunk = str(text)
        if not chunk:
            return
        self._store(channel, chunk)
        if channel == self._current:
            self._text.moveCursor(QTextCursor.MoveOperation.End)
            self._text.insertPlainText(chunk)
            self._scroll_to_end()

    def append_line(self, name: str, text: str = "") -> None:
        self.append(name, str(text) + "\n")

    def text(self, name: str = "") -> str:
        return self._buffers.get(str(name or self._current).strip(), "")

    def clear(self, name: str = "") -> None:
        channel = str(name or self._current).strip()
        if channel not in self._buffers:
            return
        self._buffers[channel] = ""
        self._lines[channel] = 0
        if channel == self._current:
            self._text.clear()

    def clear_current(self) -> None:
        self.clear(self._current)

    def text_widget(self) -> QPlainTextEdit:
        return self._text

    def channel_combo(self) -> QComboBox:
        return self._channels

    # ---------- 主题 ----------
    def apply_palette(self) -> None:
        self.setStyleSheet(
            "QFrame#obox-output-panel { "
            f"background: {palette.SURFACE}; border-top: 1px solid {palette.LINE}; }}"
        )
        self._header.setStyleSheet(
            "QFrame#obox-output-header { "
            f"background: {palette.SURFACE_MUTED}; border-bottom: 1px solid {palette.LINE}; }}"
        )
        self._title.setStyleSheet(
            f"color: {palette.TEXT_MUTED}; font-size: 12px; font-family: '{palette.FONT_FAMILY}';"
        )
        self._channels.setStyleSheet(
            f"QComboBox {{ background: {palette.SURFACE}; color: {palette.TEXT};"
            f" border: 1px solid {palette.INPUT_BORDER}; border-radius: {palette.RADIUS_CONTROL}px;"
            f" padding: 2px 8px; }}"
        )
        self._clear.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {palette.TEXT_MUTED};"
            " padding: 2px 6px; }"
            f"QPushButton:hover {{ color: {palette.ACCENT}; }}"
        )
        self._text.setStyleSheet(
            "QPlainTextEdit#obox-output-text { "
            f"background: {palette.SURFACE}; color: {palette.TEXT}; border: none;"
            f" font-family: '{palette.FONT_FAMILY}'; font-size: 12px; }}"
        )

    # ---------- 内部 ----------
    def _store(self, channel: str, chunk: str) -> None:
        text = self._buffers.get(channel, "") + chunk
        self._lines[channel] = self._lines.get(channel, 0) + chunk.count("\n")
        if self._lines[channel] > MAX_LINES + _TRIM_SLACK:
            kept = text.splitlines(keepends=True)[-MAX_LINES:]
            text = "".join(kept)
            self._lines[channel] = len(kept)
        if len(text) > MAX_CHARS:
            text = text[-MAX_CHARS:]
            cut = text.find("\n")
            if cut >= 0:
                text = text[cut + 1 :]
            self._lines[channel] = text.count("\n")
        self._buffers[channel] = text

    def _select(self, channel: str) -> None:
        if not channel or channel not in self._buffers:
            return
        index = self._channels.findText(channel)
        if index >= 0 and index != self._channels.currentIndex():
            self._channels.setCurrentIndex(index)
        if self._current != channel:
            self._render(channel)

    def _render(self, channel: str) -> None:
        self._current = channel
        self._text.setPlainText(self._buffers.get(channel, ""))
        self._scroll_to_end()

    def _on_channel_changed(self, name: str) -> None:
        if name and name in self._buffers:
            self._render(name)

    def _scroll_to_end(self) -> None:
        bar = self._text.verticalScrollBar()
        bar.setValue(bar.maximum())
