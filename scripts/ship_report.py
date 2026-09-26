#!/usr/bin/env python3
"""One table saying, per app, how far it got and what is holding it.

    python3 scripts/ship_report.py            # markdown, for the job summary
    python3 scripts/ship_report.py --json

Reads what each stage actually wrote rather than what it claimed:

  * `docs/build-evidence.json`      — the Android bundle, and whether it is signed
  * `docs/ios-ipa-evidence.json`    — the IPA
  * `.dist/play-results.json`       — the Play internal upload
  * `.dist/ios-batch/results.json`  — the TestFlight upload

A blocked app and a broken app are shown differently on purpose. Nine apps have
no Play entry and thirteen have no App Store Connect record; those need a
console login and no amount of CI fixes them. Colouring them as failures would
bury a real regression in a wall of red that nobody reads twice.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as ROOT, DIST  # noqa: E402

# Store-side gates. Each is a console action, tracked in docs/MANUAL_ACTIONS.md.
BLOCKED_PATTERNS = {
    "Package not found": ("no Play entry", "MA-021"),
    "wrong key": ("upload-key reset needed", "MA-020"),
    "NOT_PUBLISHED": ("Play app still a Draft", "MA-022"),
    "does not allow 'CREATE'": ("no App Store Connect record", "MA-008"),
    "no ASC record": ("no App Store Connect record", "MA-008"),
}


def load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def classify(error: str) -> tuple[str, str] | None:
    for needle, (label, ref) in BLOCKED_PATTERNS.items():
        if needle in (error or ""):
            return label, ref
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    apps = load(ROOT / "apps.json", {}).get("apps", [])
    aab = {r["repo"]: r for r in load(ROOT / "docs/build-evidence.json", [])}
    ipa = {r["repo"]: r for r in load(ROOT / "docs/ios-ipa-evidence.json", [])}
    play = load(DIST / "play-results.json", {})
    tf = load(DIST / "ios-batch/results.json", {})

    rows, blocked, broken = [], [], []
    for a in apps:
        repo = a["repo"]
        row = {"app": repo}

        row["aab"] = "yes" if aab.get(repo, {}).get("result") in ("SIGNED", "BUILT") else "no"
        row["ipa"] = "yes" if ipa.get(repo, {}).get("result") == "EXPORTED" else "no"

        p = play.get(repo) or {}
        if p.get("status") == "uploaded":
            row["play"] = f"v{p.get('versionCode', '?')}"
        elif p:
            kind = classify(p.get("error", ""))
            row["play"] = f"blocked · {kind[0]}" if kind else "failed"
            (blocked if kind else broken).append((repo, "play", p.get("error", "")[:110]))
        else:
            row["play"] = "—"

        t = tf.get(repo) or {}
        if t.get("status") == "uploaded":
            row["testflight"] = t.get("build_number", "yes")
        elif t:
            kind = classify(str(t.get("error", "")))
            row["testflight"] = f"blocked · {kind[0]}" if kind else "failed"
            (blocked if kind else broken).append((repo, "testflight", str(t.get("error", ""))[:110]))
        else:
            row["testflight"] = "—"

        rows.append(row)

    if args.json:
        print(json.dumps({"apps": rows, "blocked": blocked, "broken": broken}, indent=1))
        return 0

    shipped_play = sum(1 for r in rows if r["play"].startswith("v"))
    shipped_tf = sum(1 for r in rows if r["testflight"] not in ("—",)
                     and not r["testflight"].startswith(("blocked", "failed")))

    print()
    print(f"**{len(rows)} apps.** Android bundle "
          f"{sum(1 for r in rows if r['aab'] == 'yes')}, IPA "
          f"{sum(1 for r in rows if r['ipa'] == 'yes')}, "
          f"Play internal {shipped_play}, TestFlight {shipped_tf}.")
    print()
    print("| app | aab | ipa | play internal | testflight |")
    print("| --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['app']} | {r['aab']} | {r['ipa']} | {r['play']} | {r['testflight']} |")

    if broken:
        print()
        print(f"### {len(broken)} real failure(s) — these are not store gates")
        for repo, where, err in broken:
            print(f"- **{repo}** ({where}): `{err}`")

    if blocked:
        print()
        print(f"### {len(blocked)} blocked by a console gate")
        print("These need a Play Console or App Store Connect login. See "
              "`README_STORE_SETUP.md`.")
        seen = {}
        for repo, _, err in blocked:
            kind = classify(err)
            seen.setdefault(kind[0] if kind else "other", []).append(repo)
        for label, repos in sorted(seen.items()):
            print(f"- **{label}**: {', '.join(sorted(set(repos)))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
