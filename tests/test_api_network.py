"""network 命名空间：消息构造、代理解析、ICMP/UDP/HTTP/TCP 本地回环。"""

from __future__ import annotations

import base64
import contextlib
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from obox.api import network as api
from obox.api.message import Message
from obox.extensions.network import NetworkService, quic
from obox.extensions.network.proxy import ProxyError, ProxyPolicy, UnsupportedError

CTX = SimpleNamespace(extension_id="demo.obox")


# ---------- 代理解析 ----------


def test_policy_reads_camel_case_settings() -> None:
    policy = ProxyPolicy.from_settings(
        {
            "enabled": True,
            "proxyUrl": "socks5://127.0.0.1:1080",
            "noProxy": ["localhost", ".internal.example", "<local>"],
            "sslStrict": False,
        }
    )
    assert policy.enabled is True
    assert policy.proxy_url == "socks5://127.0.0.1:1080"
    assert policy.no_proxy == ("localhost", ".internal.example", "<local>")
    assert policy.ssl_strict is False
    assert policy.resolve() == "socks5://127.0.0.1:1080"


def test_policy_defaults_to_direct_and_strict() -> None:
    policy = ProxyPolicy.from_settings({})
    assert policy.enabled is False
    assert policy.ssl_strict is True
    assert policy.resolve() is None


def test_policy_reads_nested_network_section() -> None:
    policy = ProxyPolicy.from_settings(
        {"network": {"enabled": True, "proxyUrl": "http://127.0.0.1:7890"}}
    )
    assert policy.enabled is True
    assert policy.resolve() == "http://127.0.0.1:7890"


def test_policy_no_proxy_flag_forces_direct() -> None:
    policy = ProxyPolicy.from_settings({"enabled": True, "proxyUrl": "http://127.0.0.1:7890"})
    assert policy.resolve(no_proxy=True) is None


def test_policy_bypasses_matching_hosts() -> None:
    policy = ProxyPolicy.from_settings(
        {
            "enabled": True,
            "proxyUrl": "http://127.0.0.1:7890",
            "noProxy": ["localhost", ".internal.example", "<local>"],
        }
    )
    assert policy.resolve(host="localhost") is None
    assert policy.resolve(host="api.internal.example") is None
    assert policy.resolve(host="intranet") is None  # <local> 命中无点主机
    assert policy.resolve(host="example.com") == "http://127.0.0.1:7890"


def test_policy_requires_url_when_enabled() -> None:
    policy = ProxyPolicy.from_settings({"enabled": True})
    with pytest.raises(ProxyError):
        policy.resolve()


def test_policy_rejects_unknown_scheme() -> None:
    policy = ProxyPolicy.from_settings({"enabled": True, "proxyUrl": "ftp://127.0.0.1:21"})
    with pytest.raises(ProxyError):
        policy.resolve()


def test_policy_rejects_credentials() -> None:
    policy = ProxyPolicy.from_settings({"enabled": True, "proxyUrl": "socks5://u:p@127.0.0.1:1080"})
    with pytest.raises(UnsupportedError):
        policy.resolve()


# ---------- 消息构造 ----------


def test_request_message_encodes_bytes_body() -> None:
    message = api.request(
        CTX,
        api.NetworkRequestOptions(
            method="POST",
            url="https://example.com/api",
            headers={"X-Test": "1"},
            body=b"\x00\x01",
            timeout=5,
            noProxy=True,
        ),
    )
    assert isinstance(message, Message)
    assert message.src == "demo.obox"
    assert message.dst == "host.obox"
    assert message.msg_id == api.NETWORK_REQUEST_MSG
    payload = message.payload
    assert payload["method"] == "POST"
    assert payload["url"] == "https://example.com/api"
    assert payload["headers"] == {"X-Test": "1"}
    assert payload["body"] == base64.b64encode(b"\x00\x01").decode("ascii")
    assert payload["bodyEncoding"] == "base64"
    assert payload["noProxy"] is True
    options = api.NetworkRequestOptions.from_payload(payload)
    assert options.body == b"\x00\x01"


def test_request_accepts_plain_dict() -> None:
    message = api.request(CTX, {"url": "https://example.com", "body": "hello"})
    assert message.payload["body"] == "hello"
    assert message.payload["bodyEncoding"] == "text"


def test_ping_message_carries_host_and_options() -> None:
    message = api.ping(CTX, "example.com", {"timeout": 1, "count": 2, "noProxy": True})
    assert message.msg_id == api.NETWORK_PING_MSG
    assert message.payload == {
        "host": "example.com",
        "timeout": 1.0,
        "count": 2,
        "noProxy": True,
    }


def test_every_namespace_message_has_constructor() -> None:
    cases = [
        (api.tcpConnect, api.NETWORK_TCP_CONNECT_MSG, {"host": "127.0.0.1", "port": 22}),
        (api.tcpSend, api.NETWORK_TCP_SEND_MSG, {"connectionId": "a", "data": "x"}),
        (api.tcpClose, api.NETWORK_TCP_CLOSE_MSG, {"connectionId": "a"}),
        (api.udpSend, api.NETWORK_UDP_SEND_MSG, {"host": "127.0.0.1", "port": 9, "data": "x"}),
        (api.quicRequest, api.NETWORK_QUIC_REQUEST_MSG, {"url": "https://example.com"}),
        (api.sshConnect, api.NETWORK_SSH_CONNECT_MSG, {"host": "example.com"}),
        (api.sftpList, api.NETWORK_SFTP_LIST_MSG, {"sessionId": "s", "path": "/tmp"}),
    ]
    for constructor, msg_id, options in cases:
        message = constructor(CTX, options)
        assert message.msg_id == msg_id
        assert message.src == "demo.obox"
        assert message.dst == "host.obox"


# ---------- 代理下的明确拒绝 ----------


def test_ping_under_proxy_reports_unsupported() -> None:
    service = NetworkService({"enabled": True, "proxyUrl": "http://127.0.0.1:7890"})
    reply = service.handle(api.ping(CTX, "127.0.0.1"))
    assert reply["error"] == "E_UNSUPPORTED"
    assert "ICMP" in reply["message"]
    assert "noProxy" in reply["message"]


def test_udp_under_proxy_reports_unsupported() -> None:
    service = NetworkService({"enabled": True, "proxyUrl": "socks5://127.0.0.1:1080"})
    reply = service.handle(api.udpSend(CTX, {"host": "127.0.0.1", "port": 9, "data": "x"}))
    assert reply["error"] == "E_UNSUPPORTED"
    assert "SOCKS5 UDP" in reply["message"]


def test_unknown_message_reports_error() -> None:
    service = NetworkService()
    reply = service.handle(Message(src="demo.obox", dst="host.obox", msg_id="NETWORK_NOPE_MSG"))
    assert reply["error"] == "E_NETWORK"


def test_unknown_tcp_connection_reports_error() -> None:
    service = NetworkService()
    reply = service.handle(api.tcpSend(CTX, {"connectionId": "missing", "data": "x"}))
    assert reply["error"] == "E_NETWORK"
    assert "未知 TCP 连接" in reply["message"]


def test_unknown_sftp_session_reports_error() -> None:
    service = NetworkService()
    reply = service.handle(api.sftpList(CTX, {"sessionId": "missing"}))
    assert reply["error"] == "E_NETWORK"
    assert "未知 SSH 会话" in reply["message"]


def test_settings_update_applies_to_next_call() -> None:
    service = NetworkService()
    assert service.policy.enabled is False
    service.update_settings({"enabled": True, "proxyUrl": "http://127.0.0.1:7890"})
    assert service.policy.enabled is True
    assert service.policy.ssl_strict is True


@pytest.mark.skipif(quic.available(), reason="aioquic 已安装，走真实 QUIC 路径")
def test_quic_reports_missing_dependency() -> None:
    service = NetworkService()
    reply = service.handle(api.quicRequest(CTX, {"url": "https://example.com"}))
    assert reply["error"] == "E_NETWORK"
    assert "aioquic" in reply["message"]


# ---------- 本地回环 ----------


def test_udp_round_trip(qapp: object) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    server.settimeout(5)
    port = server.getsockname()[1]

    def echo() -> None:
        try:
            data, address = server.recvfrom(2048)
            server.sendto(b"pong:" + data, address)
        finally:
            server.close()

    thread = threading.Thread(target=echo, daemon=True)
    thread.start()
    service = NetworkService()
    try:
        reply = service.handle(
            api.udpSend(
                CTX,
                {
                    "host": "127.0.0.1",
                    "port": port,
                    "data": "ping",
                    "timeout": 5,
                    "expectReply": True,
                },
            )
        )
    finally:
        service.close()
        thread.join(5)
    assert "error" not in reply, reply
    assert reply["bytes"] == 4
    assert base64.b64decode(reply["reply"]) == b"pong:ping"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        payload = b"hello-network"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Network-Test", "ok")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        pass


def test_http_get_round_trip(qapp: object) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    service = NetworkService()
    try:
        reply = service.handle(
            api.request(CTX, {"url": f"http://127.0.0.1:{port}/hello", "timeout": 5})
        )
    finally:
        service.close()
        server.shutdown()
        server.server_close()
        thread.join(5)
    assert "error" not in reply, reply
    assert reply["status"] == 200
    headers = {key.lower(): value for key, value in reply["headers"].items()}
    assert headers.get("x-network-test") == "ok"
    assert base64.b64decode(reply["body"]) == b"hello-network"


def test_tcp_round_trip(qapp: object) -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    def serve() -> None:
        with contextlib.closing(listener):
            connection, _ = listener.accept()
            with contextlib.closing(connection):
                data = connection.recv(1024)
                connection.sendall(b"PONG:" + data)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    service = NetworkService()
    try:
        connected = service.handle(
            api.tcpConnect(CTX, {"host": "127.0.0.1", "port": port, "timeout": 5})
        )
        assert "error" not in connected, connected
        connection_id = connected["connectionId"]
        sent = service.handle(
            api.tcpSend(CTX, {"connectionId": connection_id, "data": "ping", "timeout": 5})
        )
        assert "error" not in sent, sent
        assert sent["bytes"] == 4
        received = service.handle(
            api.tcpSend(CTX, {"connectionId": connection_id, "data": "", "timeout": 5})
        )
        assert "error" not in received, received
        assert base64.b64decode(received["received"]) == b"PONG:ping"
        closed = service.handle(api.tcpClose(CTX, {"connectionId": connection_id}))
        assert closed == {"closed": True}
    finally:
        service.close()
        thread.join(5)
