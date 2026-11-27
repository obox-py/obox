"""关闭询问对话框：最小化到托盘 / 退出 / 取消 + 记住选择。"""

from __future__ import annotations

from typing import Callable

from obox.qt import QCheckBox

from .modal_dialog import ModalPanelDialog

_DEFAULTS = {
    "close.title": "关闭 obox",
    "close.message": "关闭 obox 时你希望：",
    "close.remember": "记住我的选择（可在设置 → 行为中修改）",
    "close.tray": "最小化到托盘",
    "close.quit": "退出",
    "close.cancel": "取消",
}


class CloseDialog(ModalPanelDialog):
    def __init__(self, parent=None, translator: Callable[[str], str] | None = None) -> None:
        def label(key: str) -> str:
            text = translator(key) if translator else ""
            if not text or text.startswith("{{"):
                return _DEFAULTS.get(key, key)
            return text

        super().__init__(parent, title=label("close.title"), message=label("close.message"))
        self.choice: str | None = None
        self.remember = False

        self.remember_box = QCheckBox(label("close.remember"), self._card)
        self.remember_box.setObjectName("obox-remember")
        self.body_layout.addWidget(self.remember_box)

        self.add_button(label("close.tray"), primary=True).clicked.connect(
            lambda _checked=False: self._choose("tray")
        )
        self.add_button(label("close.quit")).clicked.connect(lambda _checked=False: self._choose("quit"))
        self.add_button(label("close.cancel")).clicked.connect(lambda _checked=False: self._choose("cancel"))

    def _choose(self, choice: str) -> None:
        self.choice = choice
        self.remember = self.remember_box.isChecked()
        self.accept() if choice != "cancel" else self.reject()
