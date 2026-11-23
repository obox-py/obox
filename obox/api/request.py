"""请求对象：阻塞等待、回调与 await 三形态。"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Callable

from .errors import RequestTimeout

DoneCallback = Callable[["Request"], None]


class Request:
    """一次请求-应答的句柄；先完成者生效，重复完成被忽略。"""

    def __init__(self, correlation_id: str, timeout: float | None = None) -> None:
        self.correlation_id = correlation_id
        self.timeout = timeout
        self.deadline = None if timeout is None else time.monotonic() + timeout
        self._event = threading.Event()
        self._result: Any = None
        self._error: BaseException | None = None
        self._callbacks: list[DoneCallback] = []
        self._lock = threading.Lock()
        self._settled = False
        self.expire_hook: Callable[[], None] | None = None

    @property
    def done(self) -> bool:
        return self._event.is_set()

    @property
    def error(self) -> BaseException | None:
        return self._error

    def resolve(self, payload: Any = None) -> None:
        self._settle(payload)

    def reject(self, error: BaseException) -> None:
        self._settle(None, error)

    def expire(self) -> None:
        if not self.done:
            self.reject(RequestTimeout(f"请求超时：{self.correlation_id}"))

    def _settle(self, payload: Any, error: BaseException | None = None) -> None:
        with self._lock:
            if self._settled:
                return
            self._settled = True
            self._result = payload
            self._error = error
            callbacks = list(self._callbacks)
        self._event.set()
        for callback in callbacks:
            callback(self)

    def add_done_callback(self, callback: DoneCallback) -> "Request":
        with self._lock:
            settled = self._settled
            if not settled:
                self._callbacks.append(callback)
        if settled:
            callback(self)
        return self

    def result(self, timeout: float | None = None) -> Any:
        wait = self.timeout if timeout is None else timeout
        if not self._event.wait(wait):
            if self.expire_hook is not None:
                self.expire_hook()
            raise RequestTimeout(f"请求超时：{self.correlation_id}")
        if self._error is not None:
            raise self._error
        return self._result

    def __await__(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def _deliver(request: "Request") -> None:
            def _apply() -> None:
                if future.done():
                    return
                if request._error is not None:
                    future.set_exception(request._error)
                else:
                    future.set_result(request._result)

            loop.call_soon_threadsafe(_apply)

        self.add_done_callback(_deliver)
        return future.__await__()
