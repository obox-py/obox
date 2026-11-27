"""宿主侧网络服务：把 NETWORK_* 消息分派到各协议实现。

代理策略集中在本包 proxy.py：每次调用按当前设置解析，调用参数里的 noProxy
只对本次调用生效；UDP/QUIC 的 SOCKS5 UDP associate 未实现，代理下明确报错。
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from ...api import network as network_api
from ...api.message import Message
from . import http, icmp, quic, ssh_sftp, tcpudp
from .proxy import NetworkError, ProxyPolicy, UnsupportedError

Handler = Callable[[dict[str, Any]], dict[str, Any]]

__all__ = [
    "NetworkError",
    "NetworkService",
    "ProxyEndpoint",
    "ProxyError",
    "ProxyPolicy",
    "UnsupportedError",
]


class NetworkService:
    """网络消息处理器；连接与会话按 id 持有，进程退出前调用 close()。"""

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self._settings: dict[str, Any] = {}
        self._connections: dict[str, tcpudp.TcpConnection] = {}
        self._sessions: dict[str, ssh_sftp.SshSession] = {}
        self._handlers: dict[str, Handler] = {
            network_api.NETWORK_REQUEST_MSG: self._request,
            network_api.NETWORK_TCP_CONNECT_MSG: self._tcp_connect,
            network_api.NETWORK_TCP_SEND_MSG: self._tcp_send,
            network_api.NETWORK_TCP_CLOSE_MSG: self._tcp_close,
            network_api.NETWORK_UDP_SEND_MSG: self._udp_send,
            network_api.NETWORK_QUIC_REQUEST_MSG: self._quic_request,
            network_api.NETWORK_SSH_CONNECT_MSG: self._ssh_connect,
            network_api.NETWORK_SFTP_LIST_MSG: self._sftp_list,
            network_api.NETWORK_PING_MSG: self._ping,
        }
        self.update_settings(settings)

    def update_settings(self, settings: dict[str, Any] | None) -> None:
        """主进程配置变化时推送；下一次调用立即生效。"""
        self._settings = dict(settings or {})

    @property
    def policy(self) -> ProxyPolicy:
        return ProxyPolicy.from_settings(self._settings)

    def handle(self, message: Message) -> dict[str, Any]:
        """处理一条网络消息；可预期错误转成 {"error", "message"} 应答。"""
        handler = self._handlers.get(message.msg_id)
        try:
            if handler is None:
                raise NetworkError(f"未知网络消息：{message.msg_id}")
            return handler(dict(message.payload or {}))
        except (NetworkError, OSError, TimeoutError, ValueError, TypeError) as exc:
            return {"error": getattr(exc, "code", "E_NETWORK"), "message": str(exc)}

    def close(self) -> None:
        for connection in self._connections.values():
            connection.close()
        self._connections.clear()
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.NetworkRequestOptions.from_payload(payload)
        policy = self.policy
        proxy_url = policy.resolve(bool(options.noProxy), _url_host(options.url))
        result = http.request(
            options.url,
            method=options.method,
            headers=options.headers,
            body=network_api.as_bytes(options.body),
            timeout=float(options.timeout),
            proxy_url=proxy_url,
            ssl_strict=policy.ssl_strict,
        )
        return _body_payload(result)

    def _tcp_connect(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.TcpConnectOptions.from_payload(payload)
        policy = self.policy
        proxy_url = policy.resolve(bool(options.noProxy), options.host)
        connection = tcpudp.connect(
            options.host,
            int(options.port),
            float(options.timeout),
            proxy_url,
        )
        connection_id = uuid.uuid4().hex
        self._connections[connection_id] = connection
        return {
            "connectionId": connection_id,
            "connected": True,
            "host": connection.host,
            "port": connection.port,
            "proxy": connection.proxy,
        }

    def _tcp_send(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.TcpSendOptions.from_payload(payload)
        connection = self._connections.get(options.connectionId)
        if connection is None:
            raise NetworkError(f"未知 TCP 连接：{options.connectionId}")
        result = connection.send(
            network_api.as_bytes(options.data),
            float(options.timeout),
        )
        return _body_payload(result, "received", "receivedEncoding")

    def _tcp_close(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.TcpCloseOptions.from_payload(payload)
        connection = self._connections.pop(options.connectionId, None)
        if connection is None:
            raise NetworkError(f"未知 TCP 连接：{options.connectionId}")
        connection.close()
        return {"closed": True}

    def _udp_send(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.UdpSendOptions.from_payload(payload)
        policy = self.policy
        if policy.resolve(bool(options.noProxy), options.host):
            raise UnsupportedError(
                "UDP 代理需要 SOCKS5 UDP associate，当前未实现；"
                "请对本次调用传 noProxy=True 或关闭代理"
            )
        result = tcpudp.udp_send(
            options.host,
            int(options.port),
            network_api.as_bytes(options.data),
            float(options.timeout),
            bool(options.expectReply),
        )
        return _body_payload(result, "reply", "replyEncoding")

    def _quic_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.QuicRequestOptions.from_payload(payload)
        policy = self.policy
        if policy.resolve(bool(options.noProxy), _url_host(options.url)):
            raise UnsupportedError(
                "QUIC 代理需要 SOCKS5 UDP associate，当前未实现；"
                "请对本次调用传 noProxy=True 或关闭代理"
            )
        result = quic.request(
            options.url,
            method=options.method,
            headers=options.headers,
            body=network_api.as_bytes(options.body),
            timeout=float(options.timeout),
            ssl_strict=policy.ssl_strict,
        )
        return _body_payload(result)

    def _ssh_connect(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.SshConnectOptions.from_payload(payload)
        policy = self.policy
        proxy_url = policy.resolve(bool(options.noProxy), options.host)
        session = ssh_sftp.connect(
            options.host,
            port=int(options.port),
            username=options.username,
            password=options.password,
            key_path=options.keyPath,
            passphrase=options.passphrase,
            timeout=float(options.timeout),
            proxy_url=proxy_url,
        )
        session_id = uuid.uuid4().hex
        self._sessions[session_id] = session
        result: dict[str, Any] = {
            "sessionId": session_id,
            "connected": True,
            "host": session.host,
            "port": session.port,
            "proxy": session.proxy,
        }
        if options.command:
            result.update(session.exec(options.command, float(options.timeout)))
        return result

    def _sftp_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = network_api.SftpListOptions.from_payload(payload)
        session = self._sessions.get(options.sessionId) if options.sessionId else None
        if options.sessionId and session is None:
            raise NetworkError(f"未知 SSH 会话：{options.sessionId}")
        if session is None and not options.host:
            raise NetworkError("sftpList 需要 sessionId 或 host")
        if session is None:
            policy = self.policy
            proxy_url = policy.resolve(bool(options.noProxy), options.host)
            session = ssh_sftp.connect(
                options.host,
                port=int(options.port),
                username=options.username,
                password=options.password,
                key_path=options.keyPath,
                passphrase=options.passphrase,
                timeout=float(options.timeout),
                proxy_url=proxy_url,
            )
            try:
                items = session.listdir(options.path, float(options.timeout))
            finally:
                session.close()
        else:
            items = session.listdir(options.path, float(options.timeout))
        return {"items": items}

    def _ping(self, payload: dict[str, Any]) -> dict[str, Any]:
        host = str(payload.get("host") or "").strip()
        if not host:
            raise NetworkError("ping 需要 host")
        options = network_api.PingOptions.from_payload(payload)
        policy = self.policy
        if policy.resolve(bool(options.noProxy), host):
            raise UnsupportedError(
                "ICMP 只能直连：已启用代理，请对本次调用传 noProxy=True 或关闭代理"
            )
        return icmp.ping(host, float(options.timeout), int(options.count))


def _url_host(url: str) -> str:
    try:
        return urlsplit(str(url or "")).hostname or ""
    except ValueError:
        return ""


def _body_payload(
    result: dict[str, Any],
    key: str = "body",
    encoding_key: str = "",
) -> dict[str, Any]:
    """把 bytes 结果转成 JSON 可传的 base64 文本。"""
    payload = dict(result)
    text, encoding = network_api.encode_bytes(payload.pop(key, b""))
    payload[key] = text
    payload[encoding_key or f"{key}Encoding"] = encoding
    return payload
