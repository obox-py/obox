"""生成一个组件的两套骨架，并列出注册步骤。

用法：uv run python .agents/skills/obox-theme-dev/scripts/scaffold_component.py <tag> [--title 名称]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
TEMPLATE = SKILL_DIR / "templates" / "component.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 obox 组件骨架")
    parser.add_argument("tag", help="小写标签名，如 divider")
    parser.add_argument("--title", default="", help="显示名称")
    args = parser.parse_args(argv)
    tag = args.tag.strip().lower()
    if not tag.isalpha():
        print(f"[scaffold] 标签必须是小写字母：{tag}", file=sys.stderr)
        return 2
    class_name = tag.capitalize() + "Component"
    title = args.title or tag
    created = []
    for kit in ("light", "dark"):
        target = REPO_ROOT / "theme" / kit / "components" / f"{tag}.py"
        if target.exists():
            print(f"[scaffold] 已存在：{target}", file=sys.stderr)
            return 2
        text = TEMPLATE.read_text(encoding="utf-8")
        text = text.replace("__TAG__", tag).replace("__CLASS__", class_name).replace("__TITLE__", title)
        target.write_text(text, encoding="utf-8")
        created.append(target)
    print("[scaffold] 已生成：")
    for path in created:
        print(f"  {path}")
    print("[scaffold] 还需要手工完成：")
    print(f"  1. theme/{{light,dark}}/components/__init__.py 导出 {class_name}")
    print(f"  2. obox/ui/component_protocol.py 的 REQUIRED_TAGS 加入 \"{tag}\"")
    print("  3. 两处标签数断言 +1（tests/test_components.py、tests/test_kit_loader.py）")
    print("  4. uv run python scripts/build_theme.py && uv run pytest -q")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
