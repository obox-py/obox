"""HTTP/HTTPS 请求：QNetworkAccessManager + 嵌套 QEventLoop 同步等待。"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit

from obox.qt import (
    QEventLoop,
    QNetworkAccessManager,
    QNetworkProxy,
    QNetworkRequest,
    QSslConfiguration,
    QSslSocket,
    QTimer,
    QUrl,
)

from .proxy import NetworkError, parse_proxy_url


def request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 30.0,
    proxy_url: str | None = None,
    ssl_strict: bool = True,
) -> dict[str, Any]:
    """执行一次请求，返回 {"status", "headers", "body", "url", "durationMs"}。"""
    target = str(url or "").strip()
    parsed = urlsplit(target)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise NetworkError(f"HTTP 需要 http:// 或 https:// 地址：{target}")
    verb = str(method or "GET").upper()
    if not verb.isalpha():
        raise NetworkError(f"HTTP 方法不合法：{method}")
    data = bytes(body or b"")
    timeout = max(0.1, float(timeout))

    manager = QNetworkAccessManager()
    if proxy_url:
        endpoint = parse_proxy_url(proxy_url)
        proxy_type = QNetworkProxy.Socks5Proxy if endpoint.is_socks else QNetworkProxy.HttpProxy
        manager.setProxy(QNetworkProxy(proxy_type, endpoint.host, endpoint.port))

    network_request = QNetworkRequest(QUrl(target))
    network_request.setAttribute(
        QNetworkRequest.RedirectPolicyAttribute,
        QNetworkRequest.NoLessSafeRedirectPolicy,
    )
    ssl_config = QSslConfiguration.defaultConfiguration()
    ssl_config.setPeerVerifyMode(
        QSslSocket.VerifyPeer if ssl_strict else QSslSocket.VerifyNone
    )
    network_request.setSslConfiguration(ssl_config)
    for name, value in (headers or {}).items():
        network_request.setRawHeader(
            str(name).encode("latin-1"), str(value).encode("latin-1")
        )

    if verb == "GET":
        reply = manager.get(network_request)
    elif verb == "POST":
        reply = manager.post(network_request, data)
    else:
        reply = manager.sendCustomRequest(network_request, verb.encode("ascii"), data)

    loop = QEventLoop()
    timed_out = {"value": False}

    def _abort() -> None:
        timed_out["value"] = True
        reply.abort()

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(_abort)
    reply.finished.connect(loop.quit)
    timer.start(int(timeout * 1000))

    started = time.monotonic()
    try:
        if not reply.isFinished():
            loop.exec()
    finally:
        timer.stop()
    elapsed = round((time.monotonic() - started) * 1000, 1)

    try:
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        status_code = int(status) if status is not None else 0
        response_body = _to_bytes(reply.readAll())
        response_headers = {
            _to_bytes(name).decode("latin-1"): _to_bytes(value).decode("latin-1")
            for name, value in reply.rawHeaderPairs()
        }
        final_url = reply.url().toString()
        error_text = reply.errorString()
    finally:
        reply.deleteLater()
        manager.deleteLater()

    if timed_out["value"]:
        raise NetworkError(f"HTTP 请求超时（{timeout}s）：{target}")
    if status_code == 0:
        raise NetworkError(f"HTTP 请求失败：{error_text}")
    return {
        "status": status_code,
        "headers": response_headers,
        "body": response_body,
        "url": final_url,
        "durationMs": elapsed,
    }


def _to_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    data = getattr(value, "data", None)
    if data is not None:
        return bytes(data())
    return bytes(value)
