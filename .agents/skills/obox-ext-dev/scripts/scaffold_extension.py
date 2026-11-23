"""生成一个可运行的 obox 扩展骨架。

用法：uv run python .agents/skills/obox-ext-dev/scripts/scaffold_extension.py <name> <publisher> [--title 标题] [--dir 目录]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
TEMPLATES = SKILL_DIR / "templates"


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"__{key}__", value)
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 obox 扩展骨架")
    parser.add_argument("name", help="扩展名，小写字母开头")
    parser.add_argument("publisher", help="作者标识，如 obox")
    parser.add_argument("--title", default="示例扩展", help="显示名称")
    parser.add_argument("--dir", default="extensions", help="目标父目录，默认 extensions")
    args = parser.parse_args(argv)

    if not args.name.replace("-", "").isalnum() or not args.name[0].isalpha():
        print(f"[scaffold] 非法扩展名：{args.name}", file=sys.stderr)
        return 2

    target = (REPO_ROOT / args.dir / args.name).resolve()
    if target.exists():
        print(f"[scaffold] 目标已存在：{target}", file=sys.stderr)
        return 2

    values = {"NAME": args.name, "PUBLISHER": args.publisher, "TITLE": args.title}
    files = {
        "extension.json": "extension.json",
        "extension.py": "extension.py",
        "views/main.oml": "views/main.oml",
        "i18n.json": "i18n.json",
        "assets/main.svg": "assets/main.svg",
    }
    target.mkdir(parents=True)
    for relative, template in files.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = TEMPLATES / template
        destination.write_text(render(source.read_text(encoding="utf-8"), values), encoding="utf-8")
    print(f"[scaffold] 已生成 {target}")
    print("[scaffold] 下一步：")
    print(f"  uv run python .agents/skills/obox-ext-dev/scripts/check_extension.py {target}")
    print("  uv run obox")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
