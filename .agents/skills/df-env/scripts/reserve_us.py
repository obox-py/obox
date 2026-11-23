
import argparse, datetime, json, os, re, sys


def slugify(name: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]', "", name.strip())
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:20] or "change"


def main() -> int:
    ap = argparse.ArgumentParser(description="Atomically reserve a US change directory.")
    ap.add_argument("--proj", default=os.getcwd())
    ap.add_argument("--name", required=True, help="feature name from the prompt")
    ap.add_argument("--ts", default=None, help="override timestamp (YYYYmmddHHMMSS)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changes = os.path.join(os.path.abspath(args.proj), "codespec", "changes")
    os.makedirs(changes, exist_ok=True)
    ts = args.ts or datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    slug = slugify(args.name)

    idx = 0
    for name in os.listdir(changes):
        m = re.match(r"^US-\d{14}-(\d{4})-", name)
        if m:
            idx = max(idx, int(m.group(1)))

    for _ in range(50):
        idx += 1
        us = "US-%s-%04d-%s" % (ts, idx, slug)
        path = os.path.join(changes, us)
        if args.dry_run:
            if not os.path.exists(path):
                break
            continue
        try:
            os.mkdir(path)  # atomic: raises if it already exists
            break
        except FileExistsError:
            continue
    else:
        print(json.dumps({"ok": False, "reason": "index-exhausted"}, ensure_ascii=False))
        return 1

    print(json.dumps({"ok": True, "us_id": us, "path": path.replace(os.sep, "/"),
                      "index": idx, "dryRun": args.dry_run}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
