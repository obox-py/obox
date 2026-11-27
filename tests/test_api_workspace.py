"""workspace/storage/message/log 消息构造与宿主 DevApiService 的读写边界。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from obox.api import log, message, storage, workspace
from obox.api.commands import COMMANDS_EXECUTE_MSG, COMMANDS_GET_MSG
from obox.api.extensions import EXTENSIONS_ALL_MSG, EXTENSIONS_GET_MSG, HOST_ID
from obox.api.message import Message
from obox.extensions.contributions import CommandRegistry
from obox.extensions.devapi import DevApiService


class _Request:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def result(self) -> dict[str, Any]:
        return self._payload


class FakeContext:
    """把 ctx.request 直接接到 DevApiService，模拟消息往返。"""

    extension_id = "demo.obox"
    window_id = None

    def __init__(self, service: Any = None, log_dir: Path | None = None) -> None:
        self.service = service
        self.log_dir = log_dir
        self.sent: list[Message] = []
        self.listeners: dict[str, list[Any]] = {}

    def send(self, sent: Message) -> None:
        self.sent.append(sent)

    def request(self, sent: Message, timeout: float = 5.0) -> _Request:
        self.sent.append(sent)
        assert self.service is not None, "测试未接入 DevApiService"
        payload = self.service.handle(sent)
        if "error" in payload:
            raise RuntimeError(f"{payload['error']}: {payload.get('message', '')}")
        return _Request(payload)

    def on(self, message_id: str, handler: Any) -> Any:
        self.listeners.setdefault(message_id, []).append(handler)

        def _unsubscribe() -> None:
            handlers = self.listeners.get(message_id, [])
            if handler in handlers:
                handlers.remove(handler)

        return _unsubscribe


class EchoService:
    def handle(self, sent: Message) -> dict[str, Any]:
        return {"pong": sent.payload.get("n")}


@pytest.fixture
def folders(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "ws"
    extension = tmp_path / "ext"
    (root / "src").mkdir(parents=True)
    (root / "build").mkdir()
    (root / "src" / "a.py").write_text("print('a')\n", encoding="utf-8")
    (root / "build" / "b.py").write_text("print('b')\n", encoding="utf-8")
    (root / "note.txt").write_text("hello", encoding="utf-8")
    extension.mkdir()
    (extension / "tool.py").write_text("x = 1\n", encoding="utf-8")
    return root, extension


def _service(tmp_path: Path, folders: tuple[Path, Path]) -> DevApiService:
    root, extension = folders
    return DevApiService(
        tmp_path / "storage",
        manifests={"demo.obox": {"id": "demo.obox", "directory": str(extension)}},
        folders=[root],
        configuration={"obox": {"theme": "dark"}},
    )


def test_workspace_message_construction(tmp_path: Path) -> None:
    ctx = FakeContext(DevApiService(tmp_path / "storage"))
    workspace.findFiles(ctx, "**/*.py", "build/**", 10)
    assert ctx.sent[-1] == Message(
        src="demo.obox",
        dst=HOST_ID,
        msg_id=workspace.WORKSPACE_FIND_FILES_MSG,
        payload={"include": "**/*.py", "exclude": "build/**", "maxResults": 10},
    )
    workspace.workspaceFolders(ctx)
    assert ctx.sent[-1] == Message(
        src="demo.obox", dst=HOST_ID, msg_id=workspace.WORKSPACE_FOLDERS_MSG
    )


def test_workspace_folders_and_configuration(tmp_path: Path, folders: tuple[Path, Path]) -> None:
    ctx = FakeContext(_service(tmp_path, folders))
    root, _ = folders
    assert workspace.workspaceFolders(ctx) == [
        {"uri": str(root.resolve()), "name": "ws", "index": 0}
    ]
    config = workspace.getConfiguration(ctx, "obox")
    assert config.get("theme") == "dark"
    assert config.has("theme")
    config.update("theme", "light")
    assert workspace.getConfiguration(ctx, "obox").get("theme") == "light"


def test_workspace_read_file_roundtrip(tmp_path: Path, folders: tuple[Path, Path]) -> None:
    ctx = FakeContext(_service(tmp_path, folders))
    root, _ = folders
    target = root / "note.txt"
    assert workspace.readFile(ctx, str(target)) == b"hello"
    assert ctx.sent[-1].msg_id == workspace.WORKSPACE_READ_FILE_MSG


def test_workspace_configuration_change_event(tmp_path: Path, folders: tuple[Path, Path]) -> None:
    ctx = FakeContext(_service(tmp_path, folders))
    seen: list[dict[str, Any]] = []
    disposable = workspace.onDidChangeConfiguration(ctx, seen.append)
    handler = ctx.listeners[workspace.WORKSPACE_CONFIG_CHANGED_MSG][0]
    handler(
        Message(
            src="obox",
            dst="demo.obox",
            msg_id=workspace.WORKSPACE_CONFIG_CHANGED_MSG,
            payload={"section": "obox", "key": "theme", "value": "light"},
        )
    )
    assert seen == [{"section": "obox", "key": "theme", "value": "light"}]
    disposable.dispose()
    handler(
        Message(
            src="obox",
            dst="demo.obox",
            msg_id=workspace.WORKSPACE_CONFIG_CHANGED_MSG,
            payload={"section": "obox", "key": "theme", "value": "dark"},
        )
    )
    assert len(seen) == 1


def test_file_system_watcher_filters_events(tmp_path: Path, folders: tuple[Path, Path]) -> None:
    ctx = FakeContext(_service(tmp_path, folders))
    watcher = workspace.createFileSystemWatcher(ctx, "**/*.py")
    registration = ctx.sent[-1]
    assert registration.msg_id == workspace.WORKSPACE_CREATE_WATCHER_MSG
    watcher_id = registration.payload["watcherId"]
    created: list[str] = []
    watcher.onDidCreate(created.append)
    handler = ctx.listeners[workspace.WORKSPACE_WATCH_EVENT_MSG][0]
    handler(
        Message(
            src=HOST_ID,
            dst="demo.obox",
            msg_id=workspace.WORKSPACE_WATCH_EVENT_MSG,
            payload={"watcherId": watcher_id, "event": "create", "uri": "C:/ws/a.py"},
        )
    )
    handler(
        Message(
            src=HOST_ID,
            dst="demo.obox",
            msg_id=workspace.WORKSPACE_WATCH_EVENT_MSG,
            payload={"watcherId": watcher_id, "event": "create", "uri": "C:/ws/a.txt"},
        )
    )
    assert created == ["C:/ws/a.py"]
    watcher.dispose()
    assert ctx.sent[-1].msg_id == workspace.WORKSPACE_DISPOSE_WATCHER_MSG


def test_storage_roundtrip_and_files(tmp_path: Path) -> None:
    root = tmp_path / "storage"
    ctx = FakeContext(DevApiService(root))
    assert storage.globalState.get(ctx, "count", 0) == 0
    storage.globalState.update(ctx, "count", 1)
    storage.workspaceState.update(ctx, "open", True)
    assert storage.globalState.get(ctx, "count") == 1
    assert storage.globalState.keys(ctx) == ["count"]
    assert storage.workspaceState.get(ctx, "open") is True

    global_file = root / "demo.obox" / "global.json"
    workspace_file = root / "demo.obox" / "workspace.json"
    assert json.loads(global_file.read_text(encoding="utf-8")) == {"count": 1}
    assert json.loads(workspace_file.read_text(encoding="utf-8")) == {"open": True}
    assert storage.storage_update_message("demo.obox", "global", "count", 1) == Message(
        src="demo.obox",
        dst=HOST_ID,
        msg_id=storage.STORAGE_UPDATE_MSG,
        payload={"scope": "global", "key": "count", "value": 1},
    )

    storage.globalState.update(ctx, "count", None)
    assert storage.globalState.get(ctx, "count", "gone") == "gone"
    assert storage.globalState.keys(ctx) == []
    assert json.loads(workspace_file.read_text(encoding="utf-8")) == {"open": True}


def test_find_files_scoped_and_read_only(
    tmp_path: Path, folders: tuple[Path, Path]
) -> None:
    ctx = FakeContext(_service(tmp_path, folders))
    root, extension = folders
    files = workspace.findFiles(ctx, "**/*.py", "build/**", 50)
    assert str((root / "src" / "a.py").resolve()) in files
    assert str((extension / "tool.py").resolve()) in files
    assert all("build" not in Path(item).parts for item in files)
    assert len(workspace.findFiles(ctx, "**/*.py", "", 1)) == 1


def test_find_files_rejects_escape(
    tmp_path: Path, folders: tuple[Path, Path]
) -> None:
    service = _service(tmp_path, folders)
    root, _ = folders
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    result = service.handle(
        Message(
            src="demo.obox",
            dst=HOST_ID,
            msg_id=workspace.WORKSPACE_FIND_FILES_MSG,
            payload={"include": "../secret.txt"},
        )
    )
    assert result["error"] == "E_PATH_OUTSIDE"

    result = service.handle(
        Message(
            src="demo.obox",
            dst=HOST_ID,
            msg_id=workspace.WORKSPACE_FIND_FILES_MSG,
            payload={"include": str(outside)},
        )
    )
    assert result["error"] == "E_PATH_OUTSIDE"

    result = service.handle(
        Message(
            src="demo.obox",
            dst=HOST_ID,
            msg_id=workspace.WORKSPACE_READ_FILE_MSG,
            payload={"uri": str(outside)},
        )
    )
    assert result["error"] == "E_PATH_OUTSIDE"

    # 允许范围内的文件仍可读；越出工作区的路径不会被 glob 命中。
    result = service.handle(
        Message(
            src="demo.obox",
            dst=HOST_ID,
            msg_id=workspace.WORKSPACE_READ_FILE_MSG,
            payload={"uri": str(root / "note.txt")},
        )
    )
    assert "error" not in result


def test_message_send_request_broadcast(tmp_path: Path) -> None:
    ctx = FakeContext(EchoService())
    message.send(ctx, "obox", "PING", {"n": 1})
    assert ctx.sent[-1] == Message(
        src="demo.obox", dst="obox", msg_id="PING", payload={"n": 1}
    )
    assert message.request(ctx, "host.obox", "PING", {"n": 2}) == {"pong": 2}
    message.broadcast(ctx, "PING", {"n": 3})
    assert ctx.sent[-1].is_broadcast
    assert ctx.sent[-1].payload == {"n": 3}


def test_output_channel_writes_file_and_notifies(tmp_path: Path) -> None:
    ctx = FakeContext(log_dir=tmp_path / "logs")
    channel = log.createOutputChannel(ctx, "demo")
    channel.info("started %s", 1)
    channel.appendLine("raw")
    assert (tmp_path / "logs" / "demo.log").read_text(encoding="utf-8") == (
        "[info] started 1\nraw\n"
    )
    assert [item.msg_id for item in ctx.sent] == [
        log.LOG_CREATE_MSG,
        log.LOG_APPEND_MSG,
        log.LOG_APPEND_MSG,
    ]
    channel.dispose()
    assert ctx.sent[-1].msg_id == log.LOG_DISPOSE_MSG


def test_devapi_commands_and_extensions(tmp_path: Path) -> None:
    registry = CommandRegistry()
    registry.register("demo.obox", "demo.add", lambda a, b=0: a + b)
    service = DevApiService(
        tmp_path / "storage",
        commands=registry,
        manifests={
            "demo.obox": {
                "id": "demo.obox",
                "name": "Demo",
                "version": "1.0.0",
                "publisher": "obox",
                "directory": str(tmp_path / "ext"),
                "status": "active",
                "origin": "source",
            }
        },
    )
    executed = service.handle(
        Message(
            src="demo.obox",
            dst=HOST_ID,
            msg_id=COMMANDS_EXECUTE_MSG,
            payload={"command": "demo.add", "args": [2, 3]},
        )
    )
    assert executed == {"result": 5}
    listed = service.handle(
        Message(src="demo.obox", dst=HOST_ID, msg_id=COMMANDS_GET_MSG)
    )
    assert listed == {"commands": ["demo.add"]}
    items = service.handle(
        Message(src="demo.obox", dst=HOST_ID, msg_id=EXTENSIONS_ALL_MSG)
    )["items"]
    assert items[0]["id"] == "demo.obox"
    assert items[0]["storagePath"] == str(tmp_path / "storage" / "demo.obox")
    found = service.handle(
        Message(
            src="demo.obox",
            dst=HOST_ID,
            msg_id=EXTENSIONS_GET_MSG,
            payload={"id": "demo.obox"},
        )
    )
    assert found["extension"]["name"] == "Demo"
