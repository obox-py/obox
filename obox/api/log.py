"""log 命名空间：输出通道（面板消息 + 扩展日志文件）。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TextIO

from .message import OB_BOX, send

LOG_CREATE_MSG = "LOG_CREATE_MSG"
LOG_APPEND_MSG = "LOG_APPEND_MSG"
LOG_SHOW_MSG = "LOG_SHOW_MSG"
LOG_DISPOSE_MSG = "LOG_DISPOSE_MSG"

LEVELS = ("trace", "debug", "info", "warn", "error")
_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _log_dir(ctx: Any) -> Path | None:
    for attribute in ("log_dir", "log_uri"):
        value = getattr(ctx, attribute, None)
        if value:
            return Path(value)
    for attribute in ("storage_dir", "storage_uri"):
        value = getattr(ctx, attribute, None)
        if value:
            return Path(value) / "logs"
    return None


def _file_name(name: str) -> str:
    safe = _INVALID_FILENAME.sub("_", str(name)).strip(" .")
    return safe or "output"


def _format(message: Any, args: tuple[Any, ...]) -> str:
    if not args:
        return str(message)
    try:
        return str(message) % args
    except (TypeError, ValueError):
        return " ".join([str(message), *(str(item) for item in args)])


class LogOutputChannel:
    """一个命名输出通道；写法与 VS Code 的 OutputChannel 一致。"""

    def __init__(self, ctx: Any, name: str, options: dict[str, Any] | None = None) -> None:
        self._ctx = ctx
        self.name = str(name)
        self.options = dict(options or {})
        self._handle: TextIO | None = None
        self._disposed = False
        self._file_error = False
        directory = _log_dir(ctx)
        self._path: Path | None = (
            (directory / f"{_file_name(name)}.log") if directory is not None else None
        )
        self._notify(LOG_CREATE_MSG, {"name": self.name, "options": self.options})

    @property
    def path(self) -> Path | None:
        return self._path

    def _notify(self, message_id: str, payload: dict[str, Any]) -> None:
        if self._disposed:
            return
        try:
            send(self._ctx, OB_BOX, message_id, payload)
        except (AttributeError, ConnectionError, OSError):
            pass

    def _open(self) -> TextIO | None:
        if self._handle is not None or self._file_error or self._disposed:
            return self._handle
        if self._path is None:
            self._file_error = True
            return None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self._path.open("a", encoding="utf-8")
        except OSError:
            self._file_error = True
        return self._handle

    def _write(self, text: str) -> None:
        if self._disposed:
            return
        handle = self._open()
        if handle is not None:
            try:
                handle.write(text)
                handle.flush()
            except OSError:
                self._file_error = True

    def append(self, value: str) -> None:
        self._write(str(value))
        self._notify(
            LOG_APPEND_MSG,
            {"name": self.name, "text": str(value), "level": "", "line": False},
        )

    def appendLine(self, value: str) -> None:
        self._write(f"{value}\n")
        self._notify(
            LOG_APPEND_MSG,
            {"name": self.name, "text": str(value), "level": "", "line": True},
        )

    def show(self, preserveFocus: bool = False) -> None:
        self._notify(
            LOG_SHOW_MSG,
            {"name": self.name, "preserveFocus": bool(preserveFocus)},
        )

    def _log(self, level: str, message: Any, args: tuple[Any, ...]) -> None:
        text = _format(message, args)
        self._write(f"[{level}] {text}\n")
        self._notify(
            LOG_APPEND_MSG,
            {"name": self.name, "text": text, "level": level, "line": True},
        )

    def trace(self, message: Any, *args: Any) -> None:
        self._log("trace", message, args)

    def debug(self, message: Any, *args: Any) -> None:
        self._log("debug", message, args)

    def info(self, message: Any, *args: Any) -> None:
        self._log("info", message, args)

    def warn(self, message: Any, *args: Any) -> None:
        self._log("warn", message, args)

    def error(self, message: Any, *args: Any) -> None:
        self._log("error", message, args)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._notify(LOG_DISPOSE_MSG, {"name": self.name})
        self._disposed = True
        if self._handle is not None:
            try:
                self._handle.close()
            except OSError:
                pass
            self._handle = None

    def __call__(self) -> None:
        self.dispose()


def createOutputChannel(
    ctx: Any, name: str, options: dict[str, Any] | None = None
) -> LogOutputChannel:
    return LogOutputChannel(ctx, name, options)
