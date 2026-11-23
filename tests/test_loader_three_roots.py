"""三根扫描与优先级。"""

from __future__ import annotations

import json
from pathlib import Path

from obox.extensions.loader import scan_all


def _make(root: Path, name: str, origin_entry: str = "extension.py") -> None:
    directory = root / name
    (directory / "assets").mkdir(parents=True)
    (directory / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    (directory / origin_entry).write_text("VALUE = 1\n", encoding="utf-8")
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


def test_user_overrides_system(tmp_path: Path) -> None:
    user = tmp_path / "user"
    system = tmp_path / "system"
    _make(system, "demo")
    _make(user, "demo")
    infos = scan_all([(user, "user"), (system, "system")])
    assert len(infos) == 1
    assert infos[0].origin == "user"


def test_three_roots_all_loaded(tmp_path: Path) -> None:
    user = tmp_path / "user"
    system = tmp_path / "system"
    source = tmp_path / "source"
    _make(user, "a")
    _make(system, "b")
    _make(source, "c")
    infos = scan_all([(user, "user"), (system, "system"), (source, "source")])
    assert [info.manifest.name for info in infos] == ["a", "b", "c"]
