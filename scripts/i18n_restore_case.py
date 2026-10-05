#!/usr/bin/env python3
"""Undo the substitutions that silently changed a label's capitalisation.

    python3 scripts/i18n_restore_case.py --dry-run --all
    python3 scripts/i18n_restore_case.py --all

i18n_adopt.py matched literals against the shared English case-insensitively,
so a label whose case differed from the ARB was replaced by the ARB's wording:

    Text('SIGN IN')   -> 'Sign in'
    Text('share')     -> 'Share'
    Text('Clear All') -> 'Clear all'

43 labels across 13 apps changed that way. "SIGN IN" is a deliberate button
style and "share" is mid-sentence; neither is a translation improvement, and
nobody asked for the restyle. This puts those sites back to their original
literal and leaves them unlocalized, which is honest: the shared string does
not actually say what the app said.

The original wording is recovered from the diff of each app's
"Use the shared translations" commit, so nothing is guessed.
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


def originals(app_dir: pathlib.Path, en: dict[str, str]):
    """key -> original literal, for keys whose case the codemod changed."""
    sha = subprocess.run(["git", "log", "--format=%H", "-1", "--grep",
                          "Use the shared translations"], cwd=app_dir,
                         capture_output=True, text=True).stdout.strip()
    if not sha:
        return {}
    diff = subprocess.run(["git", "show", sha, "--", "lib"], cwd=app_dir,
                          capture_output=True, text=True).stdout
    removed = re.findall(r"^-.*?['\"]([^'\"\n]{2,40})['\"]", diff, re.M)
    added = re.findall(r"^\+.*?AglL10n\.of\(context\)!?\.(\w+)", diff, re.M)
    out = {}
    for lit, key in zip(removed, added):
        if key in en and en[key] != lit and en[key].lower() == lit.lower():
            out[key] = lit
    return out


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

    total = 0
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        if not (d / "lib").exists():
            continue
        wrong = originals(d, en)
        if not wrong:
            continue

        n = 0
        for p in (d / "lib").rglob("*.dart"):
            src = p.read_text(errors="ignore")
            new = src
            for key, lit in wrong.items():
                esc = lit.replace("\\", "\\\\").replace("'", r"\'")
                # Both forms: the bang version in case any survives.
                for pat in (rf"\(AglL10n\.of\(context\)\?\.{key} \?\? '[^']*'\)",
                            rf"AglL10n\.of\(context\)!\.{key}\b"):
                    new, k = re.subn(pat, f"'{esc}'", new)
                    n += k
            # Drop the import if nothing from agl_i18n is left. Restoring a
            # literal can remove a file's last AglL10n reference, and the
            # dangling import is a *warning* — which `flutter analyze
            # --no-fatal-infos` still fails on, so eight apps went red at
            # analyze after the first restore pass.
            if new != src:
                used = any(sym in new for sym in (
                    "AglL10n", "AglLocale", "aglLocalizationsDelegates",
                    "AglLanguageScreen", "AglLocales"))
                if not used:
                    new = re.sub(
                        r"^import 'package:agl_i18n/agl_i18n\.dart';\n", "",
                        new, flags=re.M)
            if new != src and not args.dry_run:
                p.write_text(new)
        if not n:
            continue
        total += n
        print(f"  {repo:18} {'would restore' if args.dry_run else 'restored'} {n}",
              flush=True)

        if args.dry_run:
            continue
        an = subprocess.run([FLUTTER, "analyze", "--no-fatal-infos"], cwd=d,
                            capture_output=True, text=True, timeout=1800)
        errs = [l.strip() for l in (an.stdout or "").splitlines()
                if " error " in l or " warning " in l]
        if errs:
            subprocess.run(["git", "checkout", "--", "lib"], cwd=d,
                           capture_output=True, text=True)
            print(f"  {repo:18} REVERTED — {errs[0][:110]}", flush=True)

    print(f"\nlabels restored: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
