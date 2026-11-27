"""ICMP：调用系统 ping 并解析时间；不自行发原始报文。"""

from __future__ import annotations

import locale
import re
import subprocess
import sys
from typing import Any

from .proxy import NetworkError

_TIME = re.compile(r"(?:time|时间|時間)\s*[=<>]\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)
_REPLY = re.compile(r"\bttl[=\s]|\bttl\b|时间[=<]|\btime[=<]|0%\s*(?:loss|丢失)", re.IGNORECASE)


def ping(host: str, timeout: float = 2.0, count: int = 1) -> dict[str, Any]:
    """返回 {"alive": bool, "timeMs": float | None, "output": str}。"""
    target = str(host or "").strip()
    if not target:
        raise NetworkError("ping 需要 host")
    try:
        count = max(1, int(count))
    except (TypeError, ValueError):
        count = 1
    timeout = max(0.2, float(timeout))
    command = _command(target, timeout, count)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            timeout=timeout * count + 5.0,
            creationflags=flags,
            check=False,
        )
    except FileNotFoundError as exc:
        raise NetworkError("系统缺少 ping 命令，无法执行 ICMP 探测") from exc
    except subprocess.TimeoutExpired as exc:
        raise NetworkError(f"ping {target} 超时") from exc
    encoding = locale.getpreferredencoding(False) or "utf-8"
    text = (completed.stdout or b"").decode(encoding, errors="replace")
    error = (completed.stderr or b"").decode(encoding, errors="replace")
    output = (text + ("\n" + error if error.strip() else "")).strip()
    match = _TIME.search(text)
    elapsed = round(float(match.group(1)), 2) if match else None
    alive = completed.returncode == 0 and bool(match or _REPLY.search(text))
    return {"alive": bool(alive), "timeMs": elapsed, "output": output}


def _command(host: str, timeout: float, count: int) -> list[str]:
    if sys.platform == "win32":
        return ["ping", "-n", str(count), "-w", str(max(1, int(timeout * 1000))), host]
    if sys.platform == "darwin":
        return ["ping", "-c", str(count), "-W", str(max(1, int(timeout * 1000))), host]
    return ["ping", "-c", str(count), "-W", str(max(1, round(timeout))), host]
