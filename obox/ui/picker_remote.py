"""SSH 远端浏览：paramiko 客户端与后台列举线程。"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal


def local_entries(path: Path, extensions: list[str], mode: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        try:
            is_dir = item.is_dir()
            info = item.stat()
        except OSError:
            continue
        if mode == "dir" and not is_dir:
            continue
        if not is_dir and extensions and item.suffix.lower().lstrip(".") not in extensions:
            continue
        hidden = item.name.startswith(".") or bool(getattr(info, "st_file_attributes", 0) & 0x2)
        entries.append(
            {
                "name": item.name,
                "path": str(item),
                "is_dir": is_dir,
                "size": 0 if is_dir else info.st_size,
                "mtime": info.st_mtime,
                "hidden": hidden,
            }
        )
    return entries


class RemoteBrowser:
    """一条 SSH 连接上的目录浏览；连接在调用线程内建立。"""

    def __init__(self, params: dict[str, Any], trusted: set[str]) -> None:
        self.params = params
        self.trusted = trusted
        self.transport = None
        self.sftp = None
        self.fingerprint = ""

    def _connect(self):
        import paramiko

        params = self.params
        transport = paramiko.Transport((params["host"], int(params.get("port") or 22)))
        transport.start_client(timeout=10)
        host_key = transport.get_remote_server_key()
        self.fingerprint = ":".join(f"{byte:02x}" for byte in host_key.get_fingerprint())
        self._remember_host_key(host_key)
        if params.get("key_path"):
            key = paramiko.RSAKey.from_private_key_file(
                params["key_path"], password=params.get("passphrase") or None
            )
            transport.auth_publickey(params.get("user") or "", key)
        else:
            transport.auth_password(params.get("user") or "", params.get("password") or "")
        if not transport.is_authenticated():
            transport.close()
            raise PermissionError("SSH 认证失败")
        self.transport = transport
        self.sftp = paramiko.SFTPClient.from_transport(transport)

    def _remember_host_key(self, host_key) -> None:
        """把主机键写入 ~/.ssh/known_hosts，下次连接不再需要确认。"""
        import paramiko

        path = Path.home() / ".ssh" / "known_hosts"
        keys = paramiko.HostKeys()
        if path.is_file():
            try:
                keys.load(str(path))
            except (OSError, IOError):
                pass
        host = self.params["host"]
        entry = keys.lookup(host) or {}
        if entry.get(host_key.get_name()) == host_key:
            return
        keys.add(host, host_key.get_name(), host_key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            keys.save(str(path))
        except OSError:
            pass

    def home(self) -> str:
        if self.sftp is None:
            self._connect()
        return self.sftp.normalize(".")

    def list(self, path: str, extensions: list[str], mode: str) -> list[dict[str, Any]]:
        if self.sftp is None:
            self._connect()
        entries: list[dict[str, Any]] = []
        for attr in self.sftp.listdir_attr(path or "."):
            is_dir = stat.S_ISDIR(attr.st_mode or 0)
            if mode == "dir" and not is_dir:
                continue
            suffix = attr.filename.rsplit(".", 1)[-1].lower() if "." in attr.filename else ""
            if not is_dir and extensions and suffix not in extensions:
                continue
            entries.append(
                {
                    "name": attr.filename,
                    "path": path.rstrip("/") + "/" + attr.filename,
                    "is_dir": is_dir,
                    "size": 0 if is_dir else int(attr.st_size or 0),
                    "mtime": float(attr.st_mtime or 0),
                    "hidden": attr.filename.startswith("."),
                }
            )
        entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))
        return entries

    def download(self, remote_path: str, local_path: str) -> None:
        if self.sftp is None:
            self._connect()
        self.sftp.get(remote_path, local_path)

    def upload(self, local_path: str, remote_path: str) -> None:
        if self.sftp is None:
            self._connect()
        self.sftp.put(local_path, remote_path)

    def close(self) -> None:
        if self.sftp is not None:
            self.sftp.close()
            self.sftp = None
        if self.transport is not None:
            self.transport.close()
            self.transport = None


class ListWorker(QThread):
    """在后台线程里列目录，结果通过信号回主线程。"""

    done = Signal(object, str)
    failed = Signal(str, str)

    def __init__(
        self,
        params: dict[str, Any],
        path: str,
        browser: RemoteBrowser | None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._params = params
        self._path = path
        self._browser = browser

    def run(self) -> None:  # noqa: D401
        try:
            mode = self._params["mode"]
            extensions = self._params["extensions"]
            if self._params.get("ssh"):
                browser = self._browser or RemoteBrowser(self._params["ssh"], set())
                self._browser = browser
                home = browser.home()
                target = self._path or home
                self.done.emit(
                    {"path": target, "entries": browser.list(target, extensions, mode), "home": home},
                    "",
                )
            else:
                target = Path(self._path or os.path.expanduser("~"))
                self.done.emit({"path": str(target), "entries": local_entries(target, extensions, mode)}, "")
        except Exception as exc:  # 网络与权限错误统一显示
            self.failed.emit("ERROR", str(exc))