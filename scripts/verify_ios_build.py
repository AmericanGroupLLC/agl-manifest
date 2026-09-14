#!/usr/bin/env python3
"""Compile every app for a real iOS device, and record what happened.

Until now not one iOS artefact had ever been produced for any app in this
portfolio. Every "iOS ready" marker in the status tables meant something weaker
than it sounded: the Podfile exists, the Info.plist keys are present, the privacy
manifest is there. None of it was evidence that the app compiles.

`--no-codesign` is the point. A signed .ipa needs a distribution certificate that
does not exist yet (MANUAL_ACTIONS MA-005), but signing is the *last* step —
everything before it is the part that actually breaks: pod resolution, deployment
target conflicts, Swift version mismatches, plugins with no arm64 slice. This
runs all of that and stops short of the one step that needs a credential.

So a pass here means "this app compiles for an iPhone", not "this app can ship".
The distinction is recorded in the result rather than glossed, because the whole
reason this script exists is that a weaker claim had been reading as a stronger
one.

Artefacts are deleted after measuring. A Runner.app is ~30 MB and an ios/ build
tree far more; the useful output is whether it built and what broke.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/spatchava/agl")
MANIFEST = ROOT / "agl-manifest"
AUDIT = MANIFEST / "docs/release-readiness.json"
FLUTTER = ROOT / ".flutter-sdk/bin/flutter"
EVIDENCE = MANIFEST / "docs/ios-build-evidence.json"

# Same machine constraints as the Android build: the JVM is not involved here,
# but CocoaPods fetches specs over the network and the shell proxy variables are
# already exported, so nothing extra is needed. Kept explicit so a future reader
# does not wonder whether it was forgotten.
ENV_NOTE = "uses the shell's HTTP(S)_PROXY; CocoaPods honours it, unlike the JVM"


def apps() -> list[dict]:
    return [a for a in json.loads(AUDIT.read_text()) if a.get("flutter")]


def app_path(a: dict) -> pathlib.Path:
    base = ROOT / a["repo"]
    return base if a["app_dir"] == "." else base / a["app_dir"]


def first_error(out: str) -> str:
    """The line a human would actually need, not the last line printed."""
    patterns = [
        r"^Error: .*$",
        r"error: .*$",
        r"^\[!\] .*$",                      # CocoaPods
        r"Could not build the precompiled application.*$",
        r"required a higher minimum iOS.*$",
        r"^.*Swift Compiler Error.*$",
    ]
    for p in patterns:
        m = re.search(p, out, re.M)
        if m:
            return m.group(0).strip()[:300]
    tail = [ln for ln in out.splitlines() if ln.strip()]
    return "\n".join(tail[-6:])[:400]


def build(a: dict, timeout: int, keep: bool) -> dict:
    d = app_path(a)
    rec: dict = {"repo": a["repo"], "app_dir": a["app_dir"]}
    started = time.time()
    proc = subprocess.run(
        [str(FLUTTER), "build", "ios", "--release", "--no-codesign"],
        cwd=d, capture_output=True, text=True, timeout=timeout, env=dict(os.environ),
    )
    rec["seconds"] = round(time.time() - started, 1)

    m = re.search(r"✓\s*Built\s+(\S+Runner\.app)", proc.stdout)
    built = (d / m.group(1)) if m else (d / "build/ios/iphoneos/Runner.app")

    if built.exists():
        # du rather than walking the tree: a .app is thousands of small files and
        # the number is only wanted for the report.
        du = subprocess.run(["du", "-sk", str(built)], capture_output=True, text=True).stdout
        try:
            rec["mb"] = round(int(du.split()[0]) / 1024, 1)
        except (ValueError, IndexError):
            pass
        # "COMPILED", deliberately not "SIGNED" — see the module docstring.
        rec["result"] = "COMPILED"
    else:
        rec["result"] = "FAILED"
        rec["detail"] = first_error(proc.stdout + "\n" + proc.stderr)
        rec["exit_code"] = proc.returncode

    if not keep:
        shutil.rmtree(d / "build/ios", ignore_errors=True)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--keep", action="store_true", help="do not delete build/ios afterwards")
    args = ap.parse_args()

    todo = apps()
    if args.apps:
        want = set(args.apps)
        todo = [a for a in todo if a["repo"] in want]

    records = {r["repo"]: r for r in json.loads(EVIDENCE.read_text())} \
        if EVIDENCE.exists() else {}

    for i, a in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {a['repo']} ... ", end="", flush=True)
        try:
            rec = build(a, args.timeout, args.keep)
        except subprocess.TimeoutExpired:
            rec = {"repo": a["repo"], "app_dir": a["app_dir"],
                   "result": "TIMEOUT", "detail": f"exceeded {args.timeout}s"}
        rec["built_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        records[a["repo"]] = rec
        print(f"{rec['result']} ({rec.get('seconds', '?')}s)")
        EVIDENCE.write_text(json.dumps(sorted(records.values(), key=lambda r: r["repo"]), indent=2) + "\n")

    ok = sum(1 for r in records.values() if r.get("result") == "COMPILED")
    print(f"\n{ok} of {len(records)} compile for iOS device (unsigned). "
          f"Evidence in {EVIDENCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
