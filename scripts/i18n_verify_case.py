#!/usr/bin/env python3
"""Check every restored literal against the file it came from, and fix it.

    python3 scripts/i18n_verify_case.py --dry-run --all
    python3 scripts/i18n_verify_case.py --all

i18n_restore_case.py paired removed literals with added keys *positionally
across a whole commit*, so a key used with two different capitalisations in
two files got one of them everywhere. RideZap is the case that caught it:

    price_breakdown.dart  'Total'   <- correct
    quote_tile.dart       'total'   <- correct

and both came back as 'total', which broke a test expecting "Total".

This compares each file against its own pre-i18n version. A literal the
original file never contained, in a case the original file *did* contain, is
put back the way that file had it. Nothing is inferred across files.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, flutter_bin  # noqa: E402

FLUTTER = str(flutter_bin())
LIT = re.compile(r"'([^'\n]{2,40})'")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    elif not args.all:
        raise SystemExit("name apps, or pass --all")

    total = 0
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        if not (d / "lib").exists():
            continue
        base = subprocess.run(["git", "log", "--format=%H", "-1", "--grep",
                               "Use the shared translations"], cwd=d,
                              capture_output=True, text=True).stdout.strip()
        if not base:
            continue

        root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=d,
                              capture_output=True, text=True).stdout.strip()
        n = 0
        for p in (d / "lib").rglob("*.dart"):
            rel = str(p.resolve()).replace(root + "/", "")
            before = subprocess.run(["git", "show", f"{base}~1:{rel}"], cwd=d,
                                    capture_output=True, text=True)
            if before.returncode != 0:
                continue
            old, src = before.stdout, p.read_text(errors="ignore")
            old_lits = set(LIT.findall(old))
            new = src
            for lit in set(LIT.findall(src)):
                if lit in old_lits:
                    continue
                # same text, different case, and the original file had it
                match = next((o for o in old_lits
                              if o.lower() == lit.lower() and o != lit), None)
                if not match:
                    continue
                new = new.replace(f"'{lit}'", f"'{match}'")
                n += 1
            if new != src and not args.dry_run:
                p.write_text(new)
        if not n:
            continue
        total += n
        print(f"  {repo:18} {'would fix' if args.dry_run else 'fixed'} {n}", flush=True)

        if args.dry_run:
            continue
        an = subprocess.run([FLUTTER, "analyze", "--no-fatal-infos"], cwd=d,
                            capture_output=True, text=True, timeout=1800)
        bad = [l.strip() for l in (an.stdout or "").splitlines()
               if " error " in l or " warning " in l]
        if bad:
            subprocess.run(["git", "checkout", "--", "lib"], cwd=d,
                           capture_output=True, text=True)
            print(f"  {repo:18} REVERTED — {bad[0][:110]}", flush=True)

    print(f"\nliterals corrected: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
