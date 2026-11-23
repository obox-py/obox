"""打包脚本：import 图分析与产物结构。"""

from __future__ import annotations

from pathlib import Path

from scripts.pack_extension import build, local_modules


def _make_extension(tmp_path: Path) -> Path:
    directory = tmp_path / "demo"
    (directory / "assets").mkdir(parents=True)
    (directory / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
    (directory / "extension.py").write_text(
        "import utils\nfrom obox.api.message import Message\n\ndef activate(context): pass\ndef deactivate(context): pass\n",
        encoding="utf-8",
    )
    (directory / "utils.py").write_text("VALUE = 1\n", encoding="utf-8")
    (directory / "extension.json").write_text(
        '{"name": "demo", "version": "0.1.0", "publisher": "obox", "description": "d",'
        ' "main": "extension.py", "icon": "icon.svg"}',
        encoding="utf-8",
    )
    return directory


def test_local_modules_follow_local_imports(tmp_path: Path) -> None:
    directory = _make_extension(tmp_path)
    modules = {path.name for path in local_modules(directory / "extension.py")}
    assert modules == {"extension.py", "utils.py"}


def test_dry_run_does_not_create_dist(tmp_path: Path) -> None:
    directory = _make_extension(tmp_path)
    dist = tmp_path / "dist"
    build(directory, dist, dry_run=True)
    assert not dist.exists()
