"""安装版用 exe 路径定位程序目录。"""

from __future__ import annotations

import sys
from pathlib import Path

from obox.runtime import is_installed, resolve


def test_installed_program_dir_uses_exe(tmp_path: Path, monkeypatch) -> None:
    install = tmp_path / "Programs" / "obox"
    install.mkdir(parents=True)
    fake_exe = install / "obox.exe"
    fake_exe.write_bytes(b"")
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("OBOX_PROGRAM_DIR", raising=False)
    monkeypatch.delenv("OBOX_INSTALLED", raising=False)
    assert is_installed()
    paths = resolve()
    assert paths.program_dir == install
    assert paths.system_extensions == install / "extensions"


def test_source_still_uses_repo_root(monkeypatch) -> None:
    monkeypatch.setattr(sys, "executable", sys.executable)
    monkeypatch.delenv("OBOX_PROGRAM_DIR", raising=False)
    monkeypatch.delenv("OBOX_INSTALLED", raising=False)
    paths = resolve()
    assert (paths.program_dir / "obox").is_dir()
