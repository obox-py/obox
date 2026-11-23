"""构建 NSIS 安装包：准备安装树 → 生成 .nsi → 调 makensis。

用法：uv run python scripts/build_installer.py [--skip-exe] [--skip-theme]
产物：dist/obox-{version}-setup.exe
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from obox import __version__  # noqa: E402

BUILD = ROOT / "build"
DIST = ROOT / "dist"
STAGE = BUILD / "install"
TEMPLATE = ROOT / "installer" / "obox.nsi"
SYSTEM_EXTENSIONS = ("app", "settings")


def find_makensis() -> Path | None:
    for candidate in (
        Path("C:/Program Files (x86)/NSIS/makensis.exe"),
        Path("C:/Program Files/NSIS/makensis.exe"),
    ):
        if candidate.is_file():
            return candidate
    found = shutil.which("makensis")
    return Path(found) if found else None


def run_step(name: str, command: list[str]) -> int:
    print(f"[installer] {name}：{' '.join(command)}")
    return subprocess.run(command, cwd=ROOT).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建 obox NSIS 安装包")
    parser.add_argument("--skip-exe", action="store_true")
    parser.add_argument("--skip-theme", action="store_true")
    args = parser.parse_args(argv)

    exe = BUILD / "obox.dist" / "obox.exe"
    if not exe.exists() and not args.skip_exe:
        code = run_step("编译 exe", [sys.executable, "scripts/build_exe.py"])
        if code != 0:
            return code
    if not exe.exists():
        print("[installer] 缺少 build/obox.dist/obox.exe", file=sys.stderr)
        return 1

    theme_pyd = ROOT / ".theme" / "light" / "light.pyd"
    if not theme_pyd.exists() and not args.skip_theme:
        code = run_step("构建主题", [sys.executable, "scripts/build_theme.py"])
        if code != 0:
            return code
    if not theme_pyd.exists():
        print("[installer] 缺少 .theme/light/light.pyd", file=sys.stderr)
        return 1

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    shutil.copytree(BUILD / "obox.dist", STAGE, dirs_exist_ok=True)
    shutil.copytree(ROOT / ".theme", STAGE / ".theme", ignore=shutil.ignore_patterns("*.build"))
    for name in SYSTEM_EXTENSIONS:
        source = ROOT / "extensions" / name
        if not source.is_dir():
            print(f"[installer] 缺少系统扩展：{source}", file=sys.stderr)
            return 1
        shutil.copytree(source, STAGE / "extensions" / name, ignore=shutil.ignore_patterns("__pycache__"))

    makensis = find_makensis()
    if makensis is None:
        print(
            "[installer] 找不到 makensis，请先安装 NSIS（winget install NSIS.NSIS 或 https://nsis.sourceforge.io/）",
            file=sys.stderr,
        )
        return 2

    DIST.mkdir(parents=True, exist_ok=True)
    output = DIST / f"obox-{__version__}-setup.exe"
    if output.exists():
        output.unlink()
    script = BUILD / "obox.nsi"
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("__VERSION__", __version__)
    text = text.replace("__STAGE__", str(STAGE))
    text = text.replace("__OUTFILE__", str(output))
    script.write_text(text, encoding="utf-8-sig")

    code = run_step("编译安装包", [str(makensis), "/V2", str(script)])
    if code != 0:
        return code
    if not output.exists():
        print("[installer] makensis 结束但没有产物", file=sys.stderr)
        return 1
    print(f"[installer] 产物：{output}（{output.stat().st_size // 1024 // 1024} MB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
