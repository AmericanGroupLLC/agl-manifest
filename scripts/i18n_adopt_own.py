#!/usr/bin/env python3
"""Wire hardcoded strings to the app's *own* translations, where they exist.

    python3 scripts/i18n_adopt_own.py --dry-run --all
    python3 scripts/i18n_adopt_own.py CalcMaster

i18n_adopt.py covers the 66 strings shared across the portfolio. This covers
the other side: eleven apps carry their own multi-locale ARB, and 85 strings
in five of them are still hardcoded even though a translated key for that
exact text already exists. Nothing new is translated here — the words are
already in every locale the app ships, they were just never read.

Every lesson from the shared-string pass is applied, because each of them
cost a revert:

  * **Case-exact only.** Matching case-insensitively restyled 43 labels
    ('SIGN IN' -> 'Sign in'). A differently-cased key is not this string.
  * **Null-safe.** `AppLocalizations.of(context)!` throws "Null check
    operator used on a null value" in any test pumping a bare MaterialApp.
    The emitted form is `(AppLocalizations.of(context)?.key ?? 'English')`.
  * **Only inside a build(BuildContext context) body**, where there is a
    context to read.
  * **const is dropped** from the enclosing widget when the analyzer says the
    value is no longer constant, and the import is removed if it ends up
    unused — an unused import is a warning, and warnings fail analyze.
  * **Verified by analyze *and* the test suite**, reverted whole on either.
    Analyze alone cannot see a runtime null; that is how 355 failing tests
    got committed last time.
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
DART = str(pathlib.Path(FLUTTER).parent / "dart")
PATTERN = re.compile(
    r"""(?P<const>\bconst\s+)?"""
    r"""(?P<lead>(?:Text|label|title|hintText|labelText|tooltip|helperText)\s*:?\s*\(?\s*)"""
    r"""(?P<q>['"])(?P<text>[^'"\n]{2,60})(?P=q)"""
)
CONST_ERR = re.compile(
    r"error\s+•\s+(?:Invalid constant value[^•]*"
    r"|The constructor being called isn't a const constructor[^•]*"
    r"|The values in a const list literal must be constants[^•]*"
    r"|Methods can't be invoked in constant expressions[^•]*"
    r")\s*•\s*(\S+?):(\d+):(\d+)")


def build_spans(src: str):
    spans = []
    for m in re.finditer(r"\bbuild\s*\(\s*BuildContext\s+context\s*[,)]", src):
        i = src.find("{", m.end() - 1)
        if i < 0:
            continue
        depth, j = 0, i
        while j < len(src):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        spans.append((i, j))
    return spans


def strip_enclosing_const(app_dir: pathlib.Path, out: str) -> int:
    fixed = 0
    for rel, line_s, col_s in {m.groups() for m in CONST_ERR.finditer(out)}:
        f = app_dir / rel
        if not f.exists():
            continue
        src = f.read_text(errors="ignore")
        lines = src.split("\n")
        line = int(line_s) - 1
        if line >= len(lines):
            continue
        pos = sum(len(l) + 1 for l in lines[:line]) + int(col_s) - 1
        hit, limit = -1, min(len(src), pos + 6)
        while True:
            # +6 so a const that begins *at* the reported column is
            # still found. `return const MainShell();` reports the
            # column of `const` itself, and searching strictly before
            # it skipped the very keyword to remove — NewsBoard then
            # never converged.
            cand = src.rfind("const ", 0, limit)
            if cand < 0:
                break
            after = src[cand + 6:cand + 46].lstrip()
            # `_Badge` too: a private widget class starts with an
            # underscore, so an isupper() test alone skipped it and
            # CodeDeal never converged.
            if (after[:1].isupper() or after[:1] in "[(<"
                    or (after[:1] == "_" and after[1:2].isupper())):
                hit = cand
                break
            limit = cand
        if hit < 0:
            continue
        f.write_text(src[:hit] + src[hit + 6:])
        fixed += 1
    return fixed


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
        l10n = d / "lib/l10n"
        arb = l10n / "app_en.arb"
        if not arb.exists() or len(list(l10n.glob("*.arb"))) < 2:
            continue
        if subprocess.run(["git", "status", "--porcelain", "--", "lib"], cwd=d,
                          capture_output=True, text=True).stdout.strip():
            print(f"  {repo:18} skipped — lib is dirty", flush=True)
            continue

        gen = (list((d / "lib/l10n/generated").glob("app_localizations.dart"))
               or list((d / "lib/l10n").glob("app_localizations.dart")))
        if not gen:
            print(f"  {repo:18} skipped — no generated app_localizations.dart", flush=True)
            continue
        gen_file = gen[0]

        # Some apps generate `static AppLocalizations of(...)` — non-nullable,
        # and internally `Localizations.of<...>(context, ...)!`, so it *throws*
        # when the delegate is absent and a `?.` on the result never runs.
        # For those the safe read is Localizations.of directly. daily-pulse is
        # the case that caught it: 186 failing tests, all "HomeScreen not
        # found" because the app blew up before building.
        nullable_of = "static AppLocalizations? of(" in gen_file.read_text(errors="ignore")

        en = {k: v for k, v in json.loads(arb.read_text()).items()
              if not k.startswith("@") and isinstance(v, str)}
        exact = {v: k for k, v in en.items()}          # case-exact only

        n = 0
        for p in (d / "lib").rglob("*.dart"):
            if "generated" in str(p) or "/l10n/" in str(p):
                continue
            src = p.read_text(errors="ignore")
            spans = build_spans(src)
            if not spans:
                continue
            out, last, k = [], 0, 0
            for m in PATTERN.finditer(src):
                key = exact.get(m.group("text"))
                if not key or not any(x < m.start() < y for x, y in spans):
                    continue
                esc = m.group("text").replace("\\", "\\\\").replace("'", r"\'")
                out.append(src[last:m.start()])
                read = (f"AppLocalizations.of(context)?.{key}" if nullable_of
                        else f"Localizations.of<AppLocalizations>(context, "
                             f"AppLocalizations)?.{key}")
                out.append(f"{m.group('lead')}({read} ?? '{esc}')")
                last, k = m.end(), k + 1
            if not k:
                continue
            out.append(src[last:])
            new = "".join(out)
            # A *relative* import, computed per file. These apps do not use
            # package:flutter_gen — they import the generated file directly,
            # and the depth differs with where the file sits:
            #   CalcMaster  ../../l10n/generated/app_localizations.dart
            #   CodeDeal    l10n/app_localizations.dart
            if "app_localizations.dart" not in new:
                import os
                rel = os.path.relpath(gen_file, p.parent)
                lines = new.split("\n")
                at = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=-1)
                lines.insert(at + 1, f"import '{rel}';")
                new = "\n".join(lines)
            if not args.dry_run:
                p.write_text(new)
            n += k

        if not n:
            continue
        total += n
        print(f"  {repo:18} {'would wire' if args.dry_run else 'wired'} {n}", flush=True)
        if args.dry_run:
            continue

        def analyze():
            return subprocess.run([FLUTTER, "analyze", "--no-fatal-infos"], cwd=d,
                                  capture_output=True, text=True, timeout=1800)

        an = analyze()
        for _ in range(8):
            bad = [l for l in (an.stdout or "").splitlines() if " error " in l]
            if not bad or not strip_enclosing_const(d, an.stdout or ""):
                break
            an = analyze()

        subprocess.run([DART, "fix", "--apply", "lib"], cwd=d,
                       capture_output=True, text=True, timeout=1800)
        an = analyze()
        bad = [l.strip() for l in (an.stdout or "").splitlines()
               if " error " in l or " warning " in l]
        ok = not bad
        if ok:
            t = subprocess.run([FLUTTER, "test"], cwd=d,
                               capture_output=True, text=True, timeout=2400)
            ok = t.returncode == 0
            if not ok:
                bad = ["tests failed"]
        if not ok:
            subprocess.run(["git", "checkout", "--", "lib"], cwd=d,
                           capture_output=True, text=True)
            total -= n
            print(f"  {repo:18} REVERTED — {bad[0][:110]}", flush=True)
        else:
            print(f"  {repo:18} analyze + tests clean", flush=True)

    print(f"\nstrings wired to the app's own translations: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
