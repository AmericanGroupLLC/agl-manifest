#!/usr/bin/env python3
"""Replace hardcoded UI strings with the shared agl_i18n translations.

    python3 scripts/i18n_adopt.py --dry-run           # report, change nothing
    python3 scripts/i18n_adopt.py Photriya            # one app, verified
    python3 scripts/i18n_adopt.py --all

26 apps wire agl_i18n into MaterialApp — delegates and 12 supportedLocales —
and then call it zero times, so every string renders in English whatever the
device is set to. docs/i18n-audit.json grades those "shell". This closes the
mechanical part of that gap: a literal that exactly matches one of the 66
shared English strings becomes `AglL10n.of(context)!.<key>`, which is already
translated into all 12 locales.

It is deliberately only the mechanical part. Of ~7,400 hardcoded strings
across the portfolio, roughly 660 match a shared key. The rest are app
copy — "Nearby guardians", "Compound Interest" — and need their own ARB
entries and a human translator. This script does not invent those.

The emitted form is `(AglL10n.of(context)?.key ?? 'Original English')`, not
`AglL10n.of(context)!.key`. The bang version compiles and analyzes clean and
then throws "Null check operator used on a null value" at runtime wherever
the agl delegates are not installed — which is every widget test that pumps
a bare MaterialApp. It cost 355 failing tests in GroceryMatch alone before
it was spotted, because the verification gate was analyze and analyze cannot
see a runtime null.

Two rules keep it safe:

  * a literal is only rewritten inside a `build(BuildContext context)` body,
    because `AglL10n.of(context)` needs a context in scope. Static field
    initialisers and plain helper methods are skipped even when the string
    matches.
  * every app is verified with `flutter analyze` afterwards and reverted in
    full if it does not come back clean.
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
IMPORT = "import 'package:agl_i18n/agl_i18n.dart';"

# Only these: a literal in one of them is UI text, not an identifier, asset
# path, route name or map key.
# The optional `const` is consumed, not just matched. `const Text('Save')`
# stops being a constant the moment the string becomes a method call, and
# Flutter rejects it: "Invalid constant value ... invalid_constant". That
# reverted the whole of Photriya on the first run.
PATTERN = re.compile(
    r"""(?P<const>\bconst\s+)?"""
    r"""(?P<lead>(?:Text|label|title|hintText|labelText|tooltip|helperText)\s*:?\s*\(?\s*)"""
    r"""(?P<q>['"])(?P<text>[^'"\n]{2,40})(?P=q)"""
)


# Three wordings for the same problem, and the bullet is U+2022. NewsBoard
# reverted because only the first was matched, then again because the regex
# had lost the whitespace before the bullet.
CONST_ERR = re.compile(
    r"error\s+\u2022\s+(?:"
    r"Invalid constant value[^\u2022]*"
    r"|The constructor being called isn't a const constructor[^\u2022]*"
    r"|The values in a const list literal must be constants[^\u2022]*"
    r")\s*\u2022\s*(\S+?):(\d+):(\d+)")   # \s* : [^\u2022]* already ate the space


def strip_enclosing_const(app_dir: pathlib.Path, analyze_output: str) -> int:
    """Remove the `const` that a newly localized string invalidated.

    The const is usually not on the Text itself but on a widget wrapping it —
    `const TextButton(child: Text('Settings'))` — so consuming a directly
    preceding `const` is not enough. The analyzer gives an exact file:line:col
    for every "Invalid constant value", and the const that caused it is the
    nearest one before that point. Removing it is what `dart fix` would do.
    """
    fixed = 0
    for rel, line_s, col_s in {m.groups() for m in CONST_ERR.finditer(analyze_output)}:
        f = app_dir / rel
        if not f.exists():
            continue
        src = f.read_text(errors="ignore")
        lines = src.split("\n")
        line = int(line_s) - 1
        if line >= len(lines):
            continue
        pos = sum(len(l) + 1 for l in lines[:line]) + int(col_s) - 1
        # Only a const that introduces a *widget*, i.e. `const Foo(` or
        # `const [`. Taking the nearest `const ` outright also matched
        # declarations like `const kPadding = 8;`, and removing that keyword
        # left "Variables must be declared using the keywords 'const',
        # 'final', 'var' or a type name" — which reverted NewsBoard,
        # portfolio-board and yourtube.
        hit = -1
        search = pos
        while True:
            cand = src.rfind("const ", 0, search)
            if cand < 0:
                break
            after = src[cand + len("const "):cand + len("const ") + 40].lstrip()
            if after[:1].isupper() or after[:1] in "[(<":
                hit = cand
                break
            search = cand
        if hit < 0:
            continue
        f.write_text(src[:hit] + src[hit + len("const "):])
        fixed += 1
    return fixed


def shared_strings():
    """(english-lowercased -> key, key -> english)."""
    arb = json.loads((M / "packages/agl_i18n/lib/l10n/agl_en.arb").read_text())
    pairs = {k: v for k, v in arb.items()
             if not k.startswith("@") and isinstance(v, str)}
    return {v.strip().lower(): k for k, v in pairs.items()}, pairs


def build_spans(src: str) -> list[tuple[int, int]]:
    """Character ranges of every `build(BuildContext context)` body."""
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


def convert(path: pathlib.Path, table: dict[str, str], en_text: dict[str, str]) -> int:
    src = path.read_text(errors="ignore")
    spans = build_spans(src)
    if not spans:
        return 0

    out, last, n = [], 0, 0
    for m in PATTERN.finditer(src):
        key = table.get(m.group("text").strip().lower())
        if not key:
            continue
        if not any(a < m.start() < b for a, b in spans):
            continue
        out.append(src[last:m.start()])
        eng = en_text[key].replace("\\", "\\\\").replace("'", "\\'")
        out.append(f"{m.group('lead')}(AglL10n.of(context)?.{key} ?? '{eng}')")
        last = m.end()
        n += 1
    if not n:
        return 0
    out.append(src[last:])
    new = "".join(out)

    if IMPORT not in new:
        lines = new.split("\n")
        at = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=-1)
        lines.insert(at + 1, IMPORT)
        new = "\n".join(lines)
    path.write_text(new)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    table, en_text = shared_strings()
    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    elif not args.all:
        raise SystemExit("name apps, or pass --all")

    report, changed_apps = {}, 0
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        lib = d / "lib"
        if not lib.exists():
            continue
        if "agl_i18n" not in (d / "pubspec.yaml").read_text(errors="ignore"):
            report[repo] = {"skipped": "does not depend on agl_i18n"}
            continue

        dirty = subprocess.run(["git", "status", "--porcelain", "--", "lib"],
                               cwd=d, capture_output=True, text=True).stdout.strip()
        if dirty:
            report[repo] = {"skipped": "lib has uncommitted changes"}
            print(f"  {repo:18} skipped — lib is dirty", flush=True)
            continue

        files = [p for p in lib.rglob("*.dart")
                 if "generated" not in str(p) and "/l10n/" not in str(p)]
        if args.dry_run:
            n = 0
            for p in files:
                src = p.read_text(errors="ignore")
                spans = build_spans(src)
                n += sum(1 for m in PATTERN.finditer(src)
                         if table.get(m.group("text").strip().lower())
                         and any(x < m.start() < y for x, y in spans))
            report[repo] = {"would_convert": n}
            print(f"  {repo:18} would convert {n}", flush=True)
            continue

        total = sum(convert(p, table, en_text) for p in files)
        if not total:
            report[repo] = {"converted": 0}
            print(f"  {repo:18} nothing to convert", flush=True)
            continue

        # Gate on errors, not the exit code. `flutter analyze` exits non-zero
        # for infos and warnings too, and most of these apps have plenty of
        # both — so an exit-code gate reverted a conversion whose repair had
        # already brought the error count to zero.
        def errors_of(res):
            return [l.strip() for l in (res.stdout or "").splitlines() if " error " in l]

        an = subprocess.run([FLUTTER, "analyze", "lib"], cwd=d,
                            capture_output=True, text=True, timeout=1800)
        # Repair rounds: removing one const can expose the next one further
        # out, and a deeply nested tree needs several passes. NewsBoard's
        # `const <NavigationDestination>[...]` list did not converge in four.
        for _ in range(8):
            if not errors_of(an) or not strip_enclosing_const(d, an.stdout or ""):
                break
            an = subprocess.run([FLUTTER, "analyze", "lib"], cwd=d,
                                capture_output=True, text=True, timeout=1800)
        if errors_of(an):
            subprocess.run(["git", "checkout", "--", "lib"], cwd=d,
                           capture_output=True, text=True)
            why = (errors_of(an) or [""])[0][:140]
            report[repo] = {"converted": 0, "reverted": total, "error": why}
            print(f"  {repo:18} REVERTED {total} — {why}", flush=True)
            continue

        report[repo] = {"converted": total}
        changed_apps += 1
        print(f"  {repo:18} converted {total}, analyze clean", flush=True)

    out = ROOT / ".dist" / "i18n-adopt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"\napps changed {changed_apps}; "
          f"total {sum(v.get('converted', 0) or v.get('would_convert', 0) for v in report.values())}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
