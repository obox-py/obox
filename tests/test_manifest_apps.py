"""清单里的 contributes.app。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from obox.api.errors import ManifestError
from obox.extensions.manifest import load_manifest


def _make(tmp_path: Path, app) -> Path:
    directory = tmp_path / "demo"
    (directory / "assets").mkdir(parents=True)
    (directory / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    (directory / "assets" / "note.svg").write_text("<svg/>", encoding="utf-8")
    (directory / "extension.py").write_text("def activate(c): pass\ndef deactivate(c): pass\n", encoding="utf-8")
    payload = {
        "name": "demo",
        "version": "0.1.0",
        "publisher": "obox",
        "description": "示范",
        "main": "extension.py",
        "icon": "icon.svg",
        "contributes": {"app": app},
    }
    (directory / "extension.json").write_text(json.dumps(payload), encoding="utf-8")
    return directory


def test_single_app(tmp_path: Path) -> None:
    manifest = load_manifest(_make(tmp_path, {"id": "demo.notes", "title": "笔记", "icon": "note.svg"}))
    assert len(manifest.apps) == 1
    app = manifest.apps[0]
    assert app["id"] == "demo.notes"
    assert app["title"] == "笔记"
    assert app["icon"].endswith("note.svg")
    assert app["single"] is True and app["persistent"] is False


def test_multiple_apps(tmp_path: Path) -> None:
    manifest = load_manifest(_make(tmp_path, [{"title": "甲"}, {"id": "demo.b", "title": "乙", "single": False}]))
    assert [app["id"] for app in manifest.apps] == ["demo.obox.app0", "demo.b"]
    assert manifest.apps[1]["single"] is False


def test_no_app(tmp_path: Path) -> None:
    manifest = load_manifest(_make(tmp_path, None))
    assert manifest.apps == []


def test_invalid_ids(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        load_manifest(_make(tmp_path, [{"id": "Bad"}]))


def test_duplicate_ids(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        load_manifest(_make(tmp_path, [{"id": "demo.a"}, {"id": "demo.a"}]))
