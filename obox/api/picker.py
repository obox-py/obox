"""文件与目录选择：扩展发起请求，obox 弹对话框并返回结果。"""

from __future__ import annotations

from typing import Any

from .message import OB_BOX, Message

PICKER_OPEN_MSG = "PICKER_OPEN_MSG"
PICKER_RESULT_MSG = "PICKER_RESULT_MSG"
MODES = ("file", "dir")


def normalize_extensions(values: Any) -> list[str]:
    """后缀统一为小写且不带点；空项丢弃。"""
    result: list[str] = []
    for item in values or []:
        text = str(item).strip().lower().lstrip(".")
        if text and text not in result:
            result.append(text)
    return result


def validate_open(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    mode = str(payload.get("mode") or "file").lower()
    if mode not in MODES:
        return None, f"mode 只能是 file 或 dir：{mode}"
    ssh = payload.get("ssh")
    if ssh is not None:
        if not isinstance(ssh, dict) or not str(ssh.get("host") or "").strip():
            return None, "ssh 至少需要 host"
        ssh = {
            "host": str(ssh["host"]).strip(),
            "port": int(ssh.get("port") or 22),
            "user": str(ssh.get("user") or "").strip(),
            "password": str(ssh.get("password") or ""),
            "key_path": str(ssh.get("key_path") or "").strip(),
            "passphrase": str(ssh.get("passphrase") or ""),
        }
    return {
        "mode": mode,
        "extensions": normalize_extensions(payload.get("extensions")),
        "multi": bool(payload.get("multi")),
        "title": str(payload.get("title") or ("选择文件夹" if mode == "dir" else "选择文件")),
        "start_path": str(payload.get("start_path") or ""),
        "window_id": str(payload.get("window_id") or ""),
        "ssh": ssh,
    }, ""


def picker_open_message(
    src: str,
    mode: str = "file",
    extensions: list[str] | None = None,
    multi: bool = False,
    title: str = "",
    start_path: str = "",
    window_id: str = "",
    ssh: dict[str, Any] | None = None,
) -> Message:
    return Message(
        src=src,
        dst=OB_BOX,
        msg_id=PICKER_OPEN_MSG,
        payload={
            "mode": mode,
            "extensions": list(extensions or []),
            "multi": multi,
            "title": title,
            "start_path": start_path,
            "window_id": window_id,
            "ssh": ssh,
        },
    )


def picker_result_message(dst: str, paths: list[Any], error: str = "", cancelled: bool = False) -> Message:
    return Message(
        src=OB_BOX,
        dst=dst,
        msg_id=PICKER_RESULT_MSG,
        payload={"paths": list(paths), "error": error, "cancelled": cancelled},
    )
