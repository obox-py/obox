"""主题双源扫描：安装目录与用户目录，用户优先。"""

from __future__ import annotations

import json
from pathlib import Path

from obox.ui.kit import scan_themes


def _theme(root: Path, name: str, mode: str = "light") -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "theme.json").write_text(
        json.dumps({"name": name, "version": "1.0.0", "mode": mode, "entry": "create_ui_provider"}),
        encoding="utf-8",
    )
    return directory


def test_two_roots_merge(tmp_path: Path) -> None:
    system = tmp_path / "themes"
    user = tmp_path / "user"
    _theme(system, "light")
    _theme(system, "dark", "dark")
    _theme(user, "my-theme")
    kits = scan_themes([system, user])
    assert [kit.name for kit in kits] == ["dark", "light", "my-theme"]


def test_user_overrides_same_name(tmp_path: Path) -> None:
    system = tmp_path / "themes"
    user = tmp_path / "user"
    _theme(system, "light")
    overridden = _theme(user, "light", "dark")
    kits = scan_themes([system, user])
    assert len(kits) == 1
    assert kits[0].directory == overridden


def test_missing_roots_are_skipped(tmp_path: Path) -> None:
    assert scan_themes([tmp_path / "nope", tmp_path / "also-nope"]) == []
