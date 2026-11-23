"""安装 .oix：解压、覆盖与路径校验。"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from obox.api.errors import ManifestError
from obox.extensions.loader import _safe_target, install_packages


def _make_package(path: Path, members: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def _manifest(name: str = "gallery", publisher: str = "obox") -> str:
    return (
        '{"name": "%s", "version": "0.1.0", "publisher": "%s", "description": "d",'
        ' "main": "extension.py", "icon": "icon.svg"}' % (name, publisher)
    )


def test_install_extracts_package(tmp_path: Path) -> None:
    install_root = tmp_path / "installed"
    install_root.mkdir()
    package = _make_package(
        install_root / "gallery.obox.0.1.0.oix",
        {"extension.json": _manifest(), "extension.pyd": "binary", "assets/icon.svg": "<svg/>"},
    )
    assert package.exists()
    installed = install_packages(install_root)
    target = install_root / "gallery.obox"
    assert installed == [target]
    assert (target / "extension.pyd").exists()
    assert (target / "assets" / "icon.svg").exists()


def test_reinstall_replaces_old_files(tmp_path: Path) -> None:
    install_root = tmp_path / "installed"
    install_root.mkdir()
    _make_package(
        install_root / "gallery.obox.0.1.0.oix", {"extension.json": _manifest(), "extension.pyd": "a"}
    )
    install_packages(install_root)
    target = install_root / "gallery.obox"
    (target / "stale.txt").write_text("old", encoding="utf-8")
    install_packages(install_root)
    assert not (target / "stale.txt").exists()


def test_path_traversal_rejected(tmp_path: Path) -> None:
    target = tmp_path / "gallery.obox"
    target.mkdir()
    with pytest.raises(ManifestError):
        _safe_target(target, "../evil.txt")


def test_missing_manifest_skipped(tmp_path: Path) -> None:
    install_root = tmp_path / "installed"
    install_root.mkdir()
    _make_package(install_root / "bad.oix", {"extension.pyd": "binary"})
    assert install_packages(install_root) == []
