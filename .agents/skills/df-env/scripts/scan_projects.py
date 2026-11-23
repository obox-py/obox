#!/usr/bin/env python3
"""List every candidate project directory under a root, as a compact JSON string.

Usage:
  python scan_projects.py --root <dir> [--depth 4] [--limit 200]

Output (single line):
  {"root":"<abs>","dirs":["pkg-a","pkg-a/crates/b"],"truncated":false}

No scoring: relevance is the caller's judgement.
"""
import argparse
import json
import os
import sys

PRUNE = {
    "node_modules", "vendor", "target", "dist", "build", "out", "bin", "obj",
    ".venv", "venv", "__pycache__", ".next", ".git", ".idea", ".vs", ".gradle",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "coverage", ".turbo",
    "third_party", "external", "deps",
}

MARKERS = {
    "Cargo.toml", "go.mod", "go.work", "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt", "Pipfile", "poetry.lock", "uv.lock", "pom.xml",
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradlew", "CMakeLists.txt", "meson.build", "Makefile.am", "Makefile", "configure.ac",
    "package.json", "pnpm-workspace.yaml", "yarn.lock", "tsconfig.json",
    "index.html", "index.htm",
}

SUFFIXES = (".csproj", ".sln", ".fsproj", ".vcxproj")


def is_project(entries):
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            continue
        if entry.name in MARKERS or entry.name.lower().endswith(SUFFIXES):
            return True
    return False


def scan(root, depth, limit):
    dirs, scanned, truncated = [], 0, False
    stack = [(root, 0)]
    while stack:
        current, level = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        scanned += 1
        if scanned > limit:
            truncated = True
            break
        if is_project(entries):
            rel = os.path.relpath(current, root)
            dirs.append("." if rel == "." else rel.replace(os.sep, "/"))
        if level >= depth:
            continue
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            if entry.name in PRUNE or entry.name.startswith("."):
                continue
            stack.append((entry.path, level + 1))
    dirs.sort()
    return dirs, scanned, truncated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    dirs, scanned, truncated = scan(root, args.depth, args.limit)
    result = {"root": root.replace(os.sep, "/"), "dirs": dirs, "truncated": truncated}
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
