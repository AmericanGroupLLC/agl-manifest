#!/usr/bin/env python3
"""Which artifacts predate the last commit that could actually change them?

The platforms have different inputs, and conflating them produces false alarms:
a change to ios/Podfile.lock cannot alter an Android bundle, and an
android/ change cannot alter an IPA. An earlier version of this script checked
lib+android+ios against both artifacts and reported eight Android bundles as
stale when the only change was a screenshot commit touching ios/Podfile.lock.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path("/Users/spatchava/agl"); DIST = ROOT / ".dist"
apps = [a for a in json.loads((ROOT/"agl-manifest/apps.json").read_text())["apps"] if a.get("flutter")]

COMMON = ["lib", "pubspec.yaml", "assets"]
AAB_ONLY = ["android"]
IPA_ONLY = ["ios"]

def last_commit(repo: str, base: str, parts: list[str]) -> int:
    paths = [p if base == "." else f"{base}/{p}" for p in parts]
    r = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%ct", "--"] + paths,
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0

sa, si = [], []
for a in apps:
    repo = a["repo"]; base = a.get("dir", ".") or "."
    aab = max([p.stat().st_mtime for p in DIST.glob(f"{repo}-*.aab")], default=0)
    ipa = max([p.stat().st_mtime for p in
               list(DIST.glob(f"{repo}.ipa")) + list(DIST.glob(f"{repo}-*.ipa"))], default=0)
    if not aab or last_commit(repo, base, COMMON + AAB_ONLY) > aab:
        sa.append(repo)
    if not ipa or last_commit(repo, base, COMMON + IPA_ONLY) > ipa:
        si.append(repo)

print(f"AAB needs rebuild ({len(sa)}): {' '.join(sa) or 'none'}")
print(f"IPA needs rebuild ({len(si)}): {' '.join(si) or 'none'}")
json.dump({"aab": sa, "ipa": si}, open(ROOT/".dist/stale.json", "w"), indent=1)
