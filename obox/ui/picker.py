"""文件与目录选择器：Windows 11 资源管理器风格的本地与 SSH 浏览。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from obox.qt import QPointF, QRectF, QSize, Qt
from obox.qt import QAction, QColor, QIcon, QPainter, QPixmap
from obox.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import palette
from .picker_remote import ListWorker, RemoteBrowser


_RECENT_PATHS: list[str] = []


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def _human_time(stamp: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(stamp)) if stamp else ""


def _entry_icon(is_dir: bool) -> QIcon:
    """自绘文件夹/文件图标，避免 emoji 在不同字体下忽大忽小。"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(2.0)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    if is_dir:
        painter.setBrush(QColor("#F5B942"))
        painter.drawRoundedRect(QRectF(3, 8, 10, 4), 1, 1)
        painter.drawRoundedRect(QRectF(3, 9.5, 10, 7), 1.5, 1.5)
        painter.setBrush(QColor("#FFD66B"))
        painter.drawRoundedRect(QRectF(3.6, 10.4, 8.8, 5.4), 1, 1)
    else:
        painter.setBrush(QColor("#DDE3EC"))
        painter.drawRoundedRect(QRectF(5, 4, 6, 9), 1.2, 1.2)
        painter.setBrush(QColor("#B7C0CE"))
        painter.drawPolygon([QPointF(11, 4), QPointF(11, 7.5), QPointF(8.5, 4)])
    painter.end()
    return QIcon(pixmap)


class PickerDialog(QDialog):
    """选择器：父窗口决定模态范围，异步列举目录。"""

    def __init__(self, params: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.params = params
        self.mode = params["mode"]
        self.multi = bool(params["multi"])
        self.extensions = list(params["extensions"])
        self._all_extensions = list(self.extensions)
        self.trusted: set[str] = set()
        self.browser: RemoteBrowser | None = None
        self.worker: ListWorker | None = None
        self.current_path = ""
        self.entries: list[dict[str, Any]] = []
        self.paths: list[Any] = []
        self.error = ""
        self._history: list[str] = []
        self._index = -1
        self._pending_select = ""
        self._ssh_home = ""
        self.show_hidden = True
        self._keyword = ""
        self.setWindowTitle(params["title"] or "选择")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(980, 640)
        self._build()
        self._browse(params.get("start_path") or "")

    def _build(self) -> None:
        self.setObjectName("obox-picker")
        self.setStyleSheet(self._stylesheet())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)

        nav = QHBoxLayout()
        nav.setSpacing(4)
        for text, slot in (("←", self._go_back), ("→", self._go_forward), ("↑", self._up)):
            button = QPushButton(text)
            button.setObjectName("picker-nav")
            button.setFixedSize(30, 30)
            button.clicked.connect(slot)
            nav.addWidget(button)
        self.path_edit = QLineEdit()
        self.path_edit.setObjectName("picker-edit")
        self.path_edit.setMinimumHeight(32)
        self.path_edit.returnPressed.connect(self._on_path_enter)
        nav.addWidget(self.path_edit, 1)
        self.history_button = QPushButton("v")
        self.history_button.setObjectName("picker-nav")
        self.history_button.setFixedSize(22, 30)
        self.history_button.clicked.connect(self._show_history)
        nav.addWidget(self.history_button)
        refresh = QPushButton("↻")
        refresh.setObjectName("picker-nav")
        refresh.setFixedSize(30, 30)
        refresh.clicked.connect(lambda: self._browse(self.current_path, record=False))
        nav.addWidget(refresh)
        self.search = QLineEdit()
        self.search.setObjectName("picker-edit")
        self.search.setPlaceholderText("搜索")
        self.search.setFixedWidth(220)
        self.search.setMinimumHeight(32)
        self.search.textChanged.connect(self._apply_filter)
        nav.addWidget(self.search)
        layout.addLayout(nav)

        tools_row = QHBoxLayout()
        tools_row.setSpacing(8)
        self.new_folder = QPushButton("新建文件夹")
        self.new_folder.setObjectName("picker-link")
        self.new_folder.clicked.connect(self._new_folder)
        self.new_folder.setVisible(not self.params.get("ssh"))
        tools_row.addWidget(self.new_folder)
        if self.params.get("ssh"):
            self.upload_button = QPushButton("上传…")
            self.upload_button.setObjectName("picker-link")
            self.upload_button.clicked.connect(self._upload)
            tools_row.addWidget(self.upload_button)
            self.download_button = QPushButton("下载…")
            self.download_button.setObjectName("picker-link")
            self.download_button.clicked.connect(self._download)
            tools_row.addWidget(self.download_button)
        self.hidden_box = QCheckBox("显示隐藏文件")
        self.hidden_box.setChecked(True)
        self.hidden_box.toggled.connect(self._toggle_hidden)
        tools_row.addWidget(self.hidden_box)
        tools_row.addStretch(1)
        layout.addLayout(tools_row)

        body = QHBoxLayout()
        body.setSpacing(10)
        side_card = QFrame()
        side_card.setObjectName("picker-card")
        side_layout = QVBoxLayout(side_card)
        side_layout.setContentsMargins(4, 8, 4, 8)
        self.side = QListWidget()
        self.side.setObjectName("picker-side")
        self.side.itemClicked.connect(self._on_side_clicked)
        side_layout.addWidget(self.side)
        side_card.setFixedWidth(200)
        body.addWidget(side_card)

        list_card = QFrame()
        list_card.setObjectName("picker-card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(1, 1, 1, 1)
        self.tree = QTreeWidget()
        self.tree.setObjectName("picker-tree")
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["名称", "修改日期", "类型", "大小"])
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.setSelectionMode(
            QTreeWidget.SelectionMode.ExtendedSelection
            if self.multi
            else QTreeWidget.SelectionMode.SingleSelection
        )
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        list_layout.addWidget(self.tree)
        body.addWidget(list_card, 1)
        layout.addLayout(body, 1)

        bar = QFrame()
        bar.setObjectName("picker-footer")
        bottom = QHBoxLayout(bar)
        bottom.setContentsMargins(0, 10, 0, 0)
        bottom.setSpacing(8)
        self.name_label = QLabel("文件夹名:" if self.mode == "dir" else "文件名:")
        self.name_label.setObjectName("picker-label")
        bottom.addWidget(self.name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("picker-edit")
        self.name_edit.setMinimumHeight(32)
        bottom.addWidget(self.name_edit, 1)
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("picker-combo")
        self.type_combo.setMinimumHeight(32)
        self.type_combo.setFixedWidth(200)
        self.type_combo.addItem("所有文件 (*.*)")
        for ext in self._all_extensions:
            self.type_combo.addItem(f".{ext} (*.{ext})")
        self.type_combo.blockSignals(True)
        self.type_combo.setCurrentIndex(1 if self._all_extensions else 0)
        self.type_combo.blockSignals(False)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        bottom.addWidget(self.type_combo)
        cancel = QPushButton("取消")
        cancel.setObjectName("picker-button")
        cancel.setMinimumSize(88, 32)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("打开" if self.mode == "file" else "选择文件夹")
        ok.setObjectName("picker-primary")
        ok.setMinimumSize(96, 32)
        ok.setDefault(True)
        ok.clicked.connect(self._accept)
        bottom.addWidget(cancel)
        bottom.addWidget(ok)
        layout.addWidget(bar)

        self.status = QLabel("")
        self.status.setObjectName("picker-status")
        layout.addWidget(self.status)
        self._fill_sidebar()

    def _stylesheet(self) -> str:
        return f"""
        QDialog#obox-picker {{ background: {palette.BACKGROUND}; }}
        QFrame#picker-card {{ background: {palette.SURFACE}; border: 1px solid {palette.LINE}; border-radius: 6px; }}
        QFrame#picker-footer {{ border-top: 1px solid {palette.LINE}; }}
        QPushButton#picker-nav {{ background: transparent; border: none; border-radius: 4px; color: {palette.TEXT}; font-size: 15px; }}
        QPushButton#picker-nav:hover {{ background: {palette.SURFACE_MUTED}; }}
        QPushButton#picker-link {{ background: transparent; border: none; color: {palette.ACCENT}; padding: 4px 6px; }}
        QPushButton#picker-link:hover {{ background: {palette.ACCENT_SOFT}; border-radius: 4px; }}
        QLineEdit#picker-edit, QComboBox#picker-combo {{ background: {palette.SURFACE}; border: 1px solid {palette.INPUT_BORDER};
            border-radius: 4px; padding: 0 10px; color: {palette.TEXT}; selection-background-color: {palette.ACCENT}; }}
        QLineEdit#picker-edit:focus, QComboBox#picker-combo:focus {{ border: 1px solid {palette.ACCENT}; }}
        QListWidget#picker-side {{ background: transparent; border: none; outline: none; }}
        QListWidget#picker-side::item {{ height: 32px; border-radius: 4px; padding-left: 8px; color: {palette.TEXT}; }}
        QListWidget#picker-side::item:hover {{ background: {palette.SURFACE_MUTED}; }}
        QListWidget#picker-side::item:selected {{ background: {palette.ACCENT_SOFT}; color: {palette.ACCENT}; }}
        QTreeWidget#picker-tree {{ background: transparent; border: none; outline: none; }}
        QTreeWidget#picker-tree::item {{ height: 32px; color: {palette.TEXT}; }}
        QTreeWidget#picker-tree::item:hover {{ background: {palette.SURFACE_MUTED}; }}
        QTreeWidget#picker-tree::item:selected {{ background: {palette.ACCENT_SOFT}; color: {palette.TEXT}; }}
        QHeaderView::section {{ background: transparent; border: none; border-bottom: 1px solid {palette.LINE};
            color: {palette.TEXT_MUTED}; font-size: 12px; padding: 6px 8px; }}
        QPushButton#picker-button {{ background: {palette.SURFACE}; border: 1px solid {palette.INPUT_BORDER};
            border-radius: 4px; color: {palette.TEXT}; }}
        QPushButton#picker-button:hover {{ background: {palette.SURFACE_MUTED}; }}
        QPushButton#picker-primary {{ background: {palette.ACCENT}; border: none; border-radius: 4px;
            color: {palette.ACCENT_TEXT}; font-weight: 500; }}
        QPushButton#picker-primary:hover {{ background: {palette.ACCENT}; }}
        QLabel#picker-label, QLabel#picker-status {{ color: {palette.TEXT_MUTED}; font-size: 12px; }}
        """

    def _section(self, title: str) -> None:
        item = QListWidgetItem(title)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setSizeHint(QSize(0, 26))
        self.side.addItem(item)

    def _nav_item(self, name: str, path: str) -> None:
        item = QListWidgetItem("  " + name)
        item.setData(Qt.ItemDataRole.UserRole, path)
        self.side.addItem(item)

    def _fill_sidebar(self) -> None:
        self.side.clear()
        if self.params.get("ssh"):
            ssh = self.params["ssh"]
            self._section(f"{ssh.get('user') or ''}@{ssh.get('host')}")
            self._nav_item("主目录", self._ssh_home or self.params.get("start_path") or "/")
            self._nav_item("根目录", "/")
            self._section("常用目录")
            for path in ("/tmp", "/etc", "/home", "/var/log", "/opt"):
                self._nav_item(path, path)
            return
        home = Path.home()
        self._section("快速访问")
        self._nav_item("主文件夹", str(home))
        for name, folder in (
            ("桌面", home / "Desktop"),
            ("下载", home / "Downloads"),
            ("文档", home / "Documents"),
            ("图片", home / "Pictures"),
            ("音乐", home / "Music"),
            ("视频", home / "Videos"),
        ):
            if folder.is_dir():
                self._nav_item(name, str(folder))
        self._section("此电脑")
        self._nav_item("本地磁盘 (C:)", "C:/")

    def _show_history(self) -> None:
        from obox.qt import QMenu

        menu = QMenu(self)
        menu.setObjectName("picker-history")
        for path in _RECENT_PATHS[:15]:
            action = QAction(path, menu)
            action.triggered.connect(lambda _checked=False, target=path: self._go_history(target))
            menu.addAction(action)
        if not _RECENT_PATHS:
            menu.addAction("暂无历史")
        menu.exec(self.history_button.mapToGlobal(self.history_button.rect().bottomLeft()))

    def _go_history(self, path: str) -> None:
        self.path_edit.setText(path)
        self._on_path_enter()

    def _upload(self) -> None:
        files, _filter = QFileDialog.getOpenFileNames(self, "上传到远端")
        if not files:
            return
        if self.browser is None:
            self.browser = RemoteBrowser(self.params["ssh"], self.trusted)
        try:
            for local in files:
                name = Path(local).name
                target = self.current_path.rstrip("/") + "/" + name
                self.browser.upload(local, target)
        except Exception as exc:
            self.status.setText(f"上传失败：{exc}")
            return
        self.status.setText(f"已上传 {len(files)} 个文件")
        self._browse(self.current_path, record=False)

    def _download(self) -> None:
        selected = [
            item.data(0, Qt.ItemDataRole.UserRole)
            for item in self.tree.selectedItems()
            if item.data(0, Qt.ItemDataRole.UserRole)
            and not item.data(0, Qt.ItemDataRole.UserRole).get("is_dir")
        ]
        if not selected:
            self.status.setText("请先选中要下载的文件")
            return
        target_dir = QFileDialog.getExistingDirectory(self, "下载到本地")
        if not target_dir:
            return
        if self.browser is None:
            self.browser = RemoteBrowser(self.params["ssh"], self.trusted)
        try:
            for entry in selected:
                self.browser.download(entry["path"], str(Path(target_dir) / entry["name"]))
        except Exception as exc:
            self.status.setText(f"下载失败：{exc}")
            return
        self.status.setText(f"已下载 {len(selected)} 个文件到 {target_dir}")

    def _on_path_enter(self) -> None:
        """路径栏支持手输：目录直接进入，文件则进入父目录并选中。"""
        text = self.path_edit.text().strip()
        if not text:
            return
        if self.params.get("ssh"):
            self._browse(text)
            return
        target = Path(text).expanduser()
        if target.is_file():
            self._pending_select = target.name
            self._browse(str(target.parent))
            return
        if target.is_dir():
            self._browse(str(target))
            return
        self.status.setText(f"路径不存在：{text}")

    def _browse(self, path: str, record: bool = True) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        self.status.setText("正在读取…")
        self.tree.clear()
        self.worker = ListWorker(self.params, path, self.browser, self)
        self.worker.done.connect(lambda payload, error: self._on_loaded(payload, error, record))
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_loaded(self, payload: dict[str, Any], _error: str, record: bool) -> None:
        self.current_path = payload["path"]
        self.entries = payload["entries"]
        self.path_edit.setText(self.current_path)
        if self.params.get("ssh") and not self._ssh_home and payload.get("home"):
            self._ssh_home = str(payload["home"])
            self._fill_sidebar()
        self._render()
        if self._pending_select:
            target = self._pending_select
            self._pending_select = ""
            for index in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(index)
                if item.text(0) == target:
                    item.setSelected(True)
                    self.tree.scrollToItem(item)
                    break
        where = "远端" if self.params.get("ssh") else "本地"
        self.status.setText(f"{where} · {len(self.entries)} 项")
        if self.current_path and self.current_path not in _RECENT_PATHS:
            _RECENT_PATHS.insert(0, self.current_path)
            del _RECENT_PATHS[20:]
        elif self.current_path in _RECENT_PATHS:
            _RECENT_PATHS.remove(self.current_path)
            _RECENT_PATHS.insert(0, self.current_path)
        if record:
            self._history = self._history[: self._index + 1]
            self._history.append(self.current_path)
            self._index = len(self._history) - 1

    def _on_failed(self, kind: str, detail: str) -> None:
        self.error = detail
        self.status.setText(f"读取失败：{detail}")

    def _on_side_clicked(self, item: QListWidgetItem) -> None:
        target = item.data(Qt.ItemDataRole.UserRole)
        if not target:
            return
        self._browse("" if target == "SSH" else str(target))

    def _go_back(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._browse(self._history[self._index], record=False)

    def _go_forward(self) -> None:
        if self._index + 1 < len(self._history):
            self._index += 1
            self._browse(self._history[self._index], record=False)

    def _up(self) -> None:
        if not self.current_path:
            return
        if self.params.get("ssh"):
            parent = self.current_path.rstrip("/").rsplit("/", 1)[0] or "/"
        else:
            parent = str(Path(self.current_path).parent)
        self._browse(parent)

    def _parent_path(self) -> str:
        if not self.current_path:
            return ""
        if self.params.get("ssh"):
            current = self.current_path.rstrip("/") or "/"
            if current == "/":
                return ""
            return current.rsplit("/", 1)[0] or "/"
        current = Path(self.current_path)
        parent = current.parent
        return "" if parent == current else str(parent)

    def _render(self) -> None:
        keyword = self._keyword.strip().lower()
        visible = [
            entry
            for entry in self.entries
            if (self.show_hidden or not entry.get("hidden"))
            and (not keyword or keyword in entry["name"].lower())
        ]
        self.tree.clear()
        self._populate(visible)

    def _toggle_hidden(self, checked: bool) -> None:
        self.show_hidden = bool(checked)
        self._render()

    def _populate(self, entries: list[dict[str, Any]]) -> None:
        parent = self._parent_path()
        if parent:
            up = QTreeWidgetItem(["..", "", "文件夹", ""])
            up.setIcon(0, _entry_icon(True))
            up.setData(0, Qt.ItemDataRole.UserRole, {"name": "..", "path": parent, "is_dir": True, "parent": True, "size": 0, "mtime": 0})
            self.tree.addTopLevelItem(up)
        for entry in entries:
            item = QTreeWidgetItem(
                [
                    entry["name"],
                    _human_time(entry["mtime"]),
                    "文件夹" if entry["is_dir"] else (entry["name"].rsplit(".", 1)[-1].upper() if "." in entry["name"] else "文件"),
                    "" if entry["is_dir"] else _human_size(entry["size"]),
                ]
            )
            item.setIcon(0, _entry_icon(entry["is_dir"]))
            item.setData(0, Qt.ItemDataRole.UserRole, entry)
            self.tree.addTopLevelItem(item)
        self.tree.setColumnWidth(0, 360)
        self.tree.setColumnWidth(1, 180)
        self.tree.setColumnWidth(2, 120)

    def _apply_filter(self, text: str) -> None:
        self._keyword = text
        self._render()

    def _on_type_changed(self, index: int) -> None:
        self.extensions = [] if index == 0 else [self._all_extensions[index - 1]]
        self.params["extensions"] = self.extensions
        self._browse(self.current_path, record=False)

    def _on_double_click(self, item: QTreeWidgetItem, _column: int) -> None:
        entry = item.data(0, Qt.ItemDataRole.UserRole)
        if entry and entry["is_dir"]:
            self._browse(entry["path"])
        elif not self.multi and self.mode == "file":
            self._accept()

    def _new_folder(self) -> None:
        if self.params.get("ssh"):
            self.status.setText("远端暂不支持新建文件夹")
            return
        target = Path(self.current_path) / "新建文件夹"
        suffix = 1
        while target.exists():
            suffix += 1
            target = Path(self.current_path) / f"新建文件夹 ({suffix})"
        try:
            target.mkdir()
        except OSError as exc:
            self.status.setText(f"新建失败：{exc}")
            return
        self._browse(self.current_path, record=False)

    def _accept(self) -> None:
        typed = self.name_edit.text().strip()
        selected = [
            item.data(0, Qt.ItemDataRole.UserRole)
            for item in self.tree.selectedItems()
            if item.data(0, Qt.ItemDataRole.UserRole)
            and not item.data(0, Qt.ItemDataRole.UserRole).get("parent")
        ]
        if typed:
            self.paths = [self._typed_result(typed)]
            self.accept()
            return
        if not selected and self.mode == "dir" and self.current_path:
            selected = [{"path": self.current_path, "name": Path(self.current_path).name, "is_dir": True}]
        if not selected:
            self.status.setText("请选择一项")
            return
        self.paths = [self._result_of(entry) for entry in selected]
        self.accept()

    def _typed_result(self, typed: str) -> Any:
        if self.params.get("ssh"):
            path = typed if typed.startswith("/") else self.current_path.rstrip("/") + "/" + typed
            ssh = self.params["ssh"]
            return {"path": path, "host": ssh["host"], "user": ssh.get("user", "")}
        path = Path(typed)
        if not path.is_absolute():
            path = Path(self.current_path) / typed
        return str(path)

    def _result_of(self, entry: dict[str, Any]) -> Any:
        if self.params.get("ssh"):
            ssh = self.params["ssh"]
            return {"path": entry["path"], "host": ssh["host"], "user": ssh.get("user", "")}
        return entry["path"]

    def selected_paths(self) -> list[Any]:
        return list(self.paths)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 接口
        if self.browser is not None:
            self.browser.close()
        super().closeEvent(event)