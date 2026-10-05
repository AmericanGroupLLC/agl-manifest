#!/usr/bin/env python3
"""Give an app the shared translations it does not have yet.

    python3 scripts/i18n_bootstrap.py --dry-run --all
    python3 scripts/i18n_bootstrap.py AeroSwift

Five apps have no internationalization at all — no agl_i18n dependency, no
supportedLocales, every string English and hardcoded. docs/i18n-audit.json
grades them "none". This adds the three things they are missing:

  1. the agl_i18n git dependency in pubspec.yaml;
  2. `localizationsDelegates: aglLocalizationsDelegates(null)` and
     `supportedLocales: AglLocales.standard` on MaterialApp;
  3. the import.

It deliberately stops there. Wiring the strings themselves is
i18n_adopt.py's job, run afterwards, so each step is verifiable on its own.

Verified per app with `flutter analyze` and the full test suite, and reverted
whole on either — including pubspec.yaml, because a half-added dependency is
worse than none.
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
DEP = """  agl_i18n:
    git:
      url: https://github.com/AmericanGroupLLC/agl-manifest.git
      path: packages/agl_i18n
      ref: master
"""
IMPORT = "import 'package:agl_i18n/agl_i18n.dart';"


def add_dep(pubspec: pathlib.Path) -> bool:
    t = pubspec.read_text()
    if "agl_i18n" in t:
        return False
    m = re.search(r"^dependencies:\s*$", t, re.M)
    if not m:
        return False
    at = m.end() + 1
    pubspec.write_text(t[:at] + DEP + t[at:])
    return True


def wire_material_app(lib: pathlib.Path) -> pathlib.Path | None:
    """Add the delegates and locales to the one MaterialApp that has neither."""
    for p in lib.rglob("*.dart"):
        src = p.read_text(errors="ignore")
        if "MaterialApp(" not in src or "supportedLocales" in src:
            continue
        new = src.replace(
            "MaterialApp(",
            "MaterialApp(\n"
            "      localizationsDelegates: aglLocalizationsDelegates(null),\n"
            "      supportedLocales: AglLocales.standard,", 1)
        if IMPORT not in new:
            lines = new.split("\n")
            at = max((i for i, l in enumerate(lines) if l.startswith("import ")), default=-1)
            lines.insert(at + 1, IMPORT)
            new = "\n".join(lines)
        p.write_text(new)
        return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    audit = {r["repo"]: r for r in
             json.loads((M / "docs/i18n-audit.json").read_text())["apps"]}
    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]
    elif not args.all:
        raise SystemExit("name apps, or pass --all")

    done = 0
    for a in manifest:
        repo = a["repo"]
        if (audit.get(repo) or {}).get("grade") != "none":
            continue
        d = ROOT / repo / (a.get("dir") or ".")
        if not (d / "lib").exists():
            continue
        # Only what this script touches, and only tracked changes. A plain
        # `git status --porcelain` also reports an untracked ios/Podfile.lock,
        # which is a build artifact and no reason to skip the app.
        if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no",
                           "--", "lib", "pubspec.yaml"], cwd=d,
                          capture_output=True, text=True).stdout.strip():
            print(f"  {repo:18} skipped — lib or pubspec has local changes", flush=True)
            continue
        if args.dry_run:
            print(f"  {repo:18} would add agl_i18n and wire MaterialApp", flush=True)
            continue

        if not add_dep(d / "pubspec.yaml"):
            print(f"  {repo:18} pubspec already has it", flush=True)
        target = wire_material_app(d / "lib")
        if not target:
            subprocess.run(["git", "checkout", "--", "lib", "pubspec.yaml"], cwd=d,
                           capture_output=True, text=True)
            print(f"  {repo:18} no un-wired MaterialApp found", flush=True)
            continue

        pg = subprocess.run([FLUTTER, "pub", "get"], cwd=d,
                            capture_output=True, text=True, timeout=1800)
        # flutter_localizations, which agl_i18n pulls in, requires exactly the
        # intl the SDK ships. An app pinning a higher patch cannot resolve:
        #   every version of agl_i18n depends on flutter_localizations from
        #   sdk which depends on intl 0.20.2, [...] version solving failed
        # Relaxing the caret to that version keeps the app's intent — same
        # major/minor — and lets both resolve.
        blob = (pg.stdout or "") + (pg.stderr or "")
        m = re.search(r"depends on intl (\d+\.\d+\.\d+)", blob)
        if pg.returncode != 0 and m:
            ps = d / "pubspec.yaml"
            txt = ps.read_text()
            relaxed = re.sub(r"^(\s*intl:\s*)\^[\d.]+$",
                             rf"\g<1>^{m.group(1)}", txt, flags=re.M)
            if relaxed != txt:
                ps.write_text(relaxed)
                print(f"  {repo:18} relaxed intl to ^{m.group(1)}", flush=True)
                pg = subprocess.run([FLUTTER, "pub", "get"], cwd=d,
                                    capture_output=True, text=True, timeout=1800)
        an = subprocess.run([FLUTTER, "analyze", "--no-fatal-infos"], cwd=d,
                            capture_output=True, text=True, timeout=1800)
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
            subprocess.run(["git", "checkout", "--", "lib", "pubspec.yaml"], cwd=d,
                           capture_output=True, text=True)
            print(f"  {repo:18} REVERTED — {bad[0][:110]}", flush=True)
            continue
        done += 1
        print(f"  {repo:18} wired via {target.relative_to(d)}, analyze + tests clean",
              flush=True)

    print(f"\napps given the shared translations: {done}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
