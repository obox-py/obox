"""把扩展目录打包成 .oix：源码编译为 pyd，连同清单与资产压成 zip。"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from obox.extensions.manifest import load_manifest  # noqa: E402


def detect_compiler() -> list[str]:
    candidates = [
        Path("C:/Program Files/Microsoft Visual Studio"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio"),
    ]
    return ["--msvc=latest"] if any(path.exists() for path in candidates) else ["--mingw64"]


def local_modules(entry: Path) -> list[Path]:
    """从入口出发收集扩展目录内可达的 .py 文件。"""
    root = entry.parent
    seen: set[Path] = {entry}
    queue: list[Path] = [entry]
    while queue:
        current = queue.pop()
        try:
            tree = ast.parse(current.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            raise SystemExit(f"解析失败 {current}：{exc}") from exc
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.module:
                        names = [node.module]
                elif node.module:
                    names = [node.module]
            for name in names:
                relative = Path(*name.split("."))
                for candidate in (root / relative.with_suffix(".py"), root / relative / "__init__.py"):
                    if candidate.exists() and candidate not in seen:
                        seen.add(candidate)
                        queue.append(candidate)
    return sorted(seen)


def compile_module(source: Path, output: Path) -> Path:
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--module",
        str(source),
        f"--output-dir={output}",
        "--nofollow-imports",
        "--remove-output",
        "--assume-yes-for-downloads",
        *detect_compiler(),
    ]
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"编译失败：{source.name}")
    produced = sorted(output.glob(f"{source.stem}*.pyd"))
    if not produced:
        raise SystemExit(f"没有产出 {source.stem}.pyd")
    target = output / f"{source.stem}.pyd"
    if produced[0] != target:
        if target.exists():
            target.unlink()
        produced[0].rename(target)
    return target


def build(extension_dir: Path, dist_dir: Path, dry_run: bool = False) -> Path:
    manifest = load_manifest(extension_dir)
    entry = extension_dir / "extension.py"
    if not entry.exists():
        raise SystemExit(f"入口不存在：{entry}")
    modules = local_modules(entry)
    print(f"[pack] 本地模块 {len(modules)} 个：{', '.join(path.name for path in modules)}")
    if dry_run:
        return extension_dir

    dist_dir.mkdir(parents=True, exist_ok=True)
    target = dist_dir / f"{manifest.name}.{manifest.publisher}.{manifest.version}.oix"
    with tempfile.TemporaryDirectory(prefix="obox-pack-") as workspace:
        built = Path(workspace)
        for module in modules:
            print(f"[pack] 编译 {module.name} ...")
            compile_module(module, built)
        staging = built / "package"
        staging.mkdir()
        for pyd in built.glob("*.pyd"):
            shutil.copy(pyd, staging / pyd.name)
        for name in ("extension.json", "i18n.json"):
            path = extension_dir / name
            if path.is_file():
                shutil.copy(path, staging / name)
        for folder in ("assets", "views"):
            source = extension_dir / folder
            if source.is_dir():
                shutil.copytree(source, staging / folder)
        partial = target.with_suffix(".oix.part")
        with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(staging).as_posix())
        partial.replace(target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把扩展目录打包成 .oix")
    parser.add_argument("extension", help="扩展目录，例如 extensions/gallery")
    parser.add_argument("--dist", default="dist", help="产物目录，默认 dist")
    parser.add_argument("--dry-run", action="store_true", help="只打印可达模块，不编译不打包")
    args = parser.parse_args(argv)
    extension_dir = Path(args.extension).resolve()
    dist_dir = Path(args.dist).resolve()
    produced = build(extension_dir, dist_dir, args.dry_run)
    if not args.dry_run:
        print(f"[pack] 产物：{produced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
