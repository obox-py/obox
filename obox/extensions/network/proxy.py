"""网络错误与代理策略：解析设置，建立 HTTP CONNECT / SOCKS5 隧道。

代理来源只有设置页：enabled、proxyUrl、noProxy、sslStrict。
调用方只传 noProxy 表示本次强制直连，不接受代理地址参数。
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from ...api.errors import OboxError


class NetworkError(OboxError):
    """网络层可预期错误；错误码会进入消息应答。"""

    code = "E_NETWORK"


class ProxyError(NetworkError):
    code = "E_PROXY"


class UnsupportedError(NetworkError):
    code = "E_UNSUPPORTED"


_DEFAULT_PORTS = {"http": 8080, "https": 443, "socks5": 1080, "socks5h": 1080}

_SOCKS_ERRORS = {
    1: "代理内部错误",
    2: "规则不允许",
    3: "网络不可达",
    4: "主机不可达",
    5: "连接被拒绝",
    6: "TTL 过期",
    7: "不支持的命令",
    8: "不支持的地址类型",
}


@dataclass(frozen=True, slots=True)
class ProxyEndpoint:
    """解析后的代理地址。"""

    scheme: str
    host: str
    port: int

    @property
    def is_socks(self) -> bool:
        return self.scheme.startswith("socks")


@dataclass(frozen=True, slots=True)
class ProxyPolicy:
    """一次网络调用要遵守的代理策略；resolve 返回代理 URL 或 None（直连）。"""

    enabled: bool = False
    proxy_url: str = ""
    no_proxy: tuple[str, ...] = ()
    ssl_strict: bool = True

    @classmethod
    def from_settings(cls, settings: Mapping[str, Any] | None) -> ProxyPolicy:
        data: dict[str, Any] = dict(settings or {})
        nested = data.get("network")
        if isinstance(nested, Mapping):
            data = {**nested, **{key: value for key, value in data.items() if key != "network"}}
        return cls(
            enabled=_as_bool(_pick(data, "enabled", "proxyEnabled", "proxy_enabled")),
            proxy_url=str(_pick(data, "proxyUrl", "proxy_url", "proxy") or "").strip(),
            no_proxy=_as_rules(_pick(data, "noProxy", "no_proxy", "bypass")),
            ssl_strict=_as_bool(_pick(data, "sslStrict", "ssl_strict"), True),
        )

    def resolve(self, no_proxy: bool = False, host: str = "") -> str | None:
        """返回代理 URL；None 表示直连。noProxy 只对本次调用生效。"""
        if no_proxy or not self.enabled:
            return None
        if not self.proxy_url:
            raise ProxyError("已启用代理，但没有配置 proxyUrl")
        if host and self.bypasses(host):
            return None
        parse_proxy_url(self.proxy_url)
        return self.proxy_url

    def bypasses(self, host: str) -> bool:
        """命中设置里的忽略地址（支持 *、.example.com、<local>）。"""
        name = str(host or "").strip().lower().rstrip(".")
        if not name:
            return False
        for rule in self.no_proxy:
            text = rule.strip().lower()
            if not text:
                continue
            if text == "*":
                return True
            if text == "<local>":
                if "." not in name:
                    return True
                continue
            text = text.lstrip(".")
            if name == text or name.endswith("." + text):
                return True
        return False


def parse_proxy_url(url: str) -> ProxyEndpoint:
    """解析并校验代理地址；不支持的写法直接报错，不静默直连。"""
    text = str(url or "").strip()
    if not text:
        raise ProxyError("代理地址为空")
    if "://" not in text:
        raise ProxyError(f"代理地址必须以 http:// 或 socks5:// 开头：{text}")
    parts = urlsplit(text)
    scheme = parts.scheme.lower()
    if scheme not in _DEFAULT_PORTS:
        raise ProxyError(f"不支持的代理协议：{scheme}（可选 http、https、socks5）")
    host = parts.hostname or ""
    if not host:
        raise ProxyError(f"代理地址缺少主机：{text}")
    if parts.username is not None or parts.password is not None:
        raise UnsupportedError("暂不支持带用户名密码的代理")
    try:
        port = parts.port or _DEFAULT_PORTS[scheme]
    except ValueError as exc:
        raise ProxyError(f"代理端口不合法：{text}") from exc
    if not 0 < port < 65536:
        raise ProxyError(f"代理端口不合法：{port}")
    return ProxyEndpoint(scheme=scheme, host=host, port=port)


def open_tunnel(proxy_url: str, host: str, port: int, timeout: float = 30.0) -> socket.socket:
    """经代理建立到 host:port 的隧道，返回已连通的 socket。"""
    endpoint = parse_proxy_url(proxy_url)
    try:
        tunnel = socket.create_connection((endpoint.host, endpoint.port), timeout=timeout)
    except OSError as exc:
        raise ProxyError(f"连接代理 {endpoint.host}:{endpoint.port} 失败：{exc}") from exc
    try:
        tunnel.settimeout(timeout)
        if endpoint.is_socks:
            _socks5_connect(tunnel, host, int(port))
        else:
            _http_connect(tunnel, host, int(port))
    except (OSError, ProxyError) as exc:
        tunnel.close()
        if isinstance(exc, ProxyError):
            raise
        raise ProxyError(f"经代理连接 {host}:{port} 失败：{exc}") from exc
    return tunnel


def _socks5_connect(tunnel: socket.socket, host: str, port: int) -> None:
    tunnel.sendall(b"\x05\x01\x00")
    greeting = _recv_exact(tunnel, 2)
    if greeting[0] != 0x05:
        raise ProxyError("代理不是 SOCKS5 服务")
    if greeting[1] != 0x00:
        raise UnsupportedError("SOCKS5 代理要求认证，暂不支持")

    address = host.encode("idna")
    if _is_ipv4(host):
        target = b"\x01" + socket.inet_aton(host)
    elif _is_ipv6(host):
        target = b"\x04" + socket.inet_pton(socket.AF_INET6, host)
    else:
        if len(address) > 255:
            raise ProxyError(f"主机名过长：{host}")
        target = b"\x03" + bytes([len(address)]) + address

    tunnel.sendall(b"\x05\x01\x00" + target + int(port).to_bytes(2, "big"))
    reply = _recv_exact(tunnel, 4)
    if reply[0] != 0x05:
        raise ProxyError("SOCKS5 应答格式错误")
    if reply[1] != 0x00:
        reason = _SOCKS_ERRORS.get(reply[1], f"错误码 {reply[1]}")
        raise ProxyError(f"SOCKS5 连接 {host}:{port} 失败：{reason}")
    if reply[3] == 0x01:
        _recv_exact(tunnel, 4)
    elif reply[3] == 0x04:
        _recv_exact(tunnel, 16)
    elif reply[3] == 0x03:
        _recv_exact(tunnel, _recv_exact(tunnel, 1)[0])
    _recv_exact(tunnel, 2)


def _http_connect(tunnel: socket.socket, host: str, port: int) -> None:
    target = f"[{host}]:{port}" if _is_ipv6(host) else f"{host}:{port}"
    request = (
        f"CONNECT {target} HTTP/1.1\r\n"
        f"Host: {target}\r\n"
        "Proxy-Connection: keep-alive\r\n\r\n"
    ).encode("ascii")
    tunnel.sendall(request)
    head = bytearray()
    while b"\r\n\r\n" not in head:
        chunk = tunnel.recv(1)
        if not chunk:
            raise ProxyError("HTTP 代理提前关闭连接")
        head += chunk
        if len(head) > 8192:
            raise ProxyError("HTTP 代理应答过长")
    status_line = bytes(head).decode("latin-1").split("\r\n", 1)[0]
    parts = status_line.split()
    if len(parts) < 2 or not parts[1].isdigit():
        raise ProxyError(f"HTTP 代理应答非法：{status_line}")
    status = int(parts[1])
    if status != 200:
        raise ProxyError(f"HTTP 代理拒绝 CONNECT（{status}）：{status_line}")


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ProxyError("代理连接中断")
        data += chunk
    return data


def _is_ipv4(host: str) -> bool:
    try:
        ipaddress.IPv4Address(host)
    except ipaddress.AddressValueError:
        return False
    return True


def _is_ipv6(host: str) -> bool:
    try:
        ipaddress.IPv6Address(host)
    except ipaddress.AddressValueError:
        return False
    return True


def _pick(data: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "no", "off")
    return bool(value)


def _as_rules(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        items: list[Any] = value.replace(";", ",").replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return ()
    rules: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in rules:
            rules.append(text)
    return tuple(rules)
