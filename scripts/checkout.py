#!/usr/bin/env python3
"""Check the selected apps out into work/.

Shallow clones, because delivery never needs history. Reuses an existing
checkout when the branch already matches, so a warm runner or a local run does
not re-download 37 repositories.

    python3 scripts/checkout.py --apps all
    python3 scripts/checkout.py --apps CalcMaster,MyHealth
    python3 scripts/checkout.py --apps android-deliverable
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORK = ROOT / "work"


def load() -> dict:
    return json.loads((ROOT / "apps.json").read_text())


def select(manifest: dict, spec: str) -> list[dict]:
    apps = manifest["apps"]
    if spec in ("all", ""):
        return apps
    if spec == "android-deliverable":
        return [a for a in apps if a["deliverable"]["android"]]
    if spec == "ios-deliverable":
        return [a for a in apps if a["deliverable"]["ios"]]
    if spec == "ads":
        return [a for a in apps if a["ads"]]
    wanted = {s.strip().lower() for s in spec.split(",") if s.strip()}
    chosen = [a for a in apps if a["repo"].lower() in wanted]
    unknown = wanted - {a["repo"].lower() for a in chosen}
    if unknown:
        sys.exit(f"unknown app(s): {', '.join(sorted(unknown))}")
    return chosen


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> int:
    return subprocess.run(cmd, cwd=cwd).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps", default="all")
    ap.add_argument("--depth", type=int, default=1)
    args = ap.parse_args()

    manifest = load()
    WORK.mkdir(exist_ok=True)
    failed = []

    for app in select(manifest, args.apps):
        target = WORK / app["repo"]
        if (target / ".git").exists():
            code = run(["git", "-C", str(target), "fetch", "--depth", str(args.depth),
                        "origin", app["branch"]])
            code |= run(["git", "-C", str(target), "checkout", "-f", "FETCH_HEAD"])
        else:
            code = run(["git", "clone", "--depth", str(args.depth),
                        "--branch", app["branch"], app["url"], str(target)])
        if code:
            failed.append(app["repo"])
            print(f"::error::checkout failed for {app['repo']}")
        else:
            print(f"{app['repo']:20} {app['branch']} -> work/{app['repo']}/{app['dir']}")

    if failed:
        print(f"\n{len(failed)} checkout(s) failed: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
