from __future__ import annotations

import json
from pathlib import Path

import pytest

from obox.api.errors import ManifestError
from obox.extensions.loader import scan_extensions
from obox.extensions.manifest import load_manifest

DEMO = Path(__file__).resolve().parent.parent / "extensions" / "demo"


def test_demo_manifest_valid() -> None:
    manifest = load_manifest(DEMO)
    assert manifest.extension_id == "demo.obox"
    assert manifest.icon_path.exists()
    assert "views" in manifest.contributes


def _write(tmp_path: Path, data: dict) -> Path:
    directory = tmp_path / "ext"
    (directory / "assets").mkdir(parents=True)
    (directory / "extension.py").write_text("def activate(context): pass\ndef deactivate(context): pass\n")
    (directory / "assets" / "icon.svg").write_text("<svg/>")
    (directory / "extension.json").write_text(json.dumps(data), encoding="utf-8")
    return directory


def _valid() -> dict:
    return {
        "name": "ext",
        "version": "1.0.0",
        "publisher": "obox",
        "description": "d",
        "main": "extension.py",
        "icon": "icon.svg",
    }


def test_missing_field(tmp_path: Path) -> None:
    data = _valid()
    data.pop("publisher")
    with pytest.raises(ManifestError):
        load_manifest(_write(tmp_path, data))


def test_icon_must_be_svg(tmp_path: Path) -> None:
    data = _valid()
    data["icon"] = "icon.png"
    with pytest.raises(ManifestError):
        load_manifest(_write(tmp_path, data))


def test_icon_cannot_escape_assets(tmp_path: Path) -> None:
    data = _valid()
    data["icon"] = "../icon.svg"
    with pytest.raises(ManifestError):
        load_manifest(_write(tmp_path, data))


def test_main_must_be_extension_py(tmp_path: Path) -> None:
    data = _valid()
    data["main"] = "main.py"
    with pytest.raises(ManifestError):
        load_manifest(_write(tmp_path, data))


def test_scan_skips_dirs_without_manifest(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    assert scan_extensions(tmp_path) == []
