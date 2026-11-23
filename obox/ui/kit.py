"""主题套件（kit）的扫描、加载与切换。"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..api.errors import OboxError
from .component_protocol import validate_provider

CONTRACT_VERSION = 1
DEFAULT_THEME = "light"


class KitError(OboxError):
    code = "E_KIT"


@dataclass(frozen=True)
class KitInfo:
    """一套 UI 主题的清单与产物位置。"""

    name: str
    version: str
    mode: str
    entry: str
    directory: Path

    @property
    def pyd_path(self) -> Path:
        direct = self.directory / f"{self.name}.pyd"
        if direct.exists():
            return direct
        candidates = sorted(self.directory.glob("*.pyd"))
        return candidates[0] if candidates else direct


def scan_themes(themes_root: Path | list[Path] | tuple[Path, ...]) -> list[KitInfo]:
    """扫描一个或多个主题目录；同名时后面的目录优先。"""
    roots = [themes_root] if isinstance(themes_root, (str, Path)) else list(themes_root)
    kits: dict[str, KitInfo] = {}
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            manifest = directory / "theme.json"
            if not manifest.exists():
                continue
            try:
                raw = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            name = str(raw.get("name", directory.name))
            kits[name] = KitInfo(
                name=name,
                version=str(raw.get("version", "")),
                mode=str(raw.get("mode", "light")),
                entry=str(raw.get("entry", "create_ui_provider")),
                directory=directory,
            )
    return [kits[name] for name in sorted(kits)]


def select_kit(kits: list[KitInfo], wanted: str) -> KitInfo:
    """按名称挑一套；缺失时报出可用清单。"""
    for kit in kits:
        if kit.name == wanted:
            return kit
    available = "、".join(kit.name for kit in kits) or "无"
    raise KitError(f"找不到主题 {wanted}；可用：{available}")


def load_provider(kit: KitInfo) -> Any:
    """导入 pyd 并调用清单声明的工厂函数。"""
    if not kit.pyd_path.exists():
        raise KitError(f"缺少编译产物：{kit.pyd_path}")
    spec = importlib.util.spec_from_file_location(kit.name, kit.pyd_path)
    if spec is None or spec.loader is None:
        raise KitError(f"无法加载：{kit.pyd_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    factory = getattr(module, kit.entry, None)
    if factory is None:
        raise KitError(f"{kit.pyd_path} 里没有入口函数 {kit.entry}")
    provider = factory()
    validate_provider(provider)
    return provider