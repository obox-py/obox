from __future__ import annotations

import uuid

from obox.core.ipc.client import IpcClient
from obox.core.ipc.server import IpcServer


def _name() -> str:
    return f"obox-test-{uuid.uuid4().hex[:8]}"


def test_handshake_and_frame_round_trip(qapp, qtbot) -> None:
    token = "token-1"
    server = IpcServer(token)
    name = server.listen(_name())
    received: list[dict] = []
    server.frame_received.connect(received.append)

    client = IpcClient()
    connected: list[bool] = []
    client.connected.connect(lambda: connected.append(True))
    client.connected.connect(
        lambda: client.send({"src": "demo.obox", "dst": "obox", "msg_id": "PING", "payload": {"n": 1}})
    )
    client.connect_to(name, token)

    qtbot.waitUntil(lambda: bool(received), timeout=5000)
    assert connected == [True]
    assert received[0]["payload"] == {"n": 1}
    server.close()
    client.close()


def test_wrong_token_rejected(qapp, qtbot) -> None:
    server = IpcServer("right-token")
    name = server.listen(_name())
    client = IpcClient()
    connected: list[bool] = []
    rejected: list[str] = []
    client.connected.connect(lambda: connected.append(True))
    server.handshake_failed.connect(rejected.append)
    client.connect_to(name, "wrong-token")
    qtbot.waitUntil(lambda: bool(rejected), timeout=3000)
    assert connected == []
    server.close()
    client.close()
