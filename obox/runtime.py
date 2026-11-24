"""程序目录与数据目录：源码态与安装态。"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


def is_installed() -> bool:
    if os.environ.get("OBOX_INSTALLED") == "1":
        return True
    if getattr(sys, "frozen", False):
        return True
    return "__compiled__" in globals()


def user_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "obox"


def migrate_legacy(legacy: Path, target: Path) -> None:
    if not legacy.is_dir() or legacy.resolve() == target.resolve():
        return
    target.mkdir(parents=True, exist_ok=True)
    config = legacy / "config.json"
    if config.is_file() and not (target / "config.json").exists():
        shutil.copy2(config, target / "config.json")
    for name in ("extensions", "storage"):
        source = legacy / name
        destination = target / name
        if source.is_dir() and not destination.exists():
            shutil.copytree(source, destination)


@dataclass(frozen=True)
class RuntimePaths:
    program_dir: Path
    data_dir: Path

    @property
    def config_path(self) -> Path:
        return self.data_dir / "config.json"

    @property
    def system_extensions(self) -> Path:
        return self.program_dir / "extensions"

    @property
    def user_extensions(self) -> Path:
        return self.data_dir / "extensions"

    @property
    def storage_dir(self) -> Path:
        return self.data_dir / "storage"

    @property
    def system_themes(self) -> Path:
        """安装目录的主题：优先 themes/，源码态回退 .theme。"""
        installed = self.program_dir / "themes"
        if installed.is_dir():
            return installed
        return self.program_dir / ".theme"

    @property
    def user_themes(self) -> Path:
        return self.data_dir / "themes"

    @property
    def themes_dir(self) -> Path:
        return self.system_themes

    def theme_dirs(self) -> list[Path]:
        return [self.system_themes, self.user_themes]

    def extension_dirs(self) -> list[Path]:
        return [self.system_extensions, self.user_extensions]


def resolve(program_dir: Path | None = None, data_dir: Path | None = None) -> RuntimePaths:
    installed = is_installed()
    if program_dir is None:
        env_program = os.environ.get("OBOX_PROGRAM_DIR")
        if env_program:
            program_dir = Path(env_program)
        elif installed:
            program_dir = Path(sys.executable).resolve().parent
        else:
            program_dir = Path(__file__).resolve().parent.parent
    if data_dir is None:
        env_data = os.environ.get("OBOX_DATA_DIR")
        data_dir = Path(env_data) if env_data else user_data_dir()
    paths = RuntimePaths(program_dir=Path(program_dir), data_dir=Path(data_dir))
    migrate_legacy(paths.program_dir / ".obox", paths.data_dir)
    return paths