
#!/usr/bin/env python3
"""Merge {change}/delta-arch.md into docs/arch.md, then delete the per-change file.

Usage: python merge_arch.py --proj <df_proj_dir> --us <df_us_id> [--dry-run] [--keep]

The appended block is fenced by HTML comment markers so a second run is a no-op.
"""
import argparse
import json
import os
import sys

HEADER = "# 架构文档\n\n<!-- 基线由基线阶段维护；每个变更的增量分析在此按时间累积，块由 df-arch:<US> 界定。 -->\n"


def emit(payload, code):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", default=os.getcwd())
    ap.add_argument("--us", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep", action="store_true", help="合并后保留 delta-arch.md")
    args = ap.parse_args()

    proj = os.path.abspath(args.proj)
    change = os.path.join(proj, "codespec", "changes", args.us)
    docs = os.path.join(proj, "docs")
    src = os.path.join(change, "delta-arch.md")
    dst = os.path.join(docs, "arch.md")
    begin, end = "<!-- df-arch:%s -->" % args.us, "<!-- /df-arch:%s -->" % args.us

    merged = ""
    if os.path.exists(dst):
        with open(dst, "r", encoding="utf-8") as fh:
            merged = fh.read()

    already = begin in merged
    has_src = os.path.exists(src)
    if not has_src and not already:
        return emit({"ok": False, "reason": "not-found", "path": src}, 1)

    payload = {"ok": True, "dryRun": args.dry_run, "alreadyMerged": already,
               "from": src.replace(os.sep, "/"), "to": dst.replace(os.sep, "/")}
    if args.dry_run:
        return emit(payload, 0)

    if not already:
        with open(src, "r", encoding="utf-8") as fh:
            body = fh.read().rstrip() + "\n"
        os.makedirs(docs, exist_ok=True)
        base = merged.rstrip() + "\n\n" if merged.strip() else HEADER
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(base + begin + "\n" + body + end + "\n")
        payload["merged"] = True
    else:
        payload["merged"] = False

    if has_src and not args.keep:
        os.remove(src)
        payload["deleted"] = True

    return emit(payload, 0)


if __name__ == "__main__":
    sys.exit(main())
