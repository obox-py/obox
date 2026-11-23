from __future__ import annotations

import asyncio
import threading
import time

import pytest

from obox.api.errors import RequestTimeout
from obox.api.request import Request


def test_blocking_result() -> None:
    request = Request("c1", timeout=1)
    threading.Timer(0.05, lambda: request.resolve({"ok": True})).start()
    assert request.result() == {"ok": True}


def test_callback_runs_once() -> None:
    request = Request("c2", timeout=1)
    seen = []
    request.add_done_callback(lambda r: seen.append(r.done))
    request.resolve(1)
    request.reject(RuntimeError("late"))
    assert seen == [True]
    assert request.result() == 1


def test_timeout() -> None:
    request = Request("c3", timeout=0.05)
    with pytest.raises(RequestTimeout):
        request.result()


def test_await() -> None:
    async def scenario() -> int:
        request = Request("c4", timeout=1)

        def _resolve() -> None:
            time.sleep(0.05)
            request.resolve(7)

        threading.Thread(target=_resolve, daemon=True).start()
        return await request

    assert asyncio.run(scenario()) == 7


def test_await_error() -> None:
    async def scenario() -> str:
        request = Request("c5", timeout=1)

        def _fail() -> None:
            time.sleep(0.02)
            request.reject(RuntimeError("boom"))

        threading.Thread(target=_fail, daemon=True).start()
        with pytest.raises(RuntimeError):
            await request
        return "done"

    assert asyncio.run(scenario()) == "done"
