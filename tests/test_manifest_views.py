"""视图容器与配置贡献的清单校验。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from obox.api.errors import ManifestError
from obox.extensions.manifest import load_manifest


def _make(tmp_path: Path, contributes: dict) -> Path:
    directory = tmp_path / "demo"
    (directory / "assets").mkdir(parents=True)
    (directory / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    (directory / "extension.py").write_text("def activate(c): pass\ndef deactivate(c): pass\n", encoding="utf-8")
    (directory / "extension.json").write_text(
        json.dumps(
            {
                "name": "demo",
                "version": "0.1.0",
                "publisher": "obox",
                "description": "示范",
                "main": "extension.py",
                "icon": "icon.svg",
                "contributes": contributes,
            }
        ),
        encoding="utf-8",
    )
    return directory


def test_main_container_rejected(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        load_manifest(_make(tmp_path, {"views": [{"id": "a.main", "container": "main"}]}))


def test_sidebar_and_bottom_accepted(tmp_path: Path) -> None:
    manifest = load_manifest(
        _make(tmp_path, {"views": [{"id": "a.main", "container": "sidebar"}, {"id": "a.bottom", "container": "bottom"}]})
    )
    assert [view["container"] for view in manifest.contributes["views"]] == ["sidebar", "bottom"]


def test_valid_configuration(tmp_path: Path) -> None:
    manifest = load_manifest(
        _make(
            tmp_path,
            {"configuration": {"properties": {"size": {"type": "enum", "title": "大小", "enum": ["s", "m"], "default": "s"}}}},
        )
    )
    assert manifest.configuration["size"]["type"] == "enum"


def test_bad_configuration_type(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        load_manifest(_make(tmp_path, {"configuration": {"properties": {"x": {"type": "number", "title": "x"}}}}))


def test_enum_default_must_exist(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        load_manifest(
            _make(tmp_path, {"configuration": {"properties": {"x": {"type": "enum", "title": "x", "enum": ["a"], "default": "b"}}}})
        )
