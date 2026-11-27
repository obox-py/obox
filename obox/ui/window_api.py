"""window/env/commands 的宿主侧处理：模态框、新窗口、状态栏与输出面板。"""

from __future__ import annotations

from typing import Any

from obox.qt import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    Qt,
)

from ..api import window as window_api
from ..api import commands as commands_api
from ..api import env as env_api
from .app_window import AppWindow
from .output_panel import OutputPanel
from .statusbar import StatusBar, StatusBarItem


class WindowApiService:
    """把 window/commands/env 消息落到主进程 UI；返回 dict 或 None。"""

    MESSAGE_IDS = (
        window_api.WINDOW_SHOW_INFORMATION_MSG,
        window_api.WINDOW_SHOW_WARNING_MSG,
        window_api.WINDOW_SHOW_ERROR_MSG,
        window_api.WINDOW_SHOW_MESSAGE_BOX_MSG,
        window_api.WINDOW_SHOW_QUICK_PICK_MSG,
        window_api.WINDOW_SHOW_INPUT_BOX_MSG,
        window_api.WINDOW_SHOW_OPEN_DIALOG_MSG,
        window_api.WINDOW_SHOW_SAVE_DIALOG_MSG,
        window_api.WINDOW_CREATE_MSG,
        window_api.WINDOW_CLOSE_MSG,
        window_api.WINDOW_SET_TITLE_MSG,
        window_api.WINDOW_GET_ACTIVE_MSG,
        window_api.WINDOW_LIST_MSG,
        window_api.WINDOW_FOCUS_MSG,
        window_api.WINDOW_CREATE_STATUS_BAR_ITEM_MSG,
        window_api.WINDOW_UPDATE_STATUS_BAR_ITEM_MSG,
        window_api.WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG,
        window_api.WINDOW_PROGRESS_MSG,
        window_api.WINDOW_CREATE_OUTPUT_CHANNEL_MSG,
        window_api.WINDOW_ACTIVE_COLOR_THEME_MSG,
        commands_api.COMMANDS_REGISTER_MSG,
        commands_api.COMMANDS_EXECUTE_MSG,
        commands_api.COMMANDS_GET_MSG,
        env_api.ENV_INFO_MSG,
        env_api.ENV_CLIPBOARD_READ_MSG,
        env_api.ENV_CLIPBOARD_WRITE_MSG,
        env_api.ENV_OPEN_EXTERNAL_MSG,
        env_api.ENV_OPEN_PATH_MSG,
    )

    def __init__(self, app: Any) -> None:
        self._app = app
        self._windows: dict[str, AppWindow] = {}
        self._counter = 0
        self._status_items: dict[str, StatusBarItem] = {}
        self._status_bar: StatusBar | None = None
        self._outputs: dict[str, OutputPanel] = {}
        self._output_channel: str = ""

    # ---- 分发 ----
    def handle(self, message: Any) -> dict[str, Any] | None:
        handlers = {
            window_api.WINDOW_SHOW_INFORMATION_MSG: self._notice,
            window_api.WINDOW_SHOW_WARNING_MSG: self._notice,
            window_api.WINDOW_SHOW_ERROR_MSG: self._notice,
            window_api.WINDOW_SHOW_MESSAGE_BOX_MSG: self._message_box,
            window_api.WINDOW_SHOW_QUICK_PICK_MSG: self._quick_pick,
            window_api.WINDOW_SHOW_INPUT_BOX_MSG: self._input_box,
            window_api.WINDOW_SHOW_OPEN_DIALOG_MSG: self._open_dialog,
            window_api.WINDOW_SHOW_SAVE_DIALOG_MSG: self._save_dialog,
            window_api.WINDOW_CREATE_MSG: self._create_window,
            window_api.WINDOW_CLOSE_MSG: self._close_window,
            window_api.WINDOW_SET_TITLE_MSG: self._set_title,
            window_api.WINDOW_GET_ACTIVE_MSG: self._get_active,
            window_api.WINDOW_LIST_MSG: self._list_windows,
            window_api.WINDOW_FOCUS_MSG: self._focus_window,
            window_api.WINDOW_CREATE_STATUS_BAR_ITEM_MSG: self._create_status_item,
            window_api.WINDOW_UPDATE_STATUS_BAR_ITEM_MSG: self._update_status_item,
            window_api.WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG: self._dispose_status_item,
            window_api.WINDOW_PROGRESS_MSG: self._progress,
            window_api.WINDOW_CREATE_OUTPUT_CHANNEL_MSG: self._create_output,
            window_api.WINDOW_ACTIVE_COLOR_THEME_MSG: self._active_theme,
            env_api.ENV_INFO_MSG: self._env_info,
            env_api.ENV_CLIPBOARD_READ_MSG: self._clipboard_read,
            env_api.ENV_CLIPBOARD_WRITE_MSG: self._clipboard_write,
            env_api.ENV_OPEN_EXTERNAL_MSG: self._open_external,
            env_api.ENV_OPEN_PATH_MSG: self._open_path,
        }
        handler = handlers.get(message.msg_id)
        if handler is None:
            return None
        return handler(message, message.payload or {})

    # ---- window ----
    def _parent(self, payload: dict[str, Any]) -> Any:
        window_id = str(payload.get("window_id") or payload.get("windowId") or "")
        return self._windows.get(window_id) or self._app.window

    def _translate(self, message: Any, value: Any) -> str:
        """扩展传进来的文案按它的命名空间替换 i18n 占位符。"""
        text = str(value or "")
        if not text:
            return ""
        owner = str(getattr(message, "src", "") or "")
        return self._app.i18n.translate(text, owner) if owner else text

    def _notice(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        kind = str(payload.get("type") or "info")
        box = QMessageBox(self._parent(payload))
        box.setWindowModality(Qt.WindowModality.WindowModal)
        box.setIcon(
            {
                "warning": QMessageBox.Icon.Warning,
                "error": QMessageBox.Icon.Critical,
                "question": QMessageBox.Icon.Question,
            }.get(kind, QMessageBox.Icon.Information)
        )
        box.setText(self._translate(message, payload.get("message")))
        items = [self._translate(message, item) for item in payload.get("items") or []]
        buttons = {}
        for item in items:
            buttons[box.addButton(item, QMessageBox.ButtonRole.AcceptRole)] = item
        box.addButton(
            self._app._t("dialog.ok" if not items else "dialog.close"),
            QMessageBox.ButtonRole.RejectRole,
        )
        box.exec()
        clicked = box.clickedButton()
        return {"item": buttons.get(clicked) if clicked is not None else None}

    def _message_box(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        options = dict(payload.get("options") or {})
        box = QMessageBox(self._parent(payload))
        box.setWindowModality(Qt.WindowModality.WindowModal)
        box.setWindowTitle(self._translate(message, options.get("title")))
        box.setText(self._translate(message, options.get("message")))
        if options.get("detail"):
            box.setDetailedText(self._translate(message, options["detail"]))
        box.setIcon(
            {
                "warning": QMessageBox.Icon.Warning,
                "error": QMessageBox.Icon.Critical,
                "question": QMessageBox.Icon.Question,
            }.get(str(options.get("type") or "info"), QMessageBox.Icon.Information)
        )
        button_list = [self._translate(message, item) for item in options.get("buttons") or ["确定"]]
        buttons = []
        for index, label in enumerate(button_list):
            role = QMessageBox.ButtonRole.AcceptRole
            if index == options.get("cancelId"):
                role = QMessageBox.ButtonRole.RejectRole
            buttons.append(box.addButton(label, role))
        if options.get("checkboxLabel"):
            box.setCheckBox(QCheckBox(self._translate(message, options["checkboxLabel"]), box))
        box.exec()
        clicked = box.clickedButton()
        response = buttons.index(clicked) if clicked in buttons else -1
        checked = bool(box.checkBox().isChecked()) if box.checkBox() is not None else False
        return {"response": response, "checkboxChecked": checked}

    def _quick_pick(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        items = payload.get("items") or []
        options = dict(payload.get("options") or {})
        dialog = QDialog(self._parent(payload))
        dialog.setWindowTitle(str(options.get("title") or "选择"))
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout(dialog)
        listing = QListWidget(dialog)
        listing.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
            if options.get("canPickMany")
            else QListWidget.SelectionMode.SingleSelection
        )
        for raw in items:
            item = raw if isinstance(raw, dict) else {"label": str(raw)}
            entry = QListWidgetItem(str(item.get("label") or ""))
            entry.setData(Qt.ItemDataRole.UserRole, item)
            listing.addItem(entry)
        layout.addWidget(listing)
        confirm = QPushButton("确定", dialog)
        confirm.clicked.connect(dialog.accept)
        layout.addWidget(confirm)
        if not dialog.exec():
            return {"items": [], "item": None}
        chosen = [entry.data(Qt.ItemDataRole.UserRole) for entry in listing.selectedItems()]
        if options.get("canPickMany"):
            return {"items": chosen}
        return {"items": chosen, "item": chosen[0] if chosen else None}

    def _input_box(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        options = dict(payload.get("options") or {})
        text, ok = QInputDialog.getText(
            self._parent(payload),
            str(options.get("title") or "输入"),
            str(options.get("prompt") or options.get("placeHolder") or ""),
            QLineEdit.EchoMode.Password if options.get("password") else QLineEdit.EchoMode.Normal,
            str(options.get("value") or ""),
        )
        return {"value": text if ok else None}

    def _open_dialog(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        options = dict(payload.get("options") or {})
        root = str(options.get("defaultUri") or "")
        if options.get("canSelectFolders") and not options.get("canSelectFiles"):
            path = QFileDialog.getExistingDirectory(self._parent(payload), str(options.get("title") or ""), root)
            return {"uris": [path] if path else []}
        paths, _filter = QFileDialog.getOpenFileNames(
            self._parent(payload), str(options.get("title") or ""), root
        )
        return {"uris": paths}

    def _save_dialog(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        options = dict(payload.get("options") or {})
        path, _filter = QFileDialog.getSaveFileName(
            self._parent(payload),
            str(options.get("title") or ""),
            str(options.get("defaultUri") or ""),
        )
        return {"uri": path or None}

    def _create_window(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        options = dict(payload.get("options") or {})
        title = str(options.get("title") or "窗口")
        self._counter += 1
        window_id = str(options.get("singleton") or f"ext-{message.src}-{self._counter}")
        existing = self._windows.get(window_id)
        if existing is not None:
            existing.show()
            existing.raise_()
            return {"windowId": window_id, "reused": True}
        window = AppWindow(title)
        parent_id = str(options.get("parent") or "")
        parent = self._windows.get(parent_id) or self._app.window
        window.setParent(parent if options.get("modal") else None)
        window.setWindowModality(
            Qt.WindowModality.WindowModal if options.get("modal") else Qt.WindowModality.NonModal
        )
        width = int(options.get("width") or 720)
        height = int(options.get("height") or 520)
        window.resize(width, height)
        source = str(options.get("oml") or options.get("html") or "")
        if source:
            try:
                root, _ids = self._app.assemble_view(str(message.src), source)
                window.set_content(root)
            except Exception as exc:
                window.show_message(str(exc))
        window.show()
        self._windows[window_id] = window
        window.destroyed.connect(lambda *_: self._windows.pop(window_id, None))
        return {"windowId": window_id}

    def _close_window(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        window = self._windows.pop(str(payload.get("windowId") or ""), None)
        if window is not None:
            window.force_close()
            return {"closed": True}
        return {"closed": False}

    def _set_title(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        window = self._windows.get(str(payload.get("windowId") or ""))
        if window is not None:
            window.setWindowTitle(str(payload.get("title") or ""))
            return {"ok": True}
        return {"ok": False}

    def _get_active(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        for window_id, window in self._windows.items():
            if window.isActiveWindow():
                return {"windowId": window_id}
        return {"windowId": None}

    def _list_windows(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        return {"windowIds": list(self._windows)}

    def _focus_window(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        window = self._windows.get(str(payload.get("windowId") or ""))
        if window is not None:
            window.show()
            window.raise_()
            window.activateWindow()
            return {"ok": True}
        return {"ok": False}

    # ---- status bar / output ----
    def _ensure_status_bar(self) -> StatusBar:
        if self._status_bar is None:
            self._status_bar = StatusBar(self._app.window)
            self._app.window.attach_status_bar(self._status_bar)
        return self._status_bar

    def _create_status_item(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        bar = self._ensure_status_bar()
        item = bar.create_item(
            str(message.src),
            alignment=str(payload.get("alignment") or "left"),
            priority=int(payload.get("priority") or 0),
        )
        item_id = f"{message.src}-{id(item)}"
        self._status_items[item_id] = item
        return {"itemId": item_id}

    def _update_status_item(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        item = self._status_items.get(str(payload.get("itemId") or ""))
        if item is None:
            return {"ok": False}
        if "text" in payload:
            item.set_text(str(payload["text"]))
        if "tooltip" in payload:
            item.set_tooltip(str(payload["tooltip"]))
        if "command" in payload:
            item.set_command(str(payload["command"]))
        if payload.get("show") is not None:
            item.setVisible(bool(payload["show"]))
        return {"ok": True}

    def _dispose_status_item(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        item = self._status_items.pop(str(payload.get("itemId") or ""), None)
        if item is not None:
            item.deleteLater()
        return {"ok": item is not None}

    def _progress(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        options = dict(payload.get("options") or {})
        dialog = QProgressDialog(str(options.get("title") or "处理中"), None, 0, 0, self._app.window)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setCancelButton(None if not payload.get("cancellable") else dialog.findChild(QPushButton))
        dialog.show()
        self._app._progress_dialog = dialog
        return {"started": True}

    def _create_output(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name") or "输出")
        panel = self._outputs.get(name)
        if panel is None:
            panel = OutputPanel(self._app.window)
            self._app.window.attach_output_panel(panel)
            self._outputs[name] = panel
        return {"channel": name}

    def theme_payload(self) -> dict[str, Any]:
        provider = getattr(self._app, "provider", None)
        palette = getattr(provider, "palette", None)
        colors = {
            name: getattr(palette, name)
            for name in dir(palette)
            if name.isupper() and isinstance(getattr(palette, name), str)
        } if palette is not None else {}
        return {
            "kind": getattr(self._app, "theme_name", "light"),
            "name": getattr(provider, "name", getattr(self._app, "theme_name", "light")),
            "colors": colors,
        }

    def broadcast_theme(self) -> None:
        from ..api.message import Message

        try:
            self._app.bus.send(
                Message(
                    src="obox",
                    dst="",
                    msg_id=window_api.WINDOW_COLOR_THEME_CHANGED_MSG,
                    payload={"theme": self.theme_payload()},
                )
            )
        except Exception:
            pass

    def _active_theme(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        return self.theme_payload()

    # ---- env ----
    def _env_info(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        from .. import __version__

        return {
            "appName": "obox",
            "appVersion": __version__,
            "language": self._app.i18n.language,
            "appHost": "desktop",
            "platform": "win32",
            "arch": "arm64" if "ARM64" in __import__("platform").machine().upper() else "x86_64",
        }

    def _clipboard_read(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        from obox.qt import QApplication

        return {"text": QApplication.clipboard().text()}

    def _clipboard_write(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        from obox.qt import QApplication

        QApplication.clipboard().setText(str(payload.get("text") or ""))
        return {"ok": True}

    def _open_external(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        from obox.qt import QDesktopServices, QUrl

        return {"ok": QDesktopServices.openUrl(QUrl(str(payload.get("uri") or "")))}

    def _open_path(self, message: Any, payload: dict[str, Any]) -> dict[str, Any]:
        from obox.qt import QDesktopServices, QUrl

        return {"ok": QDesktopServices.openUrl(QUrl.fromLocalFile(str(payload.get("path") or "")))}