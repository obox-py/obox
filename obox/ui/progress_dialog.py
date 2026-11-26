"""安装进度浮层：不可关闭，安装完成后由调用方关闭。"""

from __future__ import annotations

from obox.qt import Qt

from .modal_dialog import ModalPanelDialog


class InstallProgressDialog(ModalPanelDialog):
    def __init__(self, title: str, message: str, parent=None) -> None:
        super().__init__(parent, title=title, message=message, glyph="i")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        event.ignore()
