"""开发扩展：目录加载、origin=dev、移除后不残留。"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from obox.api.extensions import DEV_EXTENSION_REMOVE_MSG
from obox.api.message import Message
from obox.app import OboxApp
from tests.fake_provider import build_provider

ROOT = Path(__file__).resolve().parent.parent


def _prepare(tmp_path: Path) -> Path:
    dev = tmp_path / "devhello"
    (dev / "views").mkdir(parents=True)
    manifest = {
        "name": "devhello",
        "version": "1.0.0",
        "publisher": "obox",
        "description": "dev fixture",
        "main": "extension.py",
        "icon": "main.svg",
        "contributes": {"views": [{"id": "devhello.main", "name": "Dev", "container": "sidebar"}]},
    }
    (dev / "extension.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (dev / "assets").mkdir()
    (dev / "assets" / "main.svg").write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><rect width=\"24\" height=\"24\" rx=\"4\" fill=\"#888\"/></svg>", encoding="utf-8")
    (dev / "extension.py").write_text(
        "def activate(context):\n"
        "    context.register_view('devhello.main', 'views/main.oml', 'sidebar', 'Dev')\n\n"
        "def deactivate(context):\n"
        "    context.subscriptions.clear()\n",
        encoding="utf-8",
    )
    (dev / "views" / "main.oml").write_text('<Div id="devhello-root"><Text id="devhello-title" text="dev" /></Div>\n', encoding="utf-8")
    return dev


def test_dev_extension_loads_without_install(qapp, tmp_path: Path) -> None:
    dev = _prepare(tmp_path)
    data_dir = tmp_path / "data"
    obox = OboxApp(ROOT, provider=build_provider(), data_dir=data_dir, language="zh-CN", dev_extensions=[str(dev)])
    obox.start()
    for _ in range(600):
        qapp.processEvents()
        time.sleep(0.02)
        if obox._extensions.get("devhello.obox", {}).get("status") in ("active", "failed"):
            break
    item = obox._extensions.get("devhello.obox") or {}
    assert item.get("origin") == "dev"
    assert item.get("status") == "active"
    assert not (data_dir / "extensions" / "devhello").exists()
    obox.bus.send(Message(src="obox", dst="obox", msg_id=DEV_EXTENSION_REMOVE_MSG, payload={"path": str(dev)}))
    for _ in range(600):
        qapp.processEvents()
        time.sleep(0.02)
        if "devhello.obox" not in obox._extensions:
            break
    assert "devhello.obox" not in obox._extensions
    assert str(dev.resolve()) not in obox._load_config().get("dev_extensions", [])
    obox.shutdown()


def test_cli_parses_dev_flags() -> None:
    from obox.main import parse_args

    args = parse_args(["--dev-extension", "a", "--dev-extension", "b", "--debug", "--debug-port", "6000", "--no-debug-wait"])
    assert args.dev_extension == ["a", "b"]
    assert args.debug is True
    assert args.debug_port == 6000
    assert args.no_debug_wait is True

def test_supervisor_debug_arguments(monkeypatch, tmp_path: Path) -> None:
    from obox.extensions import supervisor as supervisor_module

    captured: dict[str, list[str]] = {}

    class FakeProcess:
        class ProcessChannelMode:
            MergedChannels = 0

        def __init__(self, _parent=None) -> None:
            self._args: list[str] = []

        def setProgram(self, _program: str) -> None:
            pass

        def setArguments(self, args) -> None:
            self._args = list(args)
            captured["args"] = list(args)

        def arguments(self):
            return list(self._args)

        def setProcessChannelMode(self, _mode) -> None:
            pass

        class _Signal:
            def connect(self, _slot) -> None:
                pass

        errorOccurred = _Signal()
        readyReadStandardOutput = _Signal()
        finished = _Signal()

        def start(self) -> None:
            pass

    monkeypatch.setattr(supervisor_module, "QProcess", FakeProcess)
    supervisor = supervisor_module.Supervisor(
        ROOT,
        bus=None,
        extensions_root=ROOT / "extensions",
        data_dir=tmp_path,
        dev_dirs=[tmp_path / "hello"],
        debug=True,
        debug_port=5678,
    )
    supervisor._spawn()
    args = captured["args"]
    assert args[:1] == ["-Xfrozen_modules=off"]
    assert args[1:6] == ["-m", "debugpy", "--listen", "127.0.0.1:5678", "--wait-for-client"]
    assert "--dev-dir" in args and str(tmp_path / "hello") in args


def test_launch_json_has_attach_config() -> None:
    data = json.loads((ROOT / ".vscode" / "launch.json").read_text(encoding="utf-8"))
    names = [config["name"] for config in data["configurations"]]
    assert any("attach" in name for name in names)
    attach = next(config for config in data["configurations"] if config["request"] == "attach")
    assert attach["connect"]["port"] == 5678

def test_dev_extension_accepts_extension_py_path(qapp, tmp_path: Path) -> None:
    dev = _prepare(tmp_path)
    obox = OboxApp(ROOT, provider=build_provider(), data_dir=tmp_path / "data2", language="zh-CN", dev_extensions=[str(dev / "extension.py")])
    obox.start()
    for _ in range(600):
        qapp.processEvents()
        time.sleep(0.02)
        if obox._extensions.get("devhello.obox", {}).get("status") in ("active", "failed"):
            break
    assert obox._extensions.get("devhello.obox", {}).get("origin") == "dev"
    assert str(dev) in obox._dev_extensions
    obox.shutdown()