"""宿主侧的开发者 API 服务。

扩展通过 obox.api 的 workspace/storage 等模块发来请求，宿主把消息交给
DevApiService.handle，返回值作为应答 payload 回给扩展。
"""

from __future__ import annotations

import base64
import fnmatch
import json
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from ..api.commands import COMMANDS_EXECUTE_MSG, COMMANDS_GET_MSG
from ..api.extensions import EXTENSIONS_ALL_MSG, EXTENSIONS_GET_MSG
from ..api.message import Message
from ..api.storage import (
    GLOBAL_SCOPE,
    STORAGE_GET_MSG,
    STORAGE_KEYS_MSG,
    STORAGE_UPDATE_MSG,
    WORKSPACE_SCOPE,
)
from ..api.workspace import (
    WORKSPACE_FIND_FILES_MSG,
    WORKSPACE_FOLDERS_MSG,
    WORKSPACE_GET_CONFIGURATION_MSG,
    WORKSPACE_READ_FILE_MSG,
    WORKSPACE_UPDATE_CONFIGURATION_MSG,
)
from .contributions import CommandRegistry

E_API_PAYLOAD = "E_API_PAYLOAD"
E_PATH_OUTSIDE = "E_PATH_OUTSIDE"
E_FILE_NOT_FOUND = "E_FILE_NOT_FOUND"
E_STORAGE = "E_STORAGE"
E_STORAGE_SCOPE = "E_STORAGE_SCOPE"
E_COMMAND = "E_COMMAND"
E_UNKNOWN_MESSAGE = "E_UNKNOWN_MESSAGE"
E_DEVAPI = "E_DEVAPI"

DEFAULT_MAX_RESULTS = 2000
MAX_RESULTS_LIMIT = 2000


class _ApiError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _extension_id_pattern(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", value)) and ".." not in value


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return str(value)
    return value


def _describe_manifest(item: Any, key: Any, storage_root: Path) -> dict[str, Any]:
    """把 Manifest 或宿主快照 dict 归一成扩展描述。"""
    if isinstance(item, Mapping):
        base = dict(item)
        extension_id = str(
            base.get("id") or base.get("extension_id") or key or ""
        ).strip()
        directory = base.get("directory", "")
        status = base.get("status", "active")
        origin = base.get("origin", "source")
        name = base.get("name", "")
        version = base.get("version", "")
        publisher = base.get("publisher", "")
        description = base.get("description", "")
    else:
        base = {}
        extension_id = str(
            getattr(item, "extension_id", "") or getattr(item, "id", "") or key or ""
        ).strip()
        directory = getattr(item, "directory", "")
        status = getattr(item, "status", "active")
        origin = getattr(item, "origin", "source")
        name = getattr(item, "name", "")
        version = getattr(item, "version", "")
        publisher = getattr(item, "publisher", "")
        description = getattr(item, "description", "")
    if not extension_id:
        return {}
    described = {
        **base,
        "id": extension_id,
        "name": str(name),
        "version": str(version),
        "publisher": str(publisher),
        "description": str(description),
        "directory": str(directory) if directory else "",
        "storagePath": str(storage_root / extension_id),
        "status": str(status or "active"),
        "origin": str(origin or "source"),
    }
    return described


def _glob_match(relative: str, pattern: str) -> bool:
    text = relative.replace("\\", "/")
    candidate = pattern.replace("\\", "/")
    if fnmatch.fnmatchcase(text, candidate):
        return True
    if "/" not in candidate and fnmatch.fnmatchcase(PurePosixPath(text).name, candidate):
        return True
    return candidate.startswith("**/") and fnmatch.fnmatchcase(text, candidate[3:])


class DevApiService:
    """处理扩展 API 中由宿主负责的部分；不依赖 Qt。"""

    MESSAGE_IDS = frozenset(
        {
            STORAGE_GET_MSG,
            STORAGE_UPDATE_MSG,
            STORAGE_KEYS_MSG,
            WORKSPACE_FOLDERS_MSG,
            WORKSPACE_GET_CONFIGURATION_MSG,
            WORKSPACE_UPDATE_CONFIGURATION_MSG,
            WORKSPACE_FIND_FILES_MSG,
            WORKSPACE_READ_FILE_MSG,
            COMMANDS_EXECUTE_MSG,
            COMMANDS_GET_MSG,
            EXTENSIONS_ALL_MSG,
            EXTENSIONS_GET_MSG,
        }
    )

    def __init__(
        self,
        storage_root: Path | str,
        commands: CommandRegistry | None = None,
        manifests: (
            Mapping[str, Any]
            | Sequence[Any]
            | Callable[[], Mapping[str, Any] | Sequence[Any]]
            | None
        ) = None,
        folders: Sequence[Path | str | Mapping[str, Any]] | None = None,
        configuration: Mapping[str, Any] | None = None,
    ) -> None:
        """storage_root 是扩展存储根；manifests 可为 dict/list/无参 callable；
        folders 是工作区根（单个根也可）；configuration 是 getConfiguration 的配置树。
        """
        self._storage_root = Path(storage_root)
        self._commands = commands
        self._manifests = manifests
        if folders is None:
            self._folders: list[Any] = []
        elif isinstance(folders, (str, Path, Mapping)):
            self._folders = [folders]
        else:
            self._folders = list(folders)
        self._configuration: dict[str, Any] = dict(configuration or {})

    def handles(self, message_id: str) -> bool:
        return message_id in self.MESSAGE_IDS

    def handle(self, message: Message) -> dict[str, Any]:
        """返回应答 payload；错误以 {"error", "message"} 形式返回。"""
        try:
            return self._dispatch(message)
        except _ApiError as exc:
            return {"error": exc.code, "message": str(exc)}
        except Exception as exc:  # noqa: BLE001 - 宿主侧兜底，避免坏请求拖垮扩展宿主
            return {"error": E_DEVAPI, "message": str(exc)}

    # ---- 分发 ----

    def _dispatch(self, message: Message) -> dict[str, Any]:
        message_id = str(message.msg_id)
        payload = message.payload or {}
        if not isinstance(payload, dict):
            raise _ApiError(E_API_PAYLOAD, "payload 必须是对象")
        extension_id = str(message.src)

        if message_id == STORAGE_GET_MSG:
            return self._storage_get(extension_id, payload)
        if message_id == STORAGE_UPDATE_MSG:
            return self._storage_update(extension_id, payload)
        if message_id == STORAGE_KEYS_MSG:
            return self._storage_keys(extension_id, payload)
        if message_id == WORKSPACE_FOLDERS_MSG:
            return self._workspace_folders()
        if message_id == WORKSPACE_GET_CONFIGURATION_MSG:
            return self._workspace_get_configuration(payload)
        if message_id == WORKSPACE_UPDATE_CONFIGURATION_MSG:
            return self._workspace_update_configuration(payload)
        if message_id == WORKSPACE_FIND_FILES_MSG:
            return self._workspace_find_files(extension_id, payload)
        if message_id == WORKSPACE_READ_FILE_MSG:
            return self._workspace_read_file(extension_id, payload)
        if message_id == COMMANDS_EXECUTE_MSG:
            return self._commands_execute(payload)
        if message_id == COMMANDS_GET_MSG:
            return self._commands_list()
        if message_id == EXTENSIONS_ALL_MSG:
            return self._extensions_all()
        if message_id == EXTENSIONS_GET_MSG:
            return self._extensions_get(payload)
        raise _ApiError(E_UNKNOWN_MESSAGE, f"未处理的开发者 API 消息：{message_id}")

    # ---- storage ----

    def _storage_path(self, extension_id: str, scope: str) -> Path:
        if scope not in (GLOBAL_SCOPE, WORKSPACE_SCOPE):
            raise _ApiError(E_STORAGE_SCOPE, f"未知状态作用域：{scope}")
        if not _extension_id_pattern(extension_id):
            raise _ApiError(E_API_PAYLOAD, f"非法扩展标识：{extension_id}")
        name = "global.json" if scope == GLOBAL_SCOPE else "workspace.json"
        return self._storage_root / extension_id / name

    def _storage_get(self, extension_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload.get("key") or "")
        if not key:
            raise _ApiError(E_API_PAYLOAD, "缺少状态键")
        state = self._read_state(self._storage_path(extension_id, self._scope(payload)))
        return {"value": state[key] if key in state else payload.get("default")}

    def _storage_update(self, extension_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload.get("key") or "")
        if not key:
            raise _ApiError(E_API_PAYLOAD, "缺少状态键")
        path = self._storage_path(extension_id, self._scope(payload))
        state = self._read_state(path)
        value = payload.get("value")
        if value is None:
            state.pop(key, None)
        else:
            try:
                json.dumps(value)
            except (TypeError, ValueError) as exc:
                raise _ApiError(E_STORAGE, f"状态值必须可 JSON 序列化：{exc}") from exc
            state[key] = value
        self._write_state(path, state)
        return {"ok": True, "keys": sorted(state)}

    def _storage_keys(self, extension_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._read_state(self._storage_path(extension_id, self._scope(payload)))
        return {"keys": sorted(state)}

    @staticmethod
    def _scope(payload: dict[str, Any]) -> str:
        return str(payload.get("scope") or GLOBAL_SCOPE)

    def _read_state(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write_state(self, path: Path, state: dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(path.suffix + ".tmp")
            temp.write_text(
                json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temp.replace(path)
        except (OSError, TypeError, ValueError) as exc:
            raise _ApiError(E_STORAGE, f"状态写入失败：{exc}") from exc

    # ---- workspace ----

    def _resolved_folders(self) -> list[Path]:
        result: list[Path] = []
        seen: set[Path] = set()
        for value in self._folders:
            path = self._as_configured_path(value)
            if path is None:
                continue
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            result.append(resolved)
        return result

    @staticmethod
    def _as_configured_path(value: Path | str | Mapping[str, Any]) -> Path | None:
        if isinstance(value, Mapping):
            value = value.get("path") or value.get("uri") or ""
        if not value:
            return None
        return Path(str(value))

    def _workspace_folders(self) -> dict[str, Any]:
        folders = [
            {"uri": str(path), "name": path.name or str(path), "index": index}
            for index, path in enumerate(self._resolved_folders())
        ]
        return {"folders": folders}

    def _section_values(self, section: str) -> dict[str, Any]:
        if not section:
            return dict(self._configuration)
        node: Any = self._configuration
        for part in section.split("."):
            if not isinstance(node, dict) or part not in node:
                prefix = f"{section}."
                return {
                    key[len(prefix) :]: value
                    for key, value in self._configuration.items()
                    if key.startswith(prefix)
                }
            node = node[part]
        return dict(node) if isinstance(node, dict) else {}

    def _workspace_get_configuration(self, payload: dict[str, Any]) -> dict[str, Any]:
        section = str(payload.get("section") or "")
        return {"section": section, "values": self._section_values(section)}

    def _workspace_update_configuration(self, payload: dict[str, Any]) -> dict[str, Any]:
        section = str(payload.get("section") or "")
        key = str(payload.get("key") or "")
        if not key:
            raise _ApiError(E_API_PAYLOAD, "缺少配置键")
        node: dict[str, Any] = self._configuration
        if section:
            for part in section.split("."):
                child = node.get(part)
                if not isinstance(child, dict):
                    child = {}
                    node[part] = child
                node = child
        value = payload.get("value")
        if value is None:
            node.pop(key, None)
        else:
            node[key] = value
        return {"ok": True, "values": self._section_values(section)}

    def _roots(self, extension_id: str) -> list[Path]:
        roots = [path for path in self._resolved_folders() if path.is_dir()]
        directory = self._extension_directory(extension_id)
        if directory is not None:
            try:
                resolved = directory.resolve()
            except OSError:
                resolved = None
            if resolved is not None and resolved.is_dir() and resolved not in roots:
                roots.append(resolved)
        return roots

    def _extension_directory(self, extension_id: str) -> Path | None:
        for item in self._snapshot():
            if item.get("id") == extension_id:
                directory = item.get("directory")
                return Path(str(directory)) if directory else None
        return None

    @staticmethod
    def _normalize_pattern(raw: Any) -> str:
        if not isinstance(raw, str):
            raise _ApiError(E_API_PAYLOAD, "include 必须是字符串")
        pattern = raw.strip().replace("\\", "/")
        if not pattern:
            raise _ApiError(E_API_PAYLOAD, "include 不能为空")
        if pattern.startswith("/") or re.match(r"^[A-Za-z]:", pattern):
            raise _ApiError(E_PATH_OUTSIDE, f"include 必须是工作区内的相对模式：{raw}")
        if ".." in PurePosixPath(pattern).parts:
            raise _ApiError(E_PATH_OUTSIDE, f"include 不允许越出工作区：{raw}")
        return pattern

    @staticmethod
    def _normalize_excludes(raw: Any) -> list[str]:
        if isinstance(raw, (list, tuple)):
            items = list(raw)
        else:
            items = str(raw or "").split(",")
        patterns: list[str] = []
        for item in items:
            pattern = str(item).strip().replace("\\", "/")
            if pattern:
                patterns.append(pattern)
        return patterns

    @staticmethod
    def _limit(raw: Any) -> int:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return DEFAULT_MAX_RESULTS
        if value <= 0:
            return DEFAULT_MAX_RESULTS
        return min(value, MAX_RESULTS_LIMIT)

    def _workspace_find_files(
        self, extension_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        pattern = self._normalize_pattern(payload.get("include"))
        excludes = self._normalize_excludes(payload.get("exclude"))
        limit = self._limit(payload.get("maxResults"))
        files: list[str] = []
        seen: set[str] = set()
        for root in self._roots(extension_id):
            try:
                candidates = sorted(root.glob(pattern))
            except (ValueError, NotImplementedError, OSError) as exc:
                raise _ApiError(E_PATH_OUTSIDE, f"非法的 glob 模式：{exc}") from exc
            for candidate in candidates:
                try:
                    resolved = candidate.resolve()
                except OSError:
                    continue
                if not resolved.is_file() or not resolved.is_relative_to(root):
                    continue
                key = str(resolved)
                if key in seen:
                    continue
                relative = resolved.relative_to(root).as_posix()
                if any(_glob_match(relative, exclude) for exclude in excludes):
                    continue
                seen.add(key)
                files.append(key)
                if len(files) >= limit:
                    return {"files": files}
        return {"files": files}

    def _workspace_read_file(
        self, extension_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        raw = payload.get("uri") or payload.get("path")
        path = self._local_path(raw)
        roots = self._roots(extension_id)
        try:
            resolved = path.resolve()
        except OSError as exc:
            raise _ApiError(E_FILE_NOT_FOUND, f"无法解析路径：{raw}") from exc
        if not roots or not any(resolved.is_relative_to(root) for root in roots):
            raise _ApiError(E_PATH_OUTSIDE, f"路径越出工作区或扩展目录：{raw}")
        if not resolved.is_file():
            raise _ApiError(E_FILE_NOT_FOUND, f"文件不存在：{raw}")
        try:
            data = resolved.read_bytes()
        except OSError as exc:
            raise _ApiError(E_FILE_NOT_FOUND, f"读取失败：{exc}") from exc
        return {
            "uri": str(resolved),
            "size": len(data),
            "data": base64.b64encode(data).decode("ascii"),
        }

    @staticmethod
    def _local_path(raw: Any) -> Path:
        text = str(raw or "").strip()
        if not text:
            raise _ApiError(E_API_PAYLOAD, "缺少文件 uri")
        if text.lower().startswith("file://"):
            parsed = urlparse(text)
            text = unquote(parsed.path)
            if re.match(r"^/[A-Za-z]:", text):
                text = text[1:]
            if parsed.netloc:
                text = f"//{parsed.netloc}{text}"
        path = Path(text)
        if not path.is_absolute():
            raise _ApiError(E_PATH_OUTSIDE, f"文件 uri 必须是绝对路径：{raw}")
        return path

    # ---- commands / extensions ----

    def _commands_execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._commands is None:
            raise _ApiError(E_COMMAND, "宿主未接入命令注册表")
        command_id = str(
            payload.get("command") or payload.get("commandId") or payload.get("id") or ""
        )
        if not command_id:
            raise _ApiError(E_API_PAYLOAD, "缺少 command")
        args = payload.get("args") or []
        if not isinstance(args, (list, tuple)):
            args = [args]
        try:
            result = self._commands.invoke(command_id, *args)
        except Exception as exc:
            raise _ApiError(E_COMMAND, str(exc)) from exc
        return {"result": _jsonable(result)}

    def _commands_list(self) -> dict[str, Any]:
        return {"commands": self._commands.ids() if self._commands is not None else []}

    def _extensions_all(self) -> dict[str, Any]:
        return {"items": self._snapshot()}

    def _extensions_get(self, payload: dict[str, Any]) -> dict[str, Any]:
        extension_id = str(payload.get("id") or "").strip()
        if not extension_id:
            raise _ApiError(E_API_PAYLOAD, "缺少扩展 id")
        for item in self._snapshot():
            if item.get("id") == extension_id:
                return {"extension": item}
        return {"extension": None}

    def _snapshot(self) -> list[dict[str, Any]]:
        source = self._manifests() if callable(self._manifests) else self._manifests
        if source is None:
            return []
        if isinstance(source, Mapping):
            entries: list[tuple[Any, Any]] = list(source.items())
        else:
            entries = [(None, item) for item in source]
        items = [
            described
            for key, item in entries
            if (described := _describe_manifest(item, key, self._storage_root))
        ]
        items.sort(key=lambda item: str(item.get("id") or ""))
        return items
