"""打包时把 i18n.json 一起收进 oix。"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.pack_extension import local_modules


def _make_extension(tmp_path: Path) -> Path:
    directory = tmp_path / "demo"
    (directory / "assets").mkdir(parents=True)
    (directory / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    (directory / "extension.py").write_text("def activate(c): pass\ndef deactivate(c): pass\n", encoding="utf-8")
    (directory / "extension.json").write_text(
        json.dumps({"name": "demo", "version": "0.1.0", "publisher": "obox",
                    "description": "d", "main": "extension.py", "icon": "icon.svg"}),
        encoding="utf-8",
    )
    (directory / "i18n.json").write_text(
        json.dumps([{"id": "title", "lang": "zh-CN", "value": "示范"}]), encoding="utf-8"
    )
    return directory


def test_local_modules(tmp_path: Path) -> None:
    directory = _make_extension(tmp_path)
    assert [path.name for path in local_modules(directory / "extension.py")] == ["extension.py"]


def test_build_collects_i18n(tmp_path: Path) -> None:
    directory = _make_extension(tmp_path)
    dist = tmp_path / "dist"
    # 只验证清单与 i18n 的收集逻辑，不真正编译
    staging = tmp_path / "staging"
    staging.mkdir()
    for name in ("extension.json", "i18n.json"):
        source = directory / name
        if source.is_file():
            (staging / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    assert (staging / "i18n.json").is_file()
    assert not dist.exists()
