"""校验扩展目录：清单、视图文件、i18n.json。

用法：uv run python .agents/skills/obox-ext-dev/scripts/check_extension.py <扩展目录>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from obox.api.errors import ManifestError  # noqa: E402
from obox.extensions.manifest import load_manifest  # noqa: E402
from obox.i18n import I18nError, parse_document  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    target = Path((argv or sys.argv[1:])[0] if (argv or sys.argv[1:]) else ".").resolve()
    problems: list[str] = []
    try:
        manifest = load_manifest(target)
    except ManifestError as exc:
        print(f"[check] 清单不合法：{exc}", file=sys.stderr)
        return 1

    print(f"[check] 扩展 {manifest.extension_id} v{manifest.version}")
    for view in manifest.contributes.get("views", []):
        print(f"  视图 {view.get('id')} -> {view.get('container')}")
    for app in manifest.apps:
        print(f"  应用 {app['id']}（single={app['single']}, persistent={app['persistent']}）")
    for name in manifest.configuration:
        print(f"  配置 {manifest.extension_id}.{name}")

    i18n_path = target / "i18n.json"
    if i18n_path.is_file():
        try:
            entries = parse_document(json.loads(i18n_path.read_text(encoding="utf-8")), str(i18n_path))
            print(f"[check] i18n 条目 {len(entries)} 个")
        except (I18nError, json.JSONDecodeError) as exc:
            problems.append(f"i18n.json 不合法：{exc}")

    main_py = target / manifest.main
    if not main_py.is_file() and not (target / "extension.pyd").is_file():
        problems.append("缺少 extension.py 或 extension.pyd")
    if not manifest.contributes.get("views"):
        problems.append("没有声明视图")

    if problems:
        for problem in problems:
            print(f"[check] 失败：{problem}", file=sys.stderr)
        return 1
    print("[check] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())