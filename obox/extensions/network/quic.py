"""QUIC/HTTP3：优先用 aioquic；未安装时给出明确错误。"""

from __future__ import annotations

import asyncio
import importlib.util
import ssl
import threading
from typing import Any
from urllib.parse import quote, urlsplit

from .proxy import NetworkError

_MISSING = "QUIC 需要 aioquic：请先安装（uv add aioquic）"


def available() -> bool:
    return importlib.util.find_spec("aioquic") is not None


def _ensure_aioquic() -> None:
    try:
        import aioquic  # noqa: F401
    except ImportError as exc:
        raise NetworkError(f"{_MISSING}；{exc}") from exc


def request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 30.0,
    ssl_strict: bool = True,
) -> dict[str, Any]:
    """发起一次 HTTP/3 请求，返回 {"status", "headers", "body", "url"}。"""
    _ensure_aioquic()
    target = str(url or "").strip()
    parsed = urlsplit(target)
    if parsed.scheme != "https" or not parsed.hostname:
        raise NetworkError(f"QUIC 只支持 https:// 地址：{target}")
    verb = str(method or "GET").upper()
    if not verb.isalpha():
        raise NetworkError(f"HTTP 方法不合法：{method}")
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    timeout = max(0.1, float(timeout))
    try:
        status, response_headers, payload = _run(
            _fetch(
                host=parsed.hostname,
                port=parsed.port or 443,
                path=path,
                authority=parsed.netloc,
                method=verb,
                headers=dict(headers or {}),
                body=bytes(body or b""),
                timeout=timeout,
                ssl_strict=ssl_strict,
            )
        )
    except TimeoutError as exc:
        raise NetworkError(f"QUIC 请求超时（{timeout}s）：{target}") from exc
    except NetworkError:
        raise
    except (OSError, ssl.SSLError, ConnectionError) as exc:
        raise NetworkError(f"QUIC 请求失败：{exc}") from exc
    return {
        "status": status,
        "headers": response_headers,
        "body": payload,
        "url": target,
    }


async def _fetch(
    host: str,
    port: int,
    path: str,
    authority: str,
    method: str,
    headers: dict[str, str],
    body: bytes,
    timeout: float,
    ssl_strict: bool,
) -> tuple[int, dict[str, str], bytes]:
    from aioquic.asyncio import connect
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration

    configuration = QuicConfiguration(alpn_protocols=H3_ALPN, is_client=True)
    configuration.server_name = host
    if not ssl_strict:
        configuration.verify_mode = ssl.CERT_NONE

    client_class = _client_class()
    async with connect(
        host,
        port,
        configuration=configuration,
        create_protocol=client_class,
        wait_connected=True,
    ) as protocol:
        events = await asyncio.wait_for(
            protocol.request(method, path, authority, headers, body),
            timeout,
        )
    return _assemble(events, target_host=host)


def _assemble(events: list[Any], target_host: str = "") -> tuple[int, dict[str, str], bytes]:
    from aioquic.h3.events import DataReceived, HeadersReceived

    status = 0
    headers: dict[str, str] = {}
    chunks: list[bytes] = []
    for event in events:
        if isinstance(event, HeadersReceived):
            for name, value in event.headers:
                key = name.decode("latin-1")
                if key == ":status":
                    status = int(value.decode("latin-1") or 0)
                elif not key.startswith(":"):
                    headers[key] = value.decode("latin-1")
        elif isinstance(event, DataReceived):
            chunks.append(bytes(event.data))
    if status == 0:
        raise NetworkError(f"QUIC 应答缺少 :status：{target_host}")
    return status, headers, b"".join(chunks)


def _client_class() -> type:
    """按需构造 H3 客户端类，避免无 aioquic 时导入失败。"""
    from aioquic.asyncio import QuicConnectionProtocol
    from aioquic.h3.connection import H3Connection
    from aioquic.h3.events import DataReceived, HeadersReceived

    class H3Client(QuicConnectionProtocol):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._http = H3Connection(self._quic)
            self._events: dict[int, list[Any]] = {}
            self._waiters: dict[int, asyncio.Future] = {}

        async def request(
            self,
            method: str,
            path: str,
            authority: str,
            headers: dict[str, str],
            body: bytes,
        ) -> list[Any]:
            stream_id = self._quic.get_next_available_stream_id()
            request_headers = [
                (b":method", method.encode("ascii")),
                (b":scheme", b"https"),
                (b":authority", authority.encode("ascii")),
                (b":path", quote(path, safe="/?&=%:@!").encode("ascii")),
            ]
            request_headers.extend(
                (str(name).lower().encode("latin-1"), str(value).encode("latin-1"))
                for name, value in headers.items()
            )
            waiter = asyncio.get_running_loop().create_future()
            self._events[stream_id] = []
            self._waiters[stream_id] = waiter
            self._http.send_headers(
                stream_id=stream_id,
                headers=request_headers,
                end_stream=not body,
            )
            if body:
                self._http.send_data(stream_id=stream_id, data=body, end_stream=True)
            self.transmit()
            return await waiter

        def http_event_received(self, event: Any) -> None:
            if not isinstance(event, (HeadersReceived, DataReceived)):
                return
            stream_id = event.stream_id
            waiter = self._waiters.get(stream_id)
            if waiter is None:
                return
            self._events.setdefault(stream_id, []).append(event)
            if event.stream_ended:
                self._waiters.pop(stream_id, None)
                events = self._events.pop(stream_id, [])
                if not waiter.done():
                    waiter.set_result(events)

        def quic_event_received(self, event: Any) -> None:
            for http_event in self._http.handle_event(event):
                self.http_event_received(http_event)

    return H3Client


def _run(coroutine: Any) -> Any:
    """在无事件循环的调用线程里跑；已在循环里就换到临时线程。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    box: dict[str, Any] = {}

    def _worker() -> None:
        try:
            box["value"] = asyncio.run(coroutine)
        except BaseException as exc:  # noqa: BLE001 - 由调用线程原样抛出
            box["error"] = exc

    thread = threading.Thread(target=_worker, name="obox-quic", daemon=True)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["value"]
