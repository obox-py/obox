#!/usr/bin/env python3
"""Map a project: source, config and doc files — far fewer than all files.

Usage:
  python scan_project.py --root <dir> [--limit 3000]

Skips codespec/ and build noise; counts only source/doc/config extensions so
binaries and vendored assets do not drown the map.

Output (single line, compact):
  {"root":"<abs>","files":42,"truncated":false,"exts":{".rs":30,".md":8},
   "dirs":{"crates/ui":12,"src":7},"docs":["README.md","docs/arch.md"]}
"""
import argparse
import json
import os
import sys

SKIP_DIRS = {
    "codespec", "node_modules", "vendor", "target", "dist", "build", "out",
    "bin", "obj", ".git", ".venv", "venv", "__pycache__", ".next", ".idea",
    ".vs", ".gradle", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "coverage", ".turbo", "third_party", "external", "deps", "fixtures",
}

KEEP_EXTS = {
    ".rs", ".go", ".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".vue", ".svelte", ".java", ".kt", ".kts", ".scala", ".c", ".h", ".cc",
    ".cpp", ".hpp", ".cs", ".fs", ".rb", ".php", ".swift", ".lua", ".dart",
    ".ex", ".exs", ".erl", ".hs", ".ml", ".clj", ".sol", ".sql", ".graphql",
    ".proto", ".wit", ".sh", ".bash", ".ps1", ".bat", ".html", ".css", ".scss",
    ".less", ".md", ".mdx", ".rst", ".adoc", ".txt", ".toml", ".yaml", ".yml",
    ".json", ".ini", ".cfg", ".conf", ".xml", ".gradle", ".cmake", ".mk",
}

KEEP_NAMES = {"makefile", "dockerfile", "justfile", "procfile", "vagrantfile", "cmakelists.txt"}

DOC_EXTS = {".md", ".mdx", ".rst", ".adoc", ".txt"}


def keep(name):
    low = name.lower()
    if low in KEEP_NAMES:
        return True
    return os.path.splitext(low)[1] in KEEP_EXTS


def scan(root, limit):
    exts, dirs, docs = {}, {}, []
    total, truncated = 0, False
    for current, subdirs, files in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS and not d.startswith("."))
        rel_dir = os.path.relpath(current, root)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        for name in sorted(files):
            if not keep(name):
                continue
            total += 1
            if total > limit:
                truncated = True
                break
            ext = os.path.splitext(name)[1].lower() or "(none)"
            exts[ext] = exts.get(ext, 0) + 1
            key = rel_dir or "."
            dirs[key] = dirs.get(key, 0) + 1
            if ext in DOC_EXTS and len(docs) < 40:
                docs.append((rel_dir + "/" + name).lstrip("/"))
        if truncated:
            break
    top_dirs = dict(sorted(dirs.items(), key=lambda kv: -kv[1])[:20])
    return {"files": total, "truncated": truncated, "exts": exts, "dirs": top_dirs, "docs": docs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--limit", type=int, default=3000)
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    result = {"root": root.replace(os.sep, "/")}
    result.update(scan(root, args.limit))
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
