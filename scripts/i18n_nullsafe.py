#!/usr/bin/env python3
"""Make every shared-translation lookup degrade instead of crashing.

    python3 scripts/i18n_nullsafe.py --dry-run
    python3 scripts/i18n_nullsafe.py --all

`AglL10n.of(context)!.actionBack` compiles, analyzes clean, and throws

    Null check operator used on a null value

at runtime anywhere the agl localization delegates are not installed. That is
every widget test that pumps a bare MaterialApp, and it would be a shipped
crash too if an app ever lost its delegates. i18n_adopt.py emitted that form
and the analyze-only gate could not see it: GroceryMatch went to 355 failing
tests, all of them from one shared widget.

This rewrites each call to

    (AglL10n.of(context)?.actionBack ?? 'Back')

with the fallback taken from agl_en.arb, so the rendered text is exactly the
literal the codemod replaced in the first place.
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
CALL = re.compile(r"AglL10n\.of\(context\)!\.([A-Za-z_][A-Za-z0-9_]*)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    arb = json.loads((M / "packages/agl_i18n/lib/l10n/agl_en.arb").read_text())
    en = {k: v for k, v in arb.items() if not k.startswith("@") and isinstance(v, str)}

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    elif not args.all:
        raise SystemExit("name apps, or pass --all")

    report, touched = {}, 0
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        lib = d / "lib"
        if not lib.exists():
            continue

        files = [p for p in lib.rglob("*.dart")
                 if "generated" not in str(p) and "/l10n/" not in str(p)]
        n = 0
        for p in files:
            src = p.read_text(errors="ignore")
            if "AglL10n.of(context)!." not in src:
                continue

            def sub(m):
                nonlocal n
                key = m.group(1)
                if key not in en:
                    return m.group(0)
                n += 1
                esc = en[key].replace("\\", "\\\\").replace("'", r"\'")
                return f"(AglL10n.of(context)?.{key} ?? '{esc}')"

            new = CALL.sub(sub, src)
            if new != src and not args.dry_run:
                p.write_text(new)

        if not n:
            continue
        report[repo] = {"rewritten": n}
        touched += 1
        print(f"  {repo:18} {'would rewrite' if args.dry_run else 'rewrote'} {n}",
              flush=True)

        if args.dry_run:
            continue
        an = subprocess.run([FLUTTER, "analyze", "--no-fatal-infos", "lib"], cwd=d,
                            capture_output=True, text=True, timeout=1800)
        errs = [l.strip() for l in (an.stdout or "").splitlines() if " error " in l]
        if errs:
            subprocess.run(["git", "checkout", "--", "lib"], cwd=d,
                           capture_output=True, text=True)
            report[repo] = {"rewritten": 0, "reverted": n, "error": errs[0][:140]}
            print(f"  {repo:18} REVERTED — {errs[0][:110]}", flush=True)

    print(f"\napps touched {touched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
