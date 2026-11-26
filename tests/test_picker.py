"""选择器：参数校验、本地枚举与对话框基本行为。"""

from __future__ import annotations

from pathlib import Path

from obox.api.picker import normalize_extensions, validate_open
from obox.ui.picker import PickerDialog
from obox.ui.picker_remote import local_entries


def test_normalize_extensions() -> None:
    assert normalize_extensions(["TXT", ".Md", "txt"]) == ["txt", "md"]


def test_validate_open_modes() -> None:
    params, error = validate_open({"mode": "dir"})
    assert error == "" and params["mode"] == "dir"
    params, error = validate_open({"mode": "file", "extensions": [".txt"]})
    assert params["extensions"] == ["txt"]
    _params, error = validate_open({"mode": "bad"})
    assert "mode" in error
    _params, error = validate_open({"ssh": {"port": 22}})
    assert "host" in error


def test_local_entries_filter(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "b.md").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    names = [item["name"] for item in local_entries(tmp_path, ["txt"], "file")]
    assert names == ["sub", "a.txt"]
    dirs = [item["name"] for item in local_entries(tmp_path, [], "dir")]
    assert dirs == ["sub"]


def test_dialog_is_window_modal_and_returns_path(qapp, tmp_path: Path) -> None:
    (tmp_path / "picked.txt").write_text("x", encoding="utf-8")
    dialog = PickerDialog({"mode": "file", "extensions": ["txt"], "multi": False, "title": "t", "start_path": str(tmp_path), "window_id": "", "ssh": None}, None)
    from PySide6.QtCore import Qt

    assert dialog.windowModality() == Qt.WindowModality.WindowModal
    for _ in range(200):
        qapp.processEvents()
        if dialog.tree.topLevelItemCount():
            break
    assert dialog.tree.topLevelItemCount() == 2
    picked = next(
        dialog.tree.topLevelItem(i) for i in range(dialog.tree.topLevelItemCount()) if dialog.tree.topLevelItem(i).text(0) == "picked.txt"
    )
    picked.setSelected(True)
    dialog._accept()
    assert dialog.selected_paths() == [str(tmp_path / "picked.txt")]
    dialog.deleteLater()

def test_path_bar_accepts_typed_directory_and_file(qapp, tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    target = tmp_path / "note.txt"
    target.write_text("x", encoding="utf-8")
    params = {"mode": "file", "extensions": [], "multi": False, "title": "t", "start_path": str(tmp_path), "window_id": "", "ssh": None}
    dialog = PickerDialog(params, None)

    def _pump_until(predicate, limit: int = 300) -> bool:
        for _ in range(limit):
            qapp.processEvents()
            if predicate():
                return True
        return False

    assert _pump_until(lambda: dialog.tree.topLevelItemCount() > 0)
    dialog.path_edit.setText(str(sub))
    dialog._on_path_enter()
    assert _pump_until(lambda: dialog.current_path == str(sub))
    dialog.path_edit.setText(str(target))
    dialog._on_path_enter()
    assert _pump_until(lambda: dialog.tree.selectedItems())
    assert dialog.tree.selectedItems()[0].text(0) == "note.txt"
    dialog.deleteLater()

def test_first_row_is_parent_navigation(qapp, tmp_path: Path) -> None:
    sub = tmp_path / "child"
    sub.mkdir()
    (sub / "a.txt").write_text("x", encoding="utf-8")
    params = {"mode": "file", "extensions": [], "multi": False, "title": "t", "start_path": str(sub), "window_id": "", "ssh": None}
    dialog = PickerDialog(params, None)
    for _ in range(300):
        qapp.processEvents()
        if dialog.tree.topLevelItemCount() > 1:
            break
    assert dialog.tree.topLevelItem(0).text(0) == ".."
    dialog._on_double_click(dialog.tree.topLevelItem(0), 0)
    for _ in range(300):
        qapp.processEvents()
        if dialog.current_path == str(tmp_path):
            break
    assert dialog.current_path == str(tmp_path)
    dialog.deleteLater()

def test_file_mode_without_filter_lists_every_file(qapp, tmp_path: Path) -> None:
    (tmp_path / "qwe.bin").write_text("x", encoding="utf-8")
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    base = {"mode": "file", "multi": False, "title": "t", "start_path": str(tmp_path), "window_id": "", "ssh": None}

    def _names(extensions):
        dialog = PickerDialog({**base, "extensions": extensions}, None)
        for _ in range(300):
            qapp.processEvents()
            if dialog.tree.topLevelItemCount() > 2:
                break
        names = {
            dialog.tree.topLevelItem(i).text(0)
            for i in range(dialog.tree.topLevelItemCount())
        }
        dialog.deleteLater()
        return names

    assert "qwe.bin" in _names([])
    assert "qwe.bin" not in _names(["txt"])

def test_hidden_files_shown_and_filtered(qapp, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("x", encoding="utf-8")
    (tmp_path / ".secret.txt").write_text("x", encoding="utf-8")
    (tmp_path / "visible.txt").write_text("x", encoding="utf-8")
    dialog = PickerDialog(
        {"mode": "file", "extensions": [], "multi": False, "title": "t", "start_path": str(tmp_path), "window_id": "", "ssh": None},
        None,
    )

    def _names() -> set[str]:
        for _ in range(300):
            qapp.processEvents()
            if dialog.tree.topLevelItemCount() > 2:
                break
        return {dialog.tree.topLevelItem(i).text(0) for i in range(dialog.tree.topLevelItemCount())}

    assert ".env" in _names()
    dialog._toggle_hidden(False)
    assert ".env" not in _names()
    dialog._toggle_hidden(True)
    dialog._apply_filter("secret")
    names = _names()
    assert ".secret.txt" in names and "visible.txt" not in names
    dialog.deleteLater()


def test_extension_filter_applies_to_hidden_files(qapp, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("x", encoding="utf-8")
    (tmp_path / ".secret.txt").write_text("x", encoding="utf-8")
    dialog = PickerDialog(
        {"mode": "file", "extensions": ["txt"], "multi": False, "title": "t", "start_path": str(tmp_path), "window_id": "", "ssh": None},
        None,
    )
    for _ in range(300):
        qapp.processEvents()
        if dialog.tree.topLevelItemCount() > 1:
            break
    names = {dialog.tree.topLevelItem(i).text(0) for i in range(dialog.tree.topLevelItemCount())}
    assert ".secret.txt" in names
    assert ".env" not in names
    dialog.deleteLater()
