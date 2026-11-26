"""扩展宿主侧的命名管道客户端。"""

from __future__ import annotations

from typing import Any

from obox.qt import QObject, Signal
from obox.qt import QLocalSocket

from ...api.errors import ProtocolError
from .framing import FrameDecoder, encode_frame
from .server import PROTOCOL_VERSION


class IpcClient(QObject):
    frame_received = Signal(dict)
    connected = Signal()
    disconnected = Signal()
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._socket = QLocalSocket(self)
        self._decoder = FrameDecoder()
        self._handshaken = False
        self._token = ""
        self._socket.readyRead.connect(self._on_ready_read)
        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)

    @property
    def connected_ready(self) -> bool:
        return self._handshaken

    def connect_to(self, pipe_name: str, token: str, timeout_ms: int = 3000) -> None:
        self._token = token
        self._socket.connectToServer(pipe_name)
        if not self._socket.waitForConnected(timeout_ms):
            raise ProtocolError(f"连接命名管道失败：{pipe_name}（{self._socket.errorString()}）")

    def send(self, data: dict[str, Any]) -> None:
        if not self._handshaken:
            raise ProtocolError("握手未完成，消息无法发送")
        self._socket.write(encode_frame(data))
        self._socket.flush()

    def close(self) -> None:
        self._socket.disconnectFromServer()

    def _on_connected(self) -> None:
        self._decoder = FrameDecoder()
        self._handshaken = False
        self._socket.write(encode_frame({"type": "hello", "protocol": PROTOCOL_VERSION, "token": self._token}))
        self._socket.flush()

    def _on_ready_read(self) -> None:
        for frame in self._decoder.feed(bytes(self._socket.readAll())):
            if not self._handshaken:
                if frame.get("type") != "welcome":
                    self.failed.emit("服务端拒绝握手")
                    self._socket.disconnectFromServer()
                    return
                self._handshaken = True
                self.connected.emit()
                continue
            self.frame_received.emit(frame)

    def _on_disconnected(self) -> None:
        self._handshaken = False
        self.disconnected.emit()
