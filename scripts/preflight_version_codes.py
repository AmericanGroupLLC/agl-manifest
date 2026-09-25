#!/usr/bin/env python3
"""Refuse to build bundles Play will reject, and optionally raise them.

    python3 scripts/preflight_version_codes.py --check   # exit 1 if any app is behind
    python3 scripts/preflight_version_codes.py --bump    # raise each pubspec past Play

Play rejects a bundle whose version code it has already seen —
`Version code 2 has already been used.` — and the code is baked into the .aab
at build time from `pubspec.yaml`'s `version: x.y.z+N`. Rebuilding the same
version therefore cannot fix a collision.

On 2026-09-25 that cost a full 43-app rebuild: the bundles were produced first
and only then found to be unuploadable. This runs *before* the build so the
pipeline fails in seconds instead of hours.

The next free code is read from Play's own `bundles` list per package, not from
any local record — a local record only knows about uploads from this machine,
and two apps turned out to hold codes on Play that nothing here had written
down.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CODES = pathlib.Path("/Users/spatchava/agl/.dist/play-version-codes.json")


def app_dir(a: dict) -> pathlib.Path:
    d = a.get("dir") or "."
    base = ROOT.parent / a["repo"]
    # In CI the apps live under the manifest's work/ directory instead.
    work = ROOT / "work" / a["repo"]
    root = work if work.exists() else base
    return root if d == "." else root / d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--bump", action="store_true")
    ap.add_argument("--codes", default=str(CODES),
                    help="output of scripts/play_version_codes.py")
    args = ap.parse_args()
    if not (args.check or args.bump):
        ap.error("pass --check or --bump")

    codes_path = pathlib.Path(args.codes)
    if not codes_path.exists():
        print(f"::error::{codes_path} is missing. Run "
              f"scripts/play_version_codes.py first.")
        return 1
    codes = json.loads(codes_path.read_text())
    apps = json.loads((ROOT / "apps.json").read_text())["apps"]

    behind, bumped, skipped = [], [], []
    for a in apps:
        repo = a["repo"]
        info = codes.get(repo, {})
        if info.get("state") != "OK":
            skipped.append(repo)
            continue
        pub = app_dir(a) / "pubspec.yaml"
        if not pub.exists():
            print(f"::warning::{repo}: no pubspec at {pub}")
            continue
        text = pub.read_text()
        m = re.search(r"^(version:\s*)([0-9.]+)\+(\d+)", text, re.M)
        if not m:
            print(f"::warning::{repo}: no 'version: x.y.z+N' line")
            continue
        name, current, nxt = m.group(2), int(m.group(3)), int(info["next"])
        if current >= nxt:
            continue
        behind.append((repo, f"{name}+{current}", f"{name}+{nxt}"))
        if args.bump:
            pub.write_text(text[:m.start()] + f"{m.group(1)}{name}+{nxt}"
                           + text[m.end():])
            bumped.append(repo)

    if skipped:
        print(f"{len(skipped)} app(s) have no Play listing, so no code to "
              f"clash with: {' '.join(sorted(skipped))}")

    if not behind:
        print("Every app's build number is already past what Play holds.")
        return 0

    for repo, cur, nxt in behind:
        print(f"  {repo:18} {cur}  ->  {nxt}")

    if args.bump:
        print(f"\nRaised {len(bumped)} pubspec version(s). Commit them, or the "
              f"next build produces the same collision.")
        return 0

    print(f"\n::error::{len(behind)} app(s) would be rejected by Play for a "
          f"duplicate version code. Run with --bump, commit, and rebuild.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
