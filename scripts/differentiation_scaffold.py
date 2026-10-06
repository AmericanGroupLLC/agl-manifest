#!/usr/bin/env python3
"""Draft the 4.3 answer for each app, with the facts filled and the judgement left.

    python3 scripts/differentiation_scaffold.py --dry-run
    python3 scripts/differentiation_scaffold.py

Fourteen apps were rejected under Guidelines 4.3 (Spam) and 4.2.6 (App
Generation Services). Apple's reply asks, per app:

  1. what the app does and the problem it solves, not the marketing copy
  2. the specific target audience
  3. the gap it fills that existing apps do not
  4. the beta testing done, and feedback applied
  5. whether it is standalone or part of a suite, and if a suite, how its
     scope differs from the others

Questions 1, 2 and 5 are answerable from what this repository measures, so
they are filled in. Questions 3 and 4 are claims about the market and about
testing that actually happened; inventing them is exactly what 4.2.6 screens
for, so they are left as TODO with the question restated.

The result lands in `differentiation` in store/apps/<repo>.json, which
store_checklist.py requires before an app may be submitted. An app whose
TODOs are unfilled fails that check — which is the point.

Measured alongside, and worth knowing before answering question 3: no two of
the 43 apps share more than 22% of their description vocabulary. The copy is
not duplicated, so the 4.3 trigger is more likely the shared scaffold and the
submission volume than the words.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

TODO = "TODO"


def features_of(app_dir: pathlib.Path) -> list[str]:
    """Screen names, as a factual stand-in for 'what the app contains'."""
    out = []
    for sub in ("lib/screens", "lib/features", "lib/presentation/screens"):
        d = app_dir / sub
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            name = p.stem.replace("_screen", "").replace("_", " ").strip()
            if name and name not in out:
                out.append(name)
    return out[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]

    written = 0
    for a in manifest:
        repo = a["repo"]
        f = M / "store/apps" / f"{repo}.json"
        if not f.exists():
            continue
        rec = json.loads(f.read_text())
        en = (rec.get("copy") or {}).get("en") or {}
        d = ROOT / repo / (a.get("dir") or ".")
        feats = features_of(d)

        purpose = (en.get("description") or "").split("\n\n")[0].strip()
        audience = (en.get("subtitle") or "").strip()

        text = f"""1. WHAT IT DOES
{purpose or TODO + ': describe the primary problem this app solves.'}
Screens it contains: {', '.join(feats) if feats else TODO}

2. INTENDED USER
{audience or TODO + ': describe the specific target audience.'}

3. GAP IT FILLS
{TODO}: what does this app do that existing apps do not, or do less well?
Answer concretely — a named competitor and a named difference. This cannot
be drafted from the repository; it is a claim about the market.

4. BETA TESTING DONE
{TODO}: which builds went to testers, over what period, and name one change
made because of feedback. Nine external testers are configured on this app
in TestFlight; the testing itself still has to have happened.

5. STANDALONE OR PART OF A SUITE
Part of a suite: 43 apps are published under this developer account.
Category: {rec.get('primary_category') or TODO}.
{TODO}: state how this app's scope differs from the others in the suite.
Measured input: no two of the 43 apps share more than 22% of their
description vocabulary, so the copy is already distinct; the overlap Apple
is reacting to is more likely the shared code scaffold and the number of
apps submitted together.
"""
        if args.dry_run:
            print(f"  {repo:18} would draft {len(text)} chars, "
                  f"{text.count(TODO)} TODO(s)", flush=True)
            continue
        if rec.get("differentiation") == text:
            continue
        rec["differentiation"] = text
        f.write_text(json.dumps(rec, indent=1) + "\n")
        written += 1
        print(f"  {repo:18} drafted, {text.count(TODO)} TODO(s) left", flush=True)

    print(f"\ndrafts written: {written}")
    print("Each TODO is a question only a person can answer honestly. "
          "store_checklist.py fails an app until they are gone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
