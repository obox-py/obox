"""设置页「行为」分类。"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from obox.qt import Qt
from obox.qt import QTest
from obox.qt import QCheckBox, QDialog, QPushButton, QWidget

from obox.app import OboxApp
from obox.ui.close_dialog import CloseDialog

ROOT = Path(__file__).resolve().parent.parent


def test_behavior_group_has_close_action(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    groups = {group["id"]: group for group in obox._settings_groups()}
    assert "behavior" in groups
    items = {item["key"]: item for item in groups["behavior"]["items"]}
    item = items["obox.close_action"]
    assert item["type"] == "enum"
    assert item["options"] == "ask,tray,quit"
    assert item["value"] in item["options"]
    obox.shutdown()

def test_close_dialog_uses_theme_panel(qapp) -> None:
    dialog = CloseDialog()
    assert dialog.isModal()
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dialog.findChild(QWidget, "obox-modal-card") is not None
    labels = [button.text() for button in dialog.findChildren(QPushButton)]
    assert labels == ["最小化到托盘", "退出", "取消"]
    assert dialog.findChild(QCheckBox) is not None
    dialog.reject()


def test_close_dialog_esc_cancels(qapp) -> None:
    dialog = CloseDialog()
    dialog.show()
    QTest.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.result() == QDialog.DialogCode.Rejected

def test_close_action_setting_is_accepted(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    assert obox._setting_value_ok("obox.close_action", "tray")
    assert not obox._setting_value_ok("obox.close_action", "bogus")
    obox._on_settings_set(
        SimpleNamespace(
            payload={"key": "obox.close_action", "value": "tray"}, correlation_id=""
        )
    )
    assert obox.close_action == "tray"
    obox.shutdown()

def test_close_with_tray_action_hides_window(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    obox._tray = SimpleNamespace(hide=lambda: None, show=lambda: None, deleteLater=lambda: None)
    obox.close_action = "tray"
    obox.window.show()
    obox._on_close_requested()
    assert not obox.window.isVisible()
    obox.shutdown()