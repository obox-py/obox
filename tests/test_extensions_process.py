"""两个扩展的纯函数：归一、校验、.rdp 文本与 Chrome 参数。"""

from __future__ import annotations

from pathlib import Path

from extensions.rdp.extension import build_rdp_text, normalize_connection, validate_connection
from extensions.webapp.extension import (
    build_chrome_args,
    dir_size_mb,
    find_chrome,
    normalize_site,
    validate_site,
)


def test_rdp_normalize_defaults() -> None:
    conn = normalize_connection({"name": " 办公机 ", "host": "10.0.0.8"})
    assert conn["name"] == "办公机"
    assert conn["port"] == 3389
    assert conn["remember"] is True


def test_rdp_validation_rules() -> None:
    base = normalize_connection({"name": "a", "host": "h"})
    assert validate_connection(base, []) == []
    assert validate_connection(normalize_connection({"name": "", "host": "h"}), []) == ["needName"]
    assert validate_connection(
        normalize_connection({"name": "a", "host": "", "port": "70000"}), []
    ) == ["needHost", "badPort"]
    rows = [normalize_connection({"id": 1, "name": "a", "host": "h"})]
    assert validate_connection(normalize_connection({"name": "a", "host": "h"}), rows) == ["dupName"]


def test_rdp_text_without_password() -> None:
    conn = normalize_connection({"name": "a", "host": "10.0.0.8", "port": "3390", "username": "u", "domain": "d"})
    text = build_rdp_text(conn)
    assert "full address:s:10.0.0.8:3390" in text
    assert "username:s:u" in text
    assert "domain:s:d" in text
    assert "password 51:b:" not in text
    assert text.endswith("\r\n")


def test_rdp_text_with_password_blob() -> None:
    conn = normalize_connection({"name": "a", "host": "h"})
    text = build_rdp_text(conn, b"\x01\x02")
    assert "password 51:b:0102" in text


def test_webapp_normalize_and_validate() -> None:
    site = normalize_site({"name": " 工单 ", "url": "https://t.local", "ignore": True})
    assert site["name"] == "工单"
    assert validate_site(site, []) == []
    assert validate_site(normalize_site({"name": "a", "url": "ftp://x"}), []) == ["needUrl"]
    rows = [normalize_site({"id": 1, "name": "a", "url": "https://a"})]
    assert validate_site(normalize_site({"name": "a", "url": "https://b"}), rows) == ["dupName"]


def test_chrome_args_and_missing(tmp_path: Path) -> None:
    args = build_chrome_args(
        "chrome.exe",
        {"url": "https://t.local", "ignore": True, "extraOrigins": "", "windowSize": "1280,800",
         "windowPos": "", "startMaximized": False, "lang": "", "scaleFactor": "", "disableGpu": False},
        tmp_path / "p",
    )
    assert args[1] == "--app=https://t.local"
    assert args[2].startswith("--user-data-dir=")
    assert "--ignore-certificate-errors" in args
    assert "--window-size=1280,800" in args
    assert find_chrome([str(tmp_path / "nope.exe")]) == ""


def test_dir_size_mb(tmp_path: Path) -> None:
    folder = tmp_path / "p"
    folder.mkdir()
    (folder / "a.bin").write_bytes(b"x" * 1024)
    assert 0 < dir_size_mb(folder) < 1

def test_dpapi_roundtrip_on_windows() -> None:
    import os

    import pytest

    from extensions.rdp.extension import protect, unprotect

    if os.name != "nt":
        pytest.skip("DPAPI 仅在 Windows 可用")
    secret = "p@ssw0rd".encode("utf-8")
    blob = protect(secret)
    assert blob and blob != secret
    assert unprotect(blob) == secret