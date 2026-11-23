"""obox 侧的命名管道服务端。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from ...api.errors import ProtocolError
from .framing import FrameDecoder, encode_frame

PROTOCOL_VERSION = 1


class IpcServer(QObject):
    """只接受一个宿主连接；握手校验协议版本与一次性 token。"""

    frame_received = Signal(dict)
    client_connected = Signal()
    client_disconnected = Signal()
    handshake_failed = Signal(str)

    def __init__(self, token: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.token = token
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        self._socket: QLocalSocket | None = None
        self._decoder = FrameDecoder()
        self._handshaken = False

    @property
    def pipe_name(self) -> str:
        return self._server.fullServerName()

    @property
    def connected(self) -> bool:
        return self._handshaken

    def listen(self, name: str) -> str:
        QLocalServer.removeServer(name)
        if not self._server.listen(name):
            raise ProtocolError(f"命名管道监听失败：{name}（{self._server.errorString()}）")
        return self._server.fullServerName()

    def send(self, data: dict[str, Any]) -> None:
        if self._socket is None or self._socket.state() != QLocalSocket.LocalSocketState.ConnectedState:
            raise ProtocolError("宿主未连接，消息无法发送")
        self._socket.write(encode_frame(data))
        self._socket.flush()

    def close(self) -> None:
        if self._socket is not None:
            self._socket.disconnectFromServer()
        self._server.close()

    def _on_new_connection(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        if self._socket is not None:
            socket.disconnectFromServer()
            return
        self._socket = socket
        self._decoder = FrameDecoder()
        self._handshaken = False
        socket.readyRead.connect(self._on_ready_read)
        socket.disconnected.connect(self._on_disconnected)

    def _on_ready_read(self) -> None:
        if self._socket is None:
            return
        for frame in self._decoder.feed(bytes(self._socket.readAll())):
            self._handle_frame(frame)

    def _handle_frame(self, frame: dict[str, Any]) -> None:
        if not self._handshaken:
            if frame.get("type") != "hello" or frame.get("token") != self.token:
                self._reject("握手失败")
                return
            if int(frame.get("protocol", 0)) != PROTOCOL_VERSION:
                self._reject(f"协议版本不匹配：{frame.get('protocol')}")
                return
            self._handshaken = True
            self.send({"type": "welcome", "protocol": PROTOCOL_VERSION})
            self.client_connected.emit()
            return
        self.frame_received.emit(frame)

    def _reject(self, reason: str) -> None:
        """握手失败只断开连接并报告，不在 Qt 槽里抛异常。"""
        if self._socket is not None:
            self._socket.disconnectFromServer()
            self._socket = None
        self._handshaken = False
        self.handshake_failed.emit(reason)
        self.client_disconnected.emit()

    def _on_disconnected(self) -> None:
        self._socket = None
        self._handshaken = False
        self.client_disconnected.emit()
