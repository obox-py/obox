"""按用户命名的单实例管道：第二个实例唤醒已有窗口后退出。"""

from __future__ import annotations

import getpass
import hashlib

from PySide6.QtCore import QCoreApplication, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def instance_name(prefix: str = "obox") -> str:
    user = getpass.getuser().lower()
    digest = hashlib.sha1(user.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


class SingleInstance(QObject):
    """探测/监听本地管道；同名管道已存在即视为已有实例。"""

    show_requested = Signal()

    def __init__(self, prefix: str = "obox", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name = instance_name(prefix)
        self._server: QLocalServer | None = None

    @property
    def name(self) -> str:
        return self._name

    def try_notify(self, timeout_ms: int = 300) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._name)
        if not socket.waitForConnected(timeout_ms):
            return False
        socket.write(b"show")
        socket.flush()
        socket.waitForBytesWritten(timeout_ms)
        for _ in range(20):
            QCoreApplication.processEvents()
            if socket.bytesAvailable():
                break
            socket.waitForReadyRead(10)
        socket.disconnectFromServer()
        return True

    def listen(self) -> bool:
        QLocalServer.removeServer(self._name)
        server = QLocalServer(self)
        if not server.listen(self._name):
            return False
        server.newConnection.connect(self._on_connection)
        self._server = server
        return True

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None

    def _on_connection(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            connection = self._server.nextPendingConnection()
            connection.readyRead.connect(lambda conn=connection: self._read(conn))
            connection.disconnected.connect(connection.deleteLater)
            if connection.waitForReadyRead(500):
                self._read(connection)

    def _read(self, connection) -> None:
        data = bytes(connection.readAll())
        if b"show" in data:
            self.show_requested.emit()
        connection.write(b"ok")
        connection.flush()
        connection.waitForBytesWritten(200)
        connection.disconnectFromServer()
