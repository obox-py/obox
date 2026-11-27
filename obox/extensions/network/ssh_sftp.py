"""SSH/SFTP：paramiko 会话，支持密码或私钥、exec 与 listdir。"""

from __future__ import annotations

import contextlib
import posixpath
import socket
import stat
from dataclasses import dataclass
from typing import Any

from .proxy import NetworkError, open_tunnel


def _paramiko() -> Any:
    try:
        import paramiko
    except ImportError as exc:
        raise NetworkError("SSH/SFTP 需要 paramiko：uv add paramiko") from exc
    return paramiko


@dataclass
class SshSession:
    """一条 SSH 会话；凭据只留在 paramiko 客户端里。"""

    client: Any
    host: str
    port: int
    proxy: bool = False

    def exec(self, command: str, timeout: float = 30.0) -> dict[str, Any]:
        """执行一条命令，返回 stdout/stderr/exitStatus。"""
        if not str(command or "").strip():
            raise NetworkError("SSH exec 需要 command")
        try:
            _, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            status = stdout.channel.recv_exit_status()
        except NetworkError:
            raise
        except Exception as exc:
            raise NetworkError(f"SSH 执行失败：{exc}") from exc
        return {"stdout": out, "stderr": err, "exitStatus": int(status)}

    def listdir(self, path: str = ".", timeout: float = 30.0) -> list[dict[str, Any]]:
        """列远端目录，返回 name/path/size/mode/mtime/isDir。"""
        remote = str(path or ".").strip() or "."
        try:
            sftp = self.client.open_sftp()
        except Exception as exc:
            raise NetworkError(f"SFTP 打开失败：{exc}") from exc
        try:
            channel = sftp.get_channel()
            if channel is not None and timeout > 0:
                channel.settimeout(float(timeout))
            attributes = sftp.listdir_attr(remote)
        except NetworkError:
            raise
        except Exception as exc:
            raise NetworkError(f"SFTP 列目录 {remote} 失败：{exc}") from exc
        finally:
            _close_quietly(sftp)
        items: list[dict[str, Any]] = []
        for item in attributes:
            mode = int(item.st_mode or 0)
            items.append(
                {
                    "name": item.filename,
                    "path": posixpath.join(remote, item.filename),
                    "size": int(item.st_size or 0),
                    "mode": mode,
                    "mtime": int(item.st_mtime or 0),
                    "isDir": stat.S_ISDIR(mode),
                }
            )
        return items

    def close(self) -> None:
        _close_quietly(self.client)


def connect(
    host: str,
    port: int = 22,
    username: str = "",
    password: str = "",
    key_path: str = "",
    passphrase: str = "",
    timeout: float = 30.0,
    proxy_url: str | None = None,
) -> SshSession:
    """建立 SSH 会话；给了 proxy_url 就走代理隧道。"""
    paramiko = _paramiko()
    target = str(host or "").strip()
    if not target:
        raise NetworkError("SSH 需要 host")
    try:
        target_port = int(port)
    except (TypeError, ValueError) as exc:
        raise NetworkError(f"SSH 端口不合法：{port}") from exc
    if not 0 < target_port < 65536:
        raise NetworkError(f"SSH 端口不合法：{port}")
    timeout = max(0.1, float(timeout))

    sock: socket.socket | None = None
    if proxy_url:
        sock = open_tunnel(proxy_url, target, target_port, timeout)
    else:
        try:
            sock = socket.create_connection((target, target_port), timeout=timeout)
            sock.settimeout(timeout)
        except OSError as exc:
            raise NetworkError(f"SSH 连接 {target}:{target_port} 失败：{exc}") from exc

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=target,
            port=target_port,
            username=username or None,
            password=password or None,
            key_filename=str(key_path) if key_path else None,
            passphrase=passphrase or None,
            sock=sock,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
    except Exception as exc:
        _close_quietly(client)
        if sock is not None:
            _close_quietly(sock)
        raise NetworkError(f"SSH 连接 {target}:{target_port} 失败：{exc}") from exc
    return SshSession(client=client, host=target, port=target_port, proxy=bool(proxy_url))


def _close_quietly(resource: Any) -> None:
    with contextlib.suppress(Exception):
        resource.close()
