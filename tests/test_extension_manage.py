"""扩展管理：控制消息、loader 单包能力、宿主增删、差量应用与过滤。"""

from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QWidget

from obox.api.extensions import (
    EXTENSIONS_CHANGED_MSG,
    EXT_INSTALL_MSG,
    enable_extension_message,
    extensions_changed_message,
    extensions_manage_message,
    install_extension_message,
    remove_extension_message,
)
from obox.app import OboxApp
from obox.extensions.host import ExtensionHost
from obox.api.errors import ManifestError
from obox.extensions.loader import install_one, remove_one

ROOT = Path(__file__).resolve().parent.parent


class _FakeClient:
    def __init__(self) -> None:
        self.frames: list[dict] = []

    def send(self, data: dict) -> None:
        self.frames.append(data)


def _write_extension(directory: Path, name: str = "demo") -> None:
    (directory / "views").mkdir(parents=True)
    (directory / "assets").mkdir()
    (directory / "views" / "main.oml").write_text("<Div id=\"root\" />", encoding="utf-8")
    (directory / "assets" / "main.svg").write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" />", encoding="utf-8")
    (directory / "extension.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": "0.1.0",
                "publisher": "tester",
                "description": "测试扩展",
                "main": "extension.py",
                "icon": "main.svg",
                "contributes": {"views": [{"id": f"{name}.main", "name": "测试", "container": "sidebar"}]},
            }
        ),
        encoding="utf-8",
    )
    (directory / "extension.py").write_text(
        "def activate(context):\n"
        f"    context.register_view({name!r} + '.main', 'views/main.oml', 'sidebar', '测试')\n"
        "\ndef deactivate(context):\n    context.subscriptions.clear()\n",
        encoding="utf-8",
    )


def _pack(source: Path, target: Path) -> Path:
    with zipfile.ZipFile(target, "w") as archive:
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source))
    return target


def test_messages_round_trip() -> None:
    install = install_extension_message("demo.oix")
    assert install.msg_id == EXT_INSTALL_MSG
    assert install.payload["package"] == "demo.oix"
    changed = extensions_changed_message(["a"], ["b"], [], ["cmd"], [])
    assert changed.msg_id == EXTENSIONS_CHANGED_MSG
    assert changed.payload["removed"] == ["a"]
    manage = extensions_manage_message("extensions.obox", "toggle", "demo.tester", True)
    assert manage.payload == {"action": "toggle", "id": "demo.tester", "enabled": True}


def test_loader_install_and_remove(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    _write_extension(source)
    package = _pack(source, tmp_path / "demo.tester.0.1.0.oix")
    install_root = tmp_path / "extensions"
    target = install_one(package, install_root)
    assert (target / "extension.json").is_file()
    assert remove_one(install_root, "demo.tester")
    assert not target.exists()
    assert not remove_one(install_root, "demo.tester")


def test_host_install_and_remove_push_changed(tmp_path: Path) -> None:
    host = ExtensionHost(tmp_path / "extensions", tmp_path / "install", _FakeClient(), tmp_path / "storage")
    source = tmp_path / "src"
    source.mkdir()
    _write_extension(source)
    incoming = tmp_path / "install" / "incoming"
    incoming.mkdir(parents=True)
    _pack(source, incoming / "demo.tester.0.1.0.oix")

    host._on_install(install_extension_message("demo.tester.0.1.0.oix"))
    assert "demo.main" in host._views.ids()
    assert (tmp_path / "install" / "demo.tester" / "extension.json").is_file()

    host._on_remove(remove_extension_message("demo.tester"))
    assert "demo.main" not in host._views.ids()
    assert not (tmp_path / "install" / "demo.tester").exists()


class _FakeMessage:
    def __init__(self, payload: dict, msg_id: str = "", src: str = "obox") -> None:
        self.payload = payload
        self.msg_id = msg_id
        self.src = src


def _management_module():
    path = ROOT / "extensions" / "management" / "extension.py"
    spec = importlib.util.spec_from_file_location("obox_management", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_filter_extensions() -> None:
    module = _management_module()
    items = [
        {"id": "demo.tester", "name": "演示", "publisher": "tester", "version": "1.0.0", "origin": "user", "status": "active", "enabled": True},
        {"id": "settings.obox", "name": "设置", "publisher": "obox", "version": "1.0.0", "origin": "system", "status": "active", "enabled": True},
    ]
    assert len(module.filter_extensions(items, "")) == 2
    assert [item["title"] for item in module.filter_extensions(items, "obox")] == ["设置"]
    user_item = module.filter_extensions(items, "演示")[0]
    assert user_item["removable"] is True
    system_item = module.filter_extensions(items, "设置")[0]
    assert system_item["removable"] is False


def test_app_applies_removed_extension(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    obox.window.add_view("demo.main", "演示", QWidget(), "sidebar", "")
    obox._view_specs["demo.main"] = {"view_id": "demo.main", "extension_id": "demo.tester"}
    obox._extensions["demo.tester"] = {
        "id": "demo.tester",
        "name": "演示",
        "apps": [],
        "status": "active",
        "origin": "user",
    }
    message = _FakeMessage({"removed": ["demo.tester"], "changed": [], "views": [], "extensions": []})
    message.msg_id = EXTENSIONS_CHANGED_MSG
    obox._on_extensions_changed(message)
    assert "demo.main" not in obox.window.view_ids()
    assert "demo.tester" not in obox._extensions
    obox.shutdown()


def test_disabled_list_persists(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox._save_disabled_extensions(["demo.tester"])
    assert obox.disabled_extensions() == ["demo.tester"]
    assert json.loads((tmp_path / "extensions" / "disabled.json").read_text(encoding="utf-8")) == ["demo.tester"]
    obox._save_disabled_extensions([])
    assert obox.disabled_extensions() == []
    obox.shutdown()

def test_install_failure_keeps_old_version(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    _write_extension(source)
    package = _pack(source, tmp_path / "demo.tester.0.1.0.oix")
    install_root = tmp_path / "extensions"
    target = install_one(package, install_root)
    marker = target / "extension.json"
    before = marker.read_text(encoding="utf-8")

    bad = tmp_path / "bad"
    bad.mkdir()
    _write_extension(bad)
    with zipfile.ZipFile(tmp_path / "bad.oix", "w") as archive:
        for item in bad.rglob("*"):
            if item.is_file():
                archive.write(item, item.relative_to(bad))
        archive.writestr("../evil.txt", "x")
    with pytest.raises(ManifestError):
        install_one(tmp_path / "bad.oix", install_root)
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8") == before


def test_host_rejects_disabling_system_extension(tmp_path: Path) -> None:
    client = _FakeClient()
    host = ExtensionHost(tmp_path / "extensions", tmp_path / "install", client, tmp_path / "storage")
    host._on_enable(enable_extension_message("settings.obox", False))
    assert "settings.obox" not in host._disabled
    assert any("不可停用" in str(frame.get("payload", {}).get("error")) for frame in client.frames)


def test_host_ignores_foreign_src(tmp_path: Path) -> None:
    client = _FakeClient()
    host = ExtensionHost(tmp_path / "extensions", tmp_path / "install", client, tmp_path / "storage")
    host._on_install(_FakeMessage({"package": "x.oix"}, src="demo.tester"))
    assert not client.frames


def test_host_reinstall_after_disable_enables(tmp_path: Path) -> None:
    host = ExtensionHost(tmp_path / "extensions", tmp_path / "install", _FakeClient(), tmp_path / "storage")
    source = tmp_path / "src"
    source.mkdir()
    _write_extension(source)
    incoming = tmp_path / "install" / "incoming"
    incoming.mkdir(parents=True)
    _pack(source, incoming / "demo.tester.0.1.0.oix")
    host._on_install(install_extension_message("demo.tester.0.1.0.oix"))
    host._on_enable(enable_extension_message("demo.tester", False))
    assert "demo.tester" in host._disabled
    _pack(source, incoming / "demo.tester.0.1.0.oix")
    host._on_install(install_extension_message("demo.tester.0.1.0.oix"))
    assert "demo.tester" not in host._disabled
    assert "demo.main" in host._views.ids()


def test_app_removes_view_when_extension_disabled(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    obox.window.add_view("demo.main", "演示", QWidget(), "sidebar", "")
    obox._view_specs["demo.main"] = {"view_id": "demo.main", "extension_id": "demo.tester"}
    obox._extensions["demo.tester"] = {"id": "demo.tester", "name": "演示", "status": "active", "apps": []}
    message = _FakeMessage(
        {
            "removed": [],
            "changed": ["demo.tester"],
            "views": [],
            "extensions": [{"id": "demo.tester", "name": "演示", "status": "disabled", "apps": []}],
        }
    )
    obox._on_extensions_changed(message)
    assert "demo.main" not in obox.window.view_ids()
    obox.shutdown()


def test_app_clears_disabled_on_remove(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    obox.bus.send = lambda *args, **kwargs: None
    obox.bus.reply = lambda *args, **kwargs: None
    obox._save_disabled_extensions(["demo.tester"])
    obox._extensions["demo.tester"] = {"id": "demo.tester", "name": "演示", "status": "disabled", "apps": []}
    obox._on_extensions_changed(_FakeMessage({"removed": ["demo.tester"], "views": [], "extensions": []}))
    assert "demo.tester" not in obox.disabled_extensions()
    obox.shutdown()

def test_changed_message_decodes_round_trip() -> None:
    from obox.api.component import decode_message

    message = extensions_changed_message(["a"], ["b"], [], [], [], {})
    decoded = decode_message(message.to_dict())
    assert decoded.msg_id == EXTENSIONS_CHANGED_MSG
    assert decoded.payload["removed"] == ["a"]
    assert decoded.payload["changed"] == ["b"]


def test_host_pushes_changed_frame(tmp_path: Path) -> None:
    client = _FakeClient()
    host = ExtensionHost(tmp_path / "extensions", tmp_path / "install", client, tmp_path / "storage")
    source = tmp_path / "src"
    source.mkdir()
    _write_extension(source)
    incoming = tmp_path / "install" / "incoming"
    incoming.mkdir(parents=True)
    _pack(source, incoming / "demo.tester.0.1.0.oix")
    host._on_install(install_extension_message("demo.tester.0.1.0.oix"))
    assert any(frame.get("msg_id") == EXTENSIONS_CHANGED_MSG for frame in client.frames)
