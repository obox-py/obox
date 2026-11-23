"""单实例管道：探测、监听与唤醒信号。"""

from __future__ import annotations

import getpass

from obox.ui.single_instance import SingleInstance, instance_name


def test_instance_name_is_user_scoped() -> None:
    name = instance_name("obox")
    assert name.startswith("obox-")
    assert getpass.getuser().lower() not in name  # 只保留短哈希
    assert len(name.split("-")[-1]) == 10


def test_notify_without_server_returns_false(qapp) -> None:
    instance = SingleInstance("obox-test")
    instance.close()
    assert instance.try_notify(50) is False


def test_listen_then_notify_emits_show(qapp) -> None:
    server = SingleInstance("obox-test")
    assert server.listen()
    received: list[int] = []
    server.show_requested.connect(lambda: received.append(1))
    client = SingleInstance("obox-test")
    assert client.try_notify(500) is True
    for _ in range(50):
        qapp.processEvents()
        if received:
            break
    assert received
    server.close()
