"""用 Nuitka 把 obox 编译成 standalone 可执行目录。

用法：uv run python scripts/build_exe.py [--force]
产物：build/obox.dist/obox.exe（含 Nuitka 运行时文件）
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DIST = BUILD / "obox.dist"


def _render_icon() -> Path | None:
    """由 obox.svg 生成 256px 的 ico；失败时返回 None 并在调用处记日志。"""
    source = ROOT / "obox" / "assets" / "obox.svg"
    target = ROOT / "obox" / "assets" / "obox.ico"
    if not source.exists():
        return None
    try:
        import os

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from obox.qt import QByteArray, Qt
        from obox.qt import QImage, QPainter
        from obox.qt import QSvgRenderer
        from obox.qt import QApplication

        QApplication.instance() or QApplication([])
        renderer = QSvgRenderer(QByteArray(source.read_bytes()))
        image = QImage(256, 256, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        if not image.save(str(target), "ICO"):
            return None
    except (ImportError, OSError, RuntimeError) as exc:
        print(f"[exe] 生成图标失败：{exc}", file=sys.stderr)
        return None
    print(f"[exe] 已生成图标：{target}")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="编译 obox standalone")
    parser.add_argument("--force", action="store_true", help="已存在也重新编译")
    parser.add_argument("--qt", choices=["pyside6", "pyqt5"], default="pyside6", help="选择 Qt 绑定")
    args = parser.parse_args(argv)
    os.environ["OBOX_QT"] = args.qt

    if (DIST / "obox.exe").exists() and not args.force:
        print(f"[exe] 已存在：{DIST / 'obox.exe'}")
        return 0

    BUILD.mkdir(parents=True, exist_ok=True)
    entry = BUILD / "entry.py"
    entry.write_text("from obox.main import main\n\nraise SystemExit(main())\n", encoding="utf-8")

    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        f"--enable-plugin={'pyqt5' if args.qt == 'pyqt5' else 'pyside6'}",
        f"--nofollow-import-to={'PySide6' if args.qt == 'pyqt5' else 'PyQt5'}",
        "--include-package=obox",
        "--include-package-data=obox",
        "--windows-console-mode=disable",
        "--assume-yes-for-downloads",
        f"--output-dir={BUILD}",
    ]
    icon = ROOT / "obox" / "assets" / "obox.ico"
    if not icon.exists():
        icon = _render_icon()
    if icon is not None and icon.exists():
        command.append(f"--windows-icon-from-ico={icon}")
    else:
        print("[exe] 未找到或未能生成 obox.ico，产物将不带图标", file=sys.stderr)
    command.append(str(entry))
    print(f"[exe] {' '.join(command)}")
    code = subprocess.run(command, cwd=ROOT).returncode
    if code != 0:
        print("[exe] Nuitka 编译失败", file=sys.stderr)
        return code

    candidates = sorted(BUILD.glob("entry.dist"))
    if not candidates:
        print("[exe] 没找到 Nuitka 输出目录 entry.dist", file=sys.stderr)
        return 1
    produced = candidates[0]
    if DIST.exists():
        shutil.rmtree(DIST)
    produced.rename(DIST)
    for name in ("entry.exe", "main.exe"):
        exe = DIST / name
        if exe.exists():
            exe.rename(DIST / "obox.exe")
            break
    if not (DIST / "obox.exe").exists():
        print("[exe] 输出目录里没有可执行文件", file=sys.stderr)
        return 1
    print(f"[exe] 产物：{DIST / 'obox.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())