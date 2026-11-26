"""浮层式对话框基类：遮罩铺满父窗口、居中面板、标题与按钮区共用一套。"""

from __future__ import annotations

from obox.qt import Qt
from obox.qt import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ModalPanelDialog(QDialog):
    def __init__(self, parent=None, title: str = "", message: str = "", glyph: str = "i") -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("obox-modal-overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card = QFrame(self)
        card.setObjectName("obox-modal-card")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setFixedWidth(420)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(14)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        badge = QLabel(glyph, card)
        badge.setObjectName("obox-modal-badge")
        badge.setFixedSize(16, 16)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(badge)
        headline = QLabel(title, card)
        headline.setObjectName("obox-modal-title")
        title_row.addWidget(headline)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        body = QLabel(message, card)
        body.setObjectName("obox-modal-body")
        body.setWordWrap(True)
        layout.addWidget(body)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(10)
        layout.addLayout(self.body_layout)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch(1)
        layout.addLayout(footer)

        outer.addWidget(card)
        self._card = card
        self.footer_layout = footer

    def add_button(self, text: str, primary: bool = False) -> QPushButton:
        button = QPushButton(text, self._card)
        button.setMinimumHeight(32)
        if primary:
            button.setObjectName("obox-primary")
        self.footer_layout.addWidget(button)
        return button

    def showEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.window().frameGeometry())
        super().showEvent(event)
