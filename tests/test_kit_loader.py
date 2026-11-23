"""kit 扫描与加载。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from obox.ui.kit import KitError, load_provider, scan_themes, select_kit

ROOT = Path(__file__).resolve().parent.parent


def _make_theme(root: Path, name: str, mode: str = "light") -> Path:
    directory = root / name
    directory.mkdir()
    (directory / "theme.json").write_text(
        json.dumps({"name": name, "version": "1.0.0", "mode": mode, "entry": "create_ui_provider"}),
        encoding="utf-8",
    )
    return directory


def test_scan_finds_themes(tmp_path: Path) -> None:
    _make_theme(tmp_path, "light")
    _make_theme(tmp_path, "dark", "dark")
    kits = scan_themes(tmp_path)
    assert [kit.name for kit in kits] == ["dark", "light"]


def test_scan_missing_dir(tmp_path: Path) -> None:
    assert scan_themes(tmp_path / "nope") == []


def test_select_unknown_lists_available(tmp_path: Path) -> None:
    _make_theme(tmp_path, "light")
    with pytest.raises(KitError) as error:
        select_kit(scan_themes(tmp_path), "dark")
    assert "light" in str(error.value)


def test_load_missing_pyd(tmp_path: Path) -> None:
    _make_theme(tmp_path, "light")
    with pytest.raises(KitError):
        load_provider(scan_themes(tmp_path)[0])


def test_load_real_pyd_if_built() -> None:
    pyd = ROOT / ".theme" / "light" / "light.pyd"
    if not pyd.exists():
        pytest.skip("尚未构建 pyd")
    provider = load_provider(select_kit(scan_themes(ROOT / ".theme"), "light"))
    assert provider.mode == "light"
    assert isinstance(provider.palette, dict) and provider.palette
    assert not hasattr(provider, "component_types")