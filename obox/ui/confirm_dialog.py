"""通用确认框：卸载等不可逆操作用它二次确认。"""

from __future__ import annotations

from .modal_dialog import ModalPanelDialog


class ConfirmDialog(ModalPanelDialog):
    def __init__(self, title: str, message: str, parent=None, confirm_text: str = "确认") -> None:
        super().__init__(parent, title=title, message=message, glyph="!")
        self.add_button("取消").clicked.connect(self.reject)
        self.add_button(confirm_text, primary=True).clicked.connect(self.accept)
