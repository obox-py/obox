#!/usr/bin/env python3
"""Archive one finished US change: changes/<US> -> changes/archive/<US>.

Usage:
  python archive_change.py --proj <df_proj_dir> --us <df_us_id> [--dry-run]

Prints one JSON object and exits 0 on success, 1 on refusal.
Archived changes stay on disk but leave the `changes/US-*` scan surface, so
df-env and df-init stop offering them as in-flight work.
"""
import argparse
import json
import os
import shutil
import sys


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
    args = ap.parse_args()

    proj = os.path.abspath(args.proj)
    changes = os.path.join(proj, "codespec", "changes")
    src = os.path.join(changes, args.us)
    archive = os.path.join(changes, "archive")
    dst = os.path.join(archive, args.us)

    if not os.path.isdir(src):
        return emit({"ok": False, "reason": "not-found", "path": src}, 1)
    if os.path.exists(dst):
        return emit({"ok": False, "reason": "already-archived", "path": dst}, 1)

    payload = {"ok": True, "dryRun": args.dry_run,
               "from": src.replace(os.sep, "/"), "to": dst.replace(os.sep, "/")}
    if args.dry_run:
        return emit(payload, 0)

    os.makedirs(archive, exist_ok=True)
    shutil.move(src, dst)
    payload["archived"] = True
    return emit(payload, 0)


if __name__ == "__main__":
    sys.exit(main())
