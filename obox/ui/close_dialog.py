"""关闭询问对话框：最小化到托盘 / 退出 / 取消 + 记住选择。"""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox

from .modal_dialog import ModalPanelDialog


class CloseDialog(ModalPanelDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, title="关闭 obox", message="关闭 obox 时你希望：")
        self.choice: str | None = None
        self.remember = False

        self.remember_box = QCheckBox("记住我的选择（可在设置 → 行为中修改）", self._card)
        self.remember_box.setObjectName("obox-remember")
        self.body_layout.addWidget(self.remember_box)

        self.add_button("最小化到托盘", primary=True).clicked.connect(
            lambda _checked=False: self._choose("tray")
        )
        self.add_button("退出").clicked.connect(lambda _checked=False: self._choose("quit"))
        self.add_button("取消").clicked.connect(lambda _checked=False: self._choose("cancel"))

    def _choose(self, choice: str) -> None:
        self.choice = choice
        self.remember = self.remember_box.isChecked()
        self.accept() if choice != "cancel" else self.reject()
