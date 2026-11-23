"""双根扫描与 pyd 入口。"""

from __future__ import annotations

import json
from pathlib import Path

from obox.extensions.loader import scan_roots
from obox.extensions.manifest import load_manifest


def _make_extension(root: Path, name: str, entry: str) -> Path:
    directory = root / name
    (directory / "assets").mkdir(parents=True)
    (directory / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    (directory / entry).write_text("VALUE = 1\n", encoding="utf-8")
    (directory / "extension.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": "0.1.0",
                "publisher": "obox",
                "description": "d",
                "main": "extension.py",
                "icon": "icon.svg",
            }
        ),
        encoding="utf-8",
    )
    return directory


def test_manifest_accepts_pyd_entry(tmp_path: Path) -> None:
    directory = _make_extension(tmp_path, "packed", "extension.pyd")
    manifest = load_manifest(directory)
    assert manifest.extension_id == "packed.obox"


def test_scan_roots_prefers_installed(tmp_path: Path) -> None:
    source_root = tmp_path / "extensions"
    install_root = tmp_path / "installed"
    _make_extension(source_root, "demo", "extension.py")
    _make_extension(install_root, "demo", "extension.pyd")
    infos = scan_roots(source_root, install_root)
    assert len(infos) == 1
    assert infos[0].origin == "installed"
    assert (infos[0].directory / "extension.pyd").exists()
