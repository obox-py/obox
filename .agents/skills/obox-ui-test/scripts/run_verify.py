"""跑 light/dark 两套界面验证并汇总。

用法：uv run python .agents/skills/obox-ui-test/scripts/run_verify.py [--themes light,dark] [--no-show]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
VERIFY = REPO_ROOT / "scripts" / "verify_ui.py"
PICS = REPO_ROOT / "tmp" / "pics"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="跑 obox 界面验证")
    parser.add_argument("--themes", default="light,dark")
    parser.add_argument("--no-show", action="store_true", help="不显示窗口（默认就不显示，保留参数兼容）")
    args = parser.parse_args(argv)

    themes = [theme.strip() for theme in args.themes.split(",") if theme.strip()]
    results: list[tuple[str, int]] = []
    for theme in themes:
        command = [sys.executable, str(VERIFY)]
        if theme != "light":
            command += ["--theme", theme]
        print(f"[ui-test] 运行 {theme} ...", flush=True)
        code = subprocess.run(command, cwd=REPO_ROOT).returncode
        results.append((theme, code))
        shots = sorted(PICS.glob(f"{theme}_*.png"))
        print(f"[ui-test] {theme} 退出码 {code}，截图 {len(shots)} 张：{shots[-1].name if shots else '无'}")

    failed = [theme for theme, code in results if code != 0]
    print("[ui-test] 汇总：" + "，".join(f"{theme}={'PASS' if code == 0 else 'FAIL'}" for theme, code in results))
    if failed:
        print(f"[ui-test] 失败主题：{', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
