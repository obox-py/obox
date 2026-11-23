"""校验两套套件的组件契约。

用法：uv run python .agents/skills/obox-theme-dev/scripts/check_theme.py [--root 仓库根]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from obox.ui.component_protocol import (  # noqa: E402
    KitContractError,
    validate_component_class,
)
from obox.ui.kit import KitError, load_provider, scan_themes  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验主题套件契约")
    parser.add_argument("--root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    QApplication.instance() or QApplication([])

    kits = scan_themes(root / ".theme")
    if not kits:
        print("[check] 没有 .theme 产物，先运行 uv run python scripts/build_theme.py", file=sys.stderr)
        return 1

    from obox.ui.components import COMPONENT_TYPES

    failed = False
    for kit in kits:
        try:
            provider = load_provider(kit)
        except KitError as exc:
            print(f"[check] {kit.name}: 加载失败 {exc}", file=sys.stderr)
            failed = True
            continue
        palette = getattr(provider, "palette", None)
        if not isinstance(palette, dict) or not palette:
            print(f"[check] {kit.name}: 缺少 palette", file=sys.stderr)
            failed = True
            continue
        invalid = []
        for tag, component_type in COMPONENT_TYPES.items():
            try:
                validate_component_class(tag, component_type)
            except KitContractError as exc:
                invalid.append(f"{tag}: {exc}")
        print(f"[check] {kit.name}: {len(COMPONENT_TYPES)} 个宿主组件，调色板 {len(palette)} 项")
        for problem in invalid:
            print(f"[check]   {problem}", file=sys.stderr)
        if invalid:
            failed = True
    print("[check] OK" if not failed else "[check] FAILED", file=sys.stderr if failed else sys.stdout)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())