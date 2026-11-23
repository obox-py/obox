"""进程内消息总线：路由、广播、关联表与超时。"""

from __future__ import annotations

import threading
import uuid
from typing import Any, Callable, Protocol

from ..api.component import decode_message
from ..api.errors import BroadcastReply, MessageFormatError, RequestTimeout
from ..api.message import OB_BOX, Message
from ..api.request import Request

Handler = Callable[[Message], Any]


class Transport(Protocol):
    """传输适配：把消息写入对端。"""

    def send(self, data: dict[str, Any]) -> None: ...


class MessageBus:
    """单进程内的一份总线；跨进程部分交给 attach 的 Transport。"""

    def __init__(self, local_id: str = OB_BOX) -> None:
        self.local_id = local_id
        self.local_ids: set[str] = {local_id}
        self._handlers: dict[str, list[Handler]] = {}
        self._pending: dict[str, Request] = {}
        self._timers: dict[str, threading.Timer] = {}
        self._transport: Transport | None = None
        self._lock = threading.Lock()

    def attach_transport(self, transport: Transport) -> None:
        self._transport = transport

    def add_local(self, identity: str) -> None:
        """宿主进程里每个已激活扩展都是一个本地身份。"""
        self.local_ids.add(identity)

    def on(self, msg_id: str, handler: Handler) -> Callable[[], None]:
        self._handlers.setdefault(msg_id, []).append(handler)

        def _unsubscribe() -> None:
            handlers = self._handlers.get(msg_id, [])
            if handler in handlers:
                handlers.remove(handler)

        return _unsubscribe

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def send(self, message: Message) -> None:
        if message.reply and message.is_broadcast:
            raise BroadcastReply("广播消息不接受返程")
        if message.is_broadcast:
            self._dispatch(message)
            if self._transport is not None:
                self._transport.send(message.to_dict())
            return
        if message.dst in self.local_ids:
            self._dispatch(message)
            return
        if self._transport is None:
            raise ConnectionError("没有可用的传输通道")
        self._transport.send(message.to_dict())

    def request(self, message: Message, timeout: float = 5.0) -> Request:
        correlation_id = uuid.uuid4().hex
        message.correlation_id = correlation_id
        request = Request(correlation_id, timeout)
        request.expire_hook = lambda: self._expire(correlation_id)
        with self._lock:
            self._pending[correlation_id] = request
        timer = threading.Timer(timeout, self._expire, args=(correlation_id,))
        timer.daemon = True
        with self._lock:
            self._timers[correlation_id] = timer
        timer.start()
        try:
            self.send(message)
        except Exception as exc:  # 发送失败要立刻把请求结束掉，否则调用方会白等
            self._finish(correlation_id, error=exc)
            raise
        return request

    def receive(self, data: dict[str, Any]) -> None:
        """对端帧到达；返程先进关联表，其余交给订阅者。"""
        try:
            message = decode_message(data)
        except Exception:
            return
        if message.reply:
            request = self._pending.get(message.correlation_id)
            if request is not None:
                payload = message.payload
                if "error" in payload:
                    self._finish(
                        message.correlation_id,
                        error=RuntimeError(f"{payload['error']}: {payload.get('message', '')}"),
                    )
                else:
                    self._finish(message.correlation_id, payload=payload)
                return
        if message.is_broadcast or message.dst in self.local_ids:
            self._dispatch(message)

    def reply(self, request_message: Message, payload: dict[str, Any]) -> None:
        if request_message.is_broadcast:
            raise BroadcastReply("广播消息不接受应答")
        if not request_message.correlation_id:
            raise MessageFormatError("该消息不是请求（缺少 correlation_id），无法应答")
        data = request_message.to_dict()
        data.update(
            {
                "src": request_message.dst or OB_BOX,
                "dst": request_message.src,
                "reply": True,
                "payload": {**request_message.payload, **payload},
            }
        )
        self.send(decode_message(data))

    def _dispatch(self, message: Message) -> None:
        for handler in list(self._handlers.get(message.msg_id, [])):
            handler(message)

    def _expire(self, correlation_id: str) -> None:
        self._finish(correlation_id, error=RequestTimeout(f"请求超时：{correlation_id}"))

    def _finish(self, correlation_id: str, payload: dict | None = None, error: BaseException | None = None) -> None:
        with self._lock:
            request = self._pending.pop(correlation_id, None)
            timer = self._timers.pop(correlation_id, None)
        if timer is not None:
            timer.cancel()
        if request is None:
            return
        if error is not None:
            request.reject(error)
        else:
            request.resolve(payload)
