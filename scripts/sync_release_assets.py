#!/usr/bin/env python3
"""Make each release's assets match the artefacts that were actually built.

Separate from publish_releases.py on purpose. That script creates releases and
writes notes; this one only answers "is the file that is on GitHub the file we
built?" and fixes it if not. Splitting them means a flaky upload can be retried
for as long as it takes without re-running release creation, and without the
retry logic tangling with the notes template.

Two things make that judgement, rather than assuming an upload worked:

  * an asset missing from the release entirely;
  * an asset whose size differs from the local artefact, which is what a
    truncated upload through a lossy proxy looks like. GitHub will happily serve
    a half-written 30 MB asset, and nothing about the release page says so.

This machine's egress proxy intermittently corrupts large bodies — "tls: bad
record MAC", "http2: client connection lost" — and gets worse under load. A run
of ten apps saw most uploads fail. So the retry budget here is deliberately
generous and the backoff long: the alternative is a release whose binaries are
silently absent, which is worse than a slow script.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402
ORG = "AmericanGroupLLC"
# Releases live in the monorepo since 2026-10-17 (app repos are archived); see
# publish_releases.py, which must agree with this on repo and tag.
RELEASE_REPO = f"{ORG}/agl-monorepo"
AUDIT = MANIFEST / "docs/release-readiness.json"
EVIDENCE = [MANIFEST / "docs/build-evidence.json", MANIFEST / "docs/build-evidence-apk.json"]


def gh_json(args: list[str]):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def wanted() -> dict[str, list[pathlib.Path]]:
    out: dict[str, list[pathlib.Path]] = {}
    for f in EVIDENCE:
        if not f.exists():
            continue
        for r in json.loads(f.read_text()):
            if r.get("result") != "SIGNED" or not r.get("artifact"):
                continue
            p = ROOT / r["artifact"]
            if p.exists():
                out.setdefault(r["repo"], []).append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    ap.add_argument("--attempts", type=int, default=12)
    args = ap.parse_args()

    audit = {a["repo"]: a for a in json.loads(AUDIT.read_text())}
    todo = wanted()
    if args.apps:
        todo = {k: v for k, v in todo.items() if k in set(args.apps)}
    todo.pop("Kinnav", None)   # outside the org; reachable only via a redirect

    missing_total = fixed = still_bad = 0
    for repo in sorted(todo):
        version = (audit.get(repo, {}).get("version") or "0.0.0").split("+")[0]
        tag = f"{repo}/v{version}-android"
        info = gh_json(["gh", "release", "view", tag, "--repo", RELEASE_REPO,
                        "--json", "assets"])
        if info is None:
            print(f"{repo:18} no release {tag} — run publish_releases.py first")
            continue
        have = {a["name"]: a["size"] for a in info.get("assets", [])}

        for artefact in todo[repo]:
            local = artefact.stat().st_size
            remote = have.get(artefact.name)
            if remote == local:
                continue
            why = "absent" if remote is None else f"size {remote} != {local}"
            missing_total += 1
            print(f"{repo:18} {artefact.name}: {why} — uploading", flush=True)

            for attempt in range(1, args.attempts + 1):
                r = subprocess.run(
                    ["gh", "release", "upload", tag, str(artefact),
                     "--repo", RELEASE_REPO, "--clobber"],
                    capture_output=True, text=True)
                if r.returncode == 0:
                    # Trust the check, not the exit code: a proxy that corrupts
                    # bodies can also produce a successful-looking short write.
                    chk = gh_json(["gh", "release", "view", tag, "--repo", RELEASE_REPO,
                                   "--json", "assets"]) or {}
                    got = {a["name"]: a["size"] for a in chk.get("assets", [])}.get(artefact.name)
                    if got == local:
                        print(f"{'':18}   ok on attempt {attempt}")
                        fixed += 1
                        break
                    print(f"{'':18}   attempt {attempt}: uploaded {got} of {local} bytes")
                else:
                    tail = (r.stderr.strip().splitlines() or ["?"])[-1]
                    print(f"{'':18}   attempt {attempt}: {tail[:90]}")
                time.sleep(min(10 * attempt, 60))
            else:
                still_bad += 1
                print(f"{'':18}   GAVE UP after {args.attempts} attempts")

    print(f"\n{missing_total} asset(s) needed fixing; {fixed} uploaded, {still_bad} still wrong")
    return 1 if still_bad else 0


if __name__ == "__main__":
    sys.exit(main())
