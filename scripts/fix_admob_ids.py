#!/usr/bin/env python3
"""Replace Google's sample AdMob ids with this account's real ones.

    python3 scripts/fix_admob_ids.py --dry-run
    python3 scripts/fix_admob_ids.py

Nine of the eleven ad-serving apps ship `ca-app-pub-3940256099942544` — the
id Google publishes in its own documentation so a developer can test without
an account. Every one of them has a real id waiting in docs/admob-ids.json.

Shipping the sample id means two things, both bad: the app earns nothing,
and serving Google's test inventory from a production listing is against
the AdMob policy. Four of the nine are already live on Google Play.

The pattern is consistent — the iOS Info.plist carries the sample id in all
nine, and three also carry it in the Android manifest:

    ca-app-pub-3940256099942544~1458002511   Google's sample, iOS
    ca-app-pub-3940256099942544~3347511713   Google's sample, Android

Only the application id is rewritten here. Ad *unit* ids live in Dart and
differ per placement; `docs/admob-ids.json` has them for the apps that have
been issued them, and the rest are listed at the end rather than guessed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

SAMPLE = "ca-app-pub-3940256099942544"
APP_ID = re.compile(r"ca-app-pub-\d+~\d+")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    ids = json.loads((M / "docs/admob-ids.json").read_text())
    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]

    changed, missing = 0, []
    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        real = ids.get(repo) or {}
        targets = [
            (d / "android/app/src/main/AndroidManifest.xml", real.get("android_app_id")),
            (d / "ios/Runner/Info.plist", real.get("ios_app_id")),
        ]
        for f, want in targets:
            if not f.exists():
                continue
            src = f.read_text(errors="ignore")
            found = [i for i in APP_ID.findall(src) if SAMPLE in i]
            if not found:
                continue
            if not want:
                missing.append(f"{repo} {f.name}")
                continue
            new = src
            for bad in set(found):
                new = new.replace(bad, want)
            if new == src:
                continue
            if not args.dry_run:
                f.write_text(new)
            changed += 1
            print(f"  {repo:18} {f.name:22} {sorted(set(found))[0]} -> {want}",
                  flush=True)

    print(f"\n{'would replace' if args.dry_run else 'replaced'} {changed} sample id(s)")
    if missing:
        print("no real id on record, left alone:")
        for m in missing:
            print(f"  {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
