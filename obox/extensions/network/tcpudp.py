"""TCP/UDP：QTcpSocket 与 QUdpSocket 的同步封装。

TCP 代理经 proxy.open_tunnel 建立隧道后交给 QTcpSocket 接管；
UDP 的 SOCKS5 UDP associate 未实现，由 NetworkService 明确拒绝。
"""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any

from obox.qt import QAbstractSocket, QHostAddress, QTcpSocket, QUdpSocket

from .proxy import NetworkError, open_tunnel


@dataclass
class TcpConnection:
    """一条已连通的 TCP 连接，按 connectionId 由 NetworkService 持有。"""

    socket: QTcpSocket
    host: str
    port: int
    proxy: bool = False

    def send(self, data: bytes, timeout: float = 5.0) -> dict[str, Any]:
        """发送数据并取回已缓冲的接收数据；data 为空表示只读取。"""
        sent = 0
        if data:
            written = self.socket.write(data)
            if written < 0:
                raise NetworkError(f"TCP 发送失败：{self.socket.errorString()}")
            sent = int(written)
            if not self.socket.waitForBytesWritten(_ms(timeout)):
                raise NetworkError(f"TCP 发送超时：{self.socket.errorString()}")
        else:
            timeout = max(0.1, float(timeout))
        return {"bytes": sent, "received": self.receive(0.0 if data else timeout)}

    def receive(self, timeout: float = 0.0) -> bytes:
        if self.socket.bytesAvailable() <= 0 and timeout > 0:
            self.socket.waitForReadyRead(_ms(timeout))
        return _to_bytes(self.socket.readAll())

    def close(self) -> None:
        self.socket.disconnectFromHost()
        if self.socket.state() != QAbstractSocket.UnconnectedState:
            self.socket.abort()
        self.socket.deleteLater()


def connect(
    host: str,
    port: int,
    timeout: float = 30.0,
    proxy_url: str | None = None,
) -> TcpConnection:
    """建立 TCP 连接；给了 proxy_url 就先建代理隧道。"""
    _validate(host, port)
    target_port = int(port)
    timeout = max(0.1, float(timeout))
    sock = QTcpSocket()
    if proxy_url:
        tunnel = open_tunnel(proxy_url, host, target_port, timeout)
        if not sock.setSocketDescriptor(tunnel.detach()):
            sock.deleteLater()
            raise NetworkError(f"接管代理隧道失败：{sock.errorString()}")
    else:
        sock.connectToHost(host, target_port)
        if not sock.waitForConnected(_ms(timeout)):
            error = sock.errorString()
            sock.abort()
            sock.deleteLater()
            raise NetworkError(f"TCP 连接 {host}:{target_port} 失败：{error}")
    return TcpConnection(socket=sock, host=host, port=target_port, proxy=bool(proxy_url))


def udp_send(
    host: str,
    port: int,
    data: bytes,
    timeout: float = 5.0,
    expect_reply: bool = False,
) -> dict[str, Any]:
    """发送一个 UDP 数据报；expect_reply 为真时等待一个应答数据报。"""
    _validate(host, port)
    address = _address(host)
    timeout = max(0.1, float(timeout))
    sock = QUdpSocket()
    try:
        if not sock.bind(QHostAddress(_any_address()), 0):
            raise NetworkError(f"UDP 绑定本地端口失败：{sock.errorString()}")
        written = sock.writeDatagram(data, address, int(port))
        if written < 0:
            raise NetworkError(f"UDP 发送失败：{sock.errorString()}")
        result: dict[str, Any] = {
            "bytes": int(written),
            "reply": b"",
            "from": "",
            "fromPort": 0,
        }
        if expect_reply:
            if not sock.waitForReadyRead(_ms(timeout)):
                raise NetworkError(f"UDP 等待应答超时（{timeout}s）")
            datagram = sock.receiveDatagram()
            result["reply"] = _to_bytes(datagram.data())
            result["from"] = datagram.senderAddress().toString()
            result["fromPort"] = int(datagram.senderPort())
        return result
    finally:
        sock.close()
        sock.deleteLater()


def _validate(host: str, port: int) -> None:
    if not str(host or "").strip():
        raise NetworkError("需要 host")
    try:
        target_port = int(port)
    except (TypeError, ValueError) as exc:
        raise NetworkError(f"端口不合法：{port}") from exc
    if not 0 < target_port < 65536:
        raise NetworkError(f"端口不合法：{port}")


def _address(host: str) -> QHostAddress:
    text = str(host).strip()
    address = QHostAddress(text)
    if not address.isNull():
        return address
    try:
        resolved = socket.gethostbyname(text)
    except OSError as exc:
        raise NetworkError(f"无法解析主机 {text}：{exc}") from exc
    address = QHostAddress(resolved)
    if address.isNull():
        raise NetworkError(f"无法解析主机 {text}")
    return address


def _any_address() -> QHostAddress:
    special = getattr(QHostAddress, "AnyIPv4", None)
    if special is not None:
        return QHostAddress(special)
    return QHostAddress(QHostAddress.Any)


def _to_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    data = getattr(value, "data", None)
    if data is not None:
        return bytes(data())
    return bytes(value)


def _ms(seconds: float) -> int:
    return max(1, int(float(seconds) * 1000))
