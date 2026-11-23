"""汇总静态检查、测试与各 US 基线校验。

用法：uv run python .agents/skills/obox-test/scripts/check_all.py [--skip-pytest] [--skip-baseline]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]


def run(command: list[str], cwd: Path) -> int:
    print(f"[check-all] $ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=cwd).returncode


def find_check_script() -> Path | None:
    for base in (REPO_ROOT / ".agents" / "skills", Path.home() / ".dsh" / "skills"):
        candidate = base / "df-validation" / "scripts" / "check.py"
        if candidate.is_file():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="obox 质量门禁汇总")
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-baseline", action="store_true")
    args = parser.parse_args(argv)

    failures: list[str] = []
    ruff = run([sys.executable, "-m", "ruff", "check", "obox", "tests", "scripts", "theme", "extensions", "--select", "F,E9"], REPO_ROOT)
    if ruff != 0:
        failures.append("ruff")

    if not args.skip_pytest:
        if run([sys.executable, "-m", "pytest", "-q"], REPO_ROOT) != 0:
            failures.append("pytest")

    if not args.skip_baseline:
        script = find_check_script()
        if script is None:
            print("[check-all] 找不到 check.py，跳过基线校验", file=sys.stderr)
        else:
            for change in sorted((REPO_ROOT / "codespec" / "changes").glob("US-*")):
                code = run(
                    [sys.executable, str(script), "--proj", str(REPO_ROOT), "--us", change.name, "--baseline-only"],
                    REPO_ROOT,
                )
                if code != 0:
                    failures.append(f"baseline:{change.name}")

    if failures:
        print(f"[check-all] 失败：{', '.join(failures)}", file=sys.stderr)
        return 1
    print("[check-all] 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
