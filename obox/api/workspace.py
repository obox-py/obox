"""workspace 命名空间：工作区目录、配置、文件搜索/读取与文件监视。"""

from __future__ import annotations

import base64
import fnmatch
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .extensions import HOST_ID
from .message import OB_BOX, Disposable, Message, request, send
from .message import on as subscribe

WORKSPACE_FOLDERS_MSG = "WORKSPACE_FOLDERS_MSG"
WORKSPACE_GET_CONFIGURATION_MSG = "WORKSPACE_GET_CONFIGURATION_MSG"
WORKSPACE_UPDATE_CONFIGURATION_MSG = "WORKSPACE_UPDATE_CONFIGURATION_MSG"
WORKSPACE_CONFIG_CHANGED_MSG = "WORKSPACE_CONFIG_CHANGED_MSG"
WORKSPACE_FIND_FILES_MSG = "WORKSPACE_FIND_FILES_MSG"
WORKSPACE_READ_FILE_MSG = "WORKSPACE_READ_FILE_MSG"
WORKSPACE_CREATE_WATCHER_MSG = "WORKSPACE_CREATE_WATCHER_MSG"
WORKSPACE_DISPOSE_WATCHER_MSG = "WORKSPACE_DISPOSE_WATCHER_MSG"
WORKSPACE_WATCH_EVENT_MSG = "WORKSPACE_WATCH_EVENT_MSG"

WATCH_CREATE = "create"
WATCH_CHANGE = "change"
WATCH_DELETE = "delete"

REQUEST_TIMEOUT = 30.0


def workspace_folders_message(src: str) -> Message:
    return Message(src=src, dst=HOST_ID, msg_id=WORKSPACE_FOLDERS_MSG)


def workspace_get_configuration_message(src: str, section: str = "") -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=WORKSPACE_GET_CONFIGURATION_MSG,
        payload={"section": section},
    )


def workspace_update_configuration_message(
    src: str, section: str, key: str, value: Any
) -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=WORKSPACE_UPDATE_CONFIGURATION_MSG,
        payload={"section": section, "key": key, "value": value},
    )


def workspace_find_files_message(
    src: str, include: str, exclude: str = "", maxResults: int = 2000
) -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=WORKSPACE_FIND_FILES_MSG,
        payload={"include": include, "exclude": exclude, "maxResults": maxResults},
    )


def workspace_read_file_message(src: str, uri: str) -> Message:
    return Message(
        src=src, dst=HOST_ID, msg_id=WORKSPACE_READ_FILE_MSG, payload={"uri": uri}
    )


def workspace_create_watcher_message(src: str, watcher_id: str, glob: str) -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=WORKSPACE_CREATE_WATCHER_MSG,
        payload={"watcherId": watcher_id, "glob": glob},
    )


def workspace_dispose_watcher_message(src: str, watcher_id: str) -> Message:
    return Message(
        src=src,
        dst=HOST_ID,
        msg_id=WORKSPACE_DISPOSE_WATCHER_MSG,
        payload={"watcherId": watcher_id},
    )


def workspace_watch_event_message(
    dst: str, watcher_id: str, event: str, uri: str
) -> Message:
    """宿主推送文件事件；event 是 create/change/delete。"""
    return Message(
        src=HOST_ID,
        dst=dst,
        msg_id=WORKSPACE_WATCH_EVENT_MSG,
        payload={"watcherId": watcher_id, "event": event, "uri": uri},
    )


def workspace_configuration_changed_message(
    dst: str, section: str = "", key: str = "", value: Any = None
) -> Message:
    return Message(
        src=OB_BOX,
        dst=dst,
        msg_id=WORKSPACE_CONFIG_CHANGED_MSG,
        payload={"section": section, "key": key, "value": value},
    )


def workspaceFolders(ctx: Any) -> list[dict[str, Any]]:
    """当前工作区根目录；无工作区时为空列表。"""
    payload = request(ctx, HOST_ID, WORKSPACE_FOLDERS_MSG, {}, REQUEST_TIMEOUT)
    folders = payload.get("folders") or []
    return [dict(item) for item in folders if isinstance(item, dict)]


class WorkspaceConfiguration:
    """某个 section 的配置视图；值在创建时取一次快照。"""

    def __init__(self, ctx: Any, section: str, values: dict[str, Any]) -> None:
        self._ctx = ctx
        self.section = section
        self._values = dict(values)

    def get(self, key: str, defaultValue: Any = None) -> Any:
        return self._values.get(key, defaultValue)

    def has(self, key: str) -> bool:
        return key in self._values

    def update(self, key: str, value: Any) -> None:
        request(
            self._ctx,
            HOST_ID,
            WORKSPACE_UPDATE_CONFIGURATION_MSG,
            {"section": self.section, "key": key, "value": value},
            REQUEST_TIMEOUT,
        )
        if value is None:
            self._values.pop(key, None)
        else:
            self._values[key] = value


def getConfiguration(ctx: Any, section: str = "") -> WorkspaceConfiguration:
    payload = request(
        ctx, HOST_ID, WORKSPACE_GET_CONFIGURATION_MSG, {"section": section}, REQUEST_TIMEOUT
    )
    values = payload.get("values") or {}
    if not isinstance(values, dict):
        values = {}
    return WorkspaceConfiguration(ctx, section, values)


def findFiles(
    ctx: Any, include: str, exclude: str = "", maxResults: int = 2000
) -> list[str]:
    """只读 glob 搜索；结果由宿主限制在工作区与当前扩展目录内。"""
    payload = request(
        ctx,
        HOST_ID,
        WORKSPACE_FIND_FILES_MSG,
        {"include": include, "exclude": exclude, "maxResults": maxResults},
        REQUEST_TIMEOUT,
    )
    files = payload.get("files") or []
    return [str(item) for item in files]


def readFile(ctx: Any, uri: str) -> bytes:
    """读文件内容；越出工作区/扩展目录时宿主拒绝。"""
    payload = request(
        ctx, HOST_ID, WORKSPACE_READ_FILE_MSG, {"uri": str(uri)}, REQUEST_TIMEOUT
    )
    return base64.b64decode(str(payload.get("data") or ""))


def _match_glob(glob: str, uri: str) -> bool:
    text = uri.replace("\\", "/")
    pattern = glob.replace("\\", "/")
    if "/" in pattern:
        return fnmatch.fnmatchcase(text, pattern)
    return fnmatch.fnmatchcase(Path(text).name, pattern)


class FileSystemWatcher:
    """按 glob 过滤宿主推送的 create/change/delete 事件。"""

    def __init__(self, ctx: Any, glob: str) -> None:
        self._ctx = ctx
        self.glob = glob
        self._watcher_id = uuid.uuid4().hex
        self._listeners: dict[str, list[Callable[[str], None]]] = {
            WATCH_CREATE: [],
            WATCH_CHANGE: [],
            WATCH_DELETE: [],
        }
        self._disposed = False
        self._subscription = subscribe(ctx, WORKSPACE_WATCH_EVENT_MSG, self._on_event)
        send(
            ctx,
            HOST_ID,
            WORKSPACE_CREATE_WATCHER_MSG,
            {"watcherId": self._watcher_id, "glob": glob},
        )

    def _on_event(self, payload: Any, src: str) -> None:
        data = payload if isinstance(payload, dict) else {}
        if str(data.get("watcherId") or "") != self._watcher_id:
            return
        uri = str(data.get("uri") or "")
        if not _match_glob(self.glob, uri):
            return
        for listener in list(self._listeners.get(str(data.get("event") or ""), ())):
            listener(uri)

    def _add(self, kind: str, listener: Callable[[str], None]) -> Disposable:
        if kind not in self._listeners:
            raise ValueError(f"未知文件事件：{kind}")
        self._listeners[kind].append(listener)

        def _remove() -> None:
            listeners = self._listeners[kind]
            if listener in listeners:
                listeners.remove(listener)

        return Disposable(_remove)

    def onDidCreate(self, listener: Callable[[str], None]) -> Disposable:
        return self._add(WATCH_CREATE, listener)

    def onDidChange(self, listener: Callable[[str], None]) -> Disposable:
        return self._add(WATCH_CHANGE, listener)

    def onDidDelete(self, listener: Callable[[str], None]) -> Disposable:
        return self._add(WATCH_DELETE, listener)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        self._subscription.dispose()
        send(
            self._ctx,
            HOST_ID,
            WORKSPACE_DISPOSE_WATCHER_MSG,
            {"watcherId": self._watcher_id},
        )
        for listeners in self._listeners.values():
            listeners.clear()


def createFileSystemWatcher(ctx: Any, glob: str) -> FileSystemWatcher:
    return FileSystemWatcher(ctx, glob)


def onDidChangeConfiguration(
    ctx: Any, listener: Callable[[dict[str, Any]], None]
) -> Disposable:
    def _handle(payload: Any, src: str) -> None:
        listener(dict(payload) if isinstance(payload, dict) else {})

    return subscribe(ctx, WORKSPACE_CONFIG_CHANGED_MSG, _handle)
