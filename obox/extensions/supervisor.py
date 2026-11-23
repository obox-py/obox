"""obox 侧的宿主进程管理与重启。"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from ..core.ipc.server import IpcServer

def _frozen() -> bool:
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return True
    return not sys.executable.lower().endswith(("python.exe", "pythonw.exe"))


_IS_FROZEN = _frozen()


def _debug(message: str) -> None:
    path = os.environ.get("OBOX_DEBUG_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass

_RESTART_DELAYS_MS = (500, 1000, 2000, 5000)


class Supervisor(QObject):
    """拉起宿主、握手、监控崩溃并指数退避重启。"""

    state_changed = Signal(str, str)
    extensions_ready = Signal(dict)

    def __init__(
        self,
        project_root: Path,
        bus: Any,
        extensions_root: Path | None = None,
        parent: QObject | None = None,
        data_dir: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self._root = project_root
        self._bus = bus
        self._extensions_dir = extensions_root or project_root / "extensions"
        self._data_dir = data_dir or project_root / ".obox"
        self._storage_dir = self._data_dir / "storage"
        self._token = uuid.uuid4().hex
        self._pipe_name = f"obox-{uuid.uuid4().hex[:12]}"
        self._server: IpcServer | None = None
        self._process: QProcess | None = None
        self._restarts = 0
        self._stopping = False

    @property
    def pipe_name(self) -> str:
        return self._pipe_name

    def start(self) -> None:
        self._server = IpcServer(self._token, self)
        self._server.listen(self._pipe_name)
        self._bus.attach_transport(self._server)
        self._server.frame_received.connect(self._on_frame)
        self._server.client_disconnected.connect(self._on_client_disconnected)
        self._spawn()

    def restart(self) -> None:
        """扩展目录变化时重启宿主，触发重新激活与列表推送。"""
        self.stop()
        self._restarts = 0
        self.start()

    def stop(self) -> None:
        self._stopping = True
        if self._server is not None and self._server.connected:
            try:
                self._server.send({"type": "shutdown"})
            except Exception:
                pass
        if self._process is not None:
            self._process.terminate()
            if not self._process.waitForFinished(2000):
                self._process.kill()
                self._process.waitForFinished(2000)
            self._process = None
        if self._server is not None:
            self._server.close()
            self._server = None

    def invoke_command(self, command_id: str) -> None:
        if self._server is not None and self._server.connected:
            self._server.send({"type": "command", "command": command_id})

    def _spawn(self) -> None:
        process = QProcess(self)
        program = sys.executable
        if _IS_FROZEN:
            candidate = self._root / "obox.exe"
            if candidate.is_file():
                program = str(candidate)
        process.setProgram(program)
        host_prefix = ["--extension-host"] if _IS_FROZEN else ["-m", "obox.extensions.host"]
        process.setArguments(
            [
                *host_prefix,
                "--pipe",
                self._pipe_name,
                "--token",
                self._token,
                "--extensions-dir",
                str(self._extensions_dir),
                "--system-dir",
                str(self._root / "extensions"),
                "--install-dir",
                str(self._data_dir / "extensions"),
                "--storage-dir",
                str(self._storage_dir),
            ]
        )
        _debug(f"spawn frozen={_IS_FROZEN} cmd={program} args={process.arguments()}")
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.errorOccurred.connect(lambda error: _debug(f"process error {error}"))
        process.readyReadStandardOutput.connect(lambda: self._drain(process))
        process.finished.connect(self._on_finished)
        self._process = process
        process.start()
        self.state_changed.emit("starting", "正在启动扩展宿主")

    def _drain(self, process: QProcess) -> None:
        text = bytes(process.readAllStandardOutput()).decode("utf-8", "replace").strip()
        if text:
            _debug(f"[host] {text}")
            print(f"[host] {text}", file=sys.stderr)

    def _on_frame(self, frame: dict[str, Any]) -> None:
        if "type" not in frame:
            self._bus.receive(frame)
            return
        if frame["type"] == "status":
            self._restarts = 0
            self.state_changed.emit("ready", "扩展宿主已就绪")
            self.extensions_ready.emit(frame)

    def _on_client_disconnected(self) -> None:
        if not self._stopping:
            self.state_changed.emit("disconnected", "扩展宿主连接断开")

    def _on_finished(self, code: int, status: Any) -> None:
        if self._stopping:
            return
        delay = _RESTART_DELAYS_MS[min(self._restarts, len(_RESTART_DELAYS_MS) - 1)]
        self._restarts += 1
        _debug(f"host finished code={code} status={status}")
        self.state_changed.emit("restarting", f"扩展宿主退出（{code}），{delay} 毫秒后重启")
        QTimer.singleShot(delay, self._spawn)
