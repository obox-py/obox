"""程序目录与数据目录解析。"""

from __future__ import annotations

from pathlib import Path

from obox.runtime import migrate_legacy, resolve


def test_source_layout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("OBOX_DATA_DIR", raising=False)
    paths = resolve(program_dir=tmp_path / "app")
    assert paths.program_dir == tmp_path / "app"
    assert paths.data_dir == tmp_path / "local" / "obox"
    assert paths.config_path == tmp_path / "local" / "obox" / "config.json"
    assert paths.system_extensions == tmp_path / "app" / "extensions"
    assert paths.user_extensions == tmp_path / "local" / "obox" / "extensions"


def test_env_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OBOX_PROGRAM_DIR", str(tmp_path / "app"))
    monkeypatch.setenv("OBOX_DATA_DIR", str(tmp_path / "data"))
    paths = resolve()
    assert paths.program_dir == tmp_path / "app"
    assert paths.data_dir == tmp_path / "data"


def test_installed_uses_localappdata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OBOX_INSTALLED", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("OBOX_DATA_DIR", raising=False)
    monkeypatch.setenv("OBOX_PROGRAM_DIR", str(tmp_path / "app"))
    paths = resolve()
    assert paths.data_dir == tmp_path / "obox"


def test_migrates_legacy_project_dir(tmp_path: Path, monkeypatch) -> None:
    program = tmp_path / "app"
    legacy = program / ".obox"
    legacy.mkdir(parents=True)
    (legacy / "config.json").write_text('{"settings": {"obox.close_action": "tray"}}', encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("OBOX_DATA_DIR", raising=False)
    paths = resolve(program_dir=program)
    assert (paths.data_dir / "config.json").is_file()
    assert "tray" in (paths.data_dir / "config.json").read_text(encoding="utf-8")


def test_migrate_legacy_skips_existing(tmp_path: Path) -> None:
    legacy = tmp_path / "old"
    target = tmp_path / "new"
    legacy.mkdir()
    (legacy / "config.json").write_text('{"a": 1}', encoding="utf-8")
    target.mkdir()
    (target / "config.json").write_text('{"b": 2}', encoding="utf-8")
    migrate_legacy(legacy, target)
    assert "b" in (target / "config.json").read_text(encoding="utf-8")
