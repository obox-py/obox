"""网络命名空间：请求消息与选项类型。

扩展侧只构造消息，具体协议由宿主的 NetworkService 处理；每个函数第一个参数是 ctx。
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any

from .extensions import HOST_ID
from .message import Message

if TYPE_CHECKING:
    from ..extensions.context import OboxContext

NETWORK_REQUEST_MSG = "NETWORK_REQUEST_MSG"
NETWORK_TCP_CONNECT_MSG = "NETWORK_TCP_CONNECT_MSG"
NETWORK_TCP_SEND_MSG = "NETWORK_TCP_SEND_MSG"
NETWORK_TCP_CLOSE_MSG = "NETWORK_TCP_CLOSE_MSG"
NETWORK_UDP_SEND_MSG = "NETWORK_UDP_SEND_MSG"
NETWORK_QUIC_REQUEST_MSG = "NETWORK_QUIC_REQUEST_MSG"
NETWORK_SSH_CONNECT_MSG = "NETWORK_SSH_CONNECT_MSG"
NETWORK_SFTP_LIST_MSG = "NETWORK_SFTP_LIST_MSG"
NETWORK_PING_MSG = "NETWORK_PING_MSG"


def encode_bytes(value: bytes | bytearray | memoryview | str | None) -> tuple[str, str]:
    """把 body/data 编成 JSON 可传的文本：bytes 走 base64，str 原样。"""
    if value is None:
        return "", ""
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        if not raw:
            return "", ""
        return base64.b64encode(raw).decode("ascii"), "base64"
    text = str(value)
    if not text:
        return "", ""
    return text, "text"


def decode_bytes(text: Any, encoding: str = "") -> bytes:
    """encode_bytes 的逆操作；空值返回 b""。"""
    if not text:
        return b""
    if encoding == "base64":
        return base64.b64decode(str(text))
    return str(text).encode("utf-8")


def as_bytes(value: bytes | bytearray | memoryview | str | None) -> bytes:
    """把选项里的 body/data 统一成 bytes；文本按 UTF-8。"""
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    return str(value).encode("utf-8")


def _body_value(value: Any, encoding: str) -> bytes | str:
    """payload 里的 body/data 还原：base64 解成 bytes，文本保持 str。"""
    if not value:
        return b""
    if encoding == "base64":
        return decode_bytes(value, "base64")
    return str(value)


@dataclass
class _Options:
    """选项基类：payload 与选项对象互转，未知字段忽略。"""

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None):
        data = dict(payload or {})
        allowed = {item.name for item in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def to_payload(self) -> dict[str, Any]:
        return {item.name: getattr(self, item.name) for item in fields(self)}


@dataclass
class NetworkRequestOptions(_Options):
    """HTTP/HTTPS 请求选项；noProxy 只对本次调用强制直连。"""

    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | str | None = None
    timeout: float = 30.0
    noProxy: bool = False

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> NetworkRequestOptions:
        data = dict(payload or {})
        headers = data.get("headers")
        if not isinstance(headers, dict):
            headers = {}
        return cls(
            method=str(data.get("method") or "GET"),
            url=str(data.get("url") or ""),
            headers={str(key): str(value) for key, value in headers.items()},
            body=_body_value(data.get("body"), str(data.get("bodyEncoding") or "")),
            timeout=_as_float(data.get("timeout"), 30.0),
            noProxy=bool(data.get("noProxy")),
        )

    def to_payload(self) -> dict[str, Any]:
        text, encoding = encode_bytes(self.body)
        return {
            "method": self.method,
            "url": self.url,
            "headers": dict(self.headers),
            "body": text,
            "bodyEncoding": encoding,
            "timeout": float(self.timeout),
            "noProxy": bool(self.noProxy),
        }


@dataclass
class TcpConnectOptions(_Options):
    host: str = ""
    port: int = 0
    timeout: float = 30.0
    noProxy: bool = False


@dataclass
class TcpSendOptions(_Options):
    connectionId: str = ""
    data: bytes | str | None = None
    timeout: float = 5.0

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> TcpSendOptions:
        data = dict(payload or {})
        return cls(
            connectionId=str(data.get("connectionId") or ""),
            data=_body_value(data.get("data"), str(data.get("dataEncoding") or "")),
            timeout=_as_float(data.get("timeout"), 5.0),
        )

    def to_payload(self) -> dict[str, Any]:
        text, encoding = encode_bytes(self.data)
        return {
            "connectionId": self.connectionId,
            "data": text,
            "dataEncoding": encoding,
            "timeout": float(self.timeout),
        }


@dataclass
class TcpCloseOptions(_Options):
    connectionId: str = ""


@dataclass
class UdpSendOptions(_Options):
    host: str = ""
    port: int = 0
    data: bytes | str | None = None
    timeout: float = 5.0
    expectReply: bool = False
    noProxy: bool = False

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> UdpSendOptions:
        data = dict(payload or {})
        return cls(
            host=str(data.get("host") or ""),
            port=_as_int(data.get("port"), 0),
            data=_body_value(data.get("data"), str(data.get("dataEncoding") or "")),
            timeout=_as_float(data.get("timeout"), 5.0),
            expectReply=bool(data.get("expectReply")),
            noProxy=bool(data.get("noProxy")),
        )

    def to_payload(self) -> dict[str, Any]:
        text, encoding = encode_bytes(self.data)
        return {
            "host": self.host,
            "port": int(self.port),
            "data": text,
            "dataEncoding": encoding,
            "timeout": float(self.timeout),
            "expectReply": bool(self.expectReply),
            "noProxy": bool(self.noProxy),
        }


@dataclass
class QuicRequestOptions(_Options):
    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | str | None = None
    timeout: float = 30.0
    noProxy: bool = False

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> QuicRequestOptions:
        data = dict(payload or {})
        headers = data.get("headers")
        if not isinstance(headers, dict):
            headers = {}
        return cls(
            method=str(data.get("method") or "GET"),
            url=str(data.get("url") or ""),
            headers={str(key): str(value) for key, value in headers.items()},
            body=_body_value(data.get("body"), str(data.get("bodyEncoding") or "")),
            timeout=_as_float(data.get("timeout"), 30.0),
            noProxy=bool(data.get("noProxy")),
        )

    def to_payload(self) -> dict[str, Any]:
        text, encoding = encode_bytes(self.body)
        return {
            "method": self.method,
            "url": self.url,
            "headers": dict(self.headers),
            "body": text,
            "bodyEncoding": encoding,
            "timeout": float(self.timeout),
            "noProxy": bool(self.noProxy),
        }


@dataclass
class SshConnectOptions(_Options):
    host: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    keyPath: str = ""
    passphrase: str = ""
    command: str = ""
    timeout: float = 30.0
    noProxy: bool = False


@dataclass
class SftpListOptions(SshConnectOptions):
    """指定 sessionId 复用会话；否则用 host 等字段新建一次性会话。"""

    path: str = "."
    sessionId: str = ""


@dataclass
class PingOptions(_Options):
    timeout: float = 2.0
    count: int = 1
    noProxy: bool = False


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _options(cls: type[_Options], value: Any) -> _Options:
    if isinstance(value, cls):
        return value
    if value is None or isinstance(value, Mapping):
        return cls.from_payload(value)
    raise TypeError(f"{cls.__name__} 需要 {cls.__name__} 或 dict，收到 {type(value).__name__}")


def _network_message(ctx: OboxContext, msg_id: str, payload: dict[str, Any]) -> Message:
    return Message(src=ctx.extension_id, dst=HOST_ID, msg_id=msg_id, payload=payload)


def request(ctx: OboxContext, options: NetworkRequestOptions | Mapping[str, Any] | None = None) -> Message:
    """HTTP/HTTPS 请求，返回 {"status", "headers", "body"}。"""
    return _network_message(ctx, NETWORK_REQUEST_MSG, _options(NetworkRequestOptions, options).to_payload())


def tcpConnect(ctx: OboxContext, options: TcpConnectOptions | Mapping[str, Any] | None = None) -> Message:
    """建立 TCP 连接，返回 {"connectionId", "connected"}。"""
    return _network_message(ctx, NETWORK_TCP_CONNECT_MSG, _options(TcpConnectOptions, options).to_payload())


def tcpSend(ctx: OboxContext, options: TcpSendOptions | Mapping[str, Any] | None = None) -> Message:
    """发送并取回已缓冲数据；data 为空表示只读取。"""
    return _network_message(ctx, NETWORK_TCP_SEND_MSG, _options(TcpSendOptions, options).to_payload())


def tcpClose(ctx: OboxContext, options: TcpCloseOptions | Mapping[str, Any] | None = None) -> Message:
    """关闭 TCP 连接。"""
    return _network_message(ctx, NETWORK_TCP_CLOSE_MSG, _options(TcpCloseOptions, options).to_payload())


def udpSend(ctx: OboxContext, options: UdpSendOptions | Mapping[str, Any] | None = None) -> Message:
    """发送 UDP 数据报，返回 {"bytes", "reply"}。"""
    return _network_message(ctx, NETWORK_UDP_SEND_MSG, _options(UdpSendOptions, options).to_payload())


def quicRequest(ctx: OboxContext, options: QuicRequestOptions | Mapping[str, Any] | None = None) -> Message:
    """QUIC/HTTP3 请求，返回 {"status", "headers", "body"}。"""
    return _network_message(ctx, NETWORK_QUIC_REQUEST_MSG, _options(QuicRequestOptions, options).to_payload())


def sshConnect(ctx: OboxContext, options: SshConnectOptions | Mapping[str, Any] | None = None) -> Message:
    """SSH 连接，返回 {"sessionId"}；options.command 可顺带执行一条命令。"""
    return _network_message(ctx, NETWORK_SSH_CONNECT_MSG, _options(SshConnectOptions, options).to_payload())


def sftpList(ctx: OboxContext, options: SftpListOptions | Mapping[str, Any] | None = None) -> Message:
    """列远端目录，返回 {"items": [...]}。"""
    return _network_message(ctx, NETWORK_SFTP_LIST_MSG, _options(SftpListOptions, options).to_payload())


def ping(ctx: OboxContext, host: str, options: PingOptions | Mapping[str, Any] | None = None) -> Message:
    """系统 ping，返回 {"alive", "timeMs"}。"""
    payload = {"host": str(host or ""), **_options(PingOptions, options).to_payload()}
    return _network_message(ctx, NETWORK_PING_MSG, payload)
