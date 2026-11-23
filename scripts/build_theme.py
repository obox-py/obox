"""把 theme 套件编译成 pyd，并复制清单到 .theme 产物目录。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES_SRC = ROOT / "theme"
THEMES_OUT = ROOT / ".theme"


def detect_compiler() -> list[str]:
    """有 Visual Studio 用 MSVC，否则让 Nuitka 走自带 MinGW64。"""
    candidates = [
        Path("C:/Program Files/Microsoft Visual Studio"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio"),
    ]
    if any(path.exists() for path in candidates):
        return ["--msvc=latest"]
    return ["--mingw64"]


def build_theme(name: str) -> Path:
    source = THEMES_SRC / name
    if not (source / "theme.json").exists():
        raise SystemExit(f"缺少清单：{source / 'theme.json'}")
    target = THEMES_OUT / name
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob("*.pyd"):
        try:
            stale.unlink()
        except PermissionError as exc:
            raise SystemExit(f"无法替换 {stale}：文件被占用，请先关闭正在运行的 obox") from exc
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--module",
        str(THEMES_SRC / "_build" / f"{name}.py"),
        "--include-package=theme",
        f"--output-dir={target}",
        "--remove-output",
        "--assume-yes-for-downloads",
        *detect_compiler(),
    ]
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        shutil.rmtree(target, ignore_errors=True)
        raise SystemExit(f"编译失败：{name}")
    fonts = source / "fonts"
    if fonts.is_dir():
        shutil.copytree(fonts, target / "fonts", dirs_exist_ok=True)
    shutil.copy(source / "theme.json", target / "theme.json")
    shutil.copy(source / "styles.qss", target / "styles.qss")
    canonical = target / f"{name}.pyd"
    candidates = sorted(target.glob("*.pyd"))
    if candidates and candidates[0].name != canonical.name:
        candidates[0].rename(canonical)
    produced = canonical
    if not produced.exists():
        shutil.rmtree(target, ignore_errors=True)
        raise SystemExit(f"没有产出 {produced}")
    return produced


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="编译 obox 主题套件")
    parser.add_argument("names", nargs="*", default=["light", "dark"], help="套件名，默认两套都编")
    args = parser.parse_args(argv)
    for name in args.names:
        print(f"[build] 编译 {name} ...")
        produced = build_theme(name)
        print(f"[build] 完成：{produced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())