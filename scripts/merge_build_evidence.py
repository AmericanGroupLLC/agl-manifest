#!/usr/bin/env python3
"""Merge the per-shard build evidence back into one file.

    python3 scripts/merge_build_evidence.py            # aab
    python3 scripts/merge_build_evidence.py --kind apk

The Android build runs as six parallel shards, each writing
docs/build-evidence-shard<N>.json. Everything downstream — the release job, the
Play upload, ship_report.py, status.csv — reads docs/build-evidence.json, so the
shards have to be recombined before any of it runs.

Records are keyed on repo and the newest `built_at` wins, so re-running a single
shard updates only that shard's apps and leaves the rest of the portfolio's
evidence standing.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("aab", "apk"), default="aab")
    args = ap.parse_args()

    docs = MANIFEST / "docs"
    stem = "build-evidence" if args.kind == "aab" else "build-evidence-apk"
    target = docs / f"{stem}.json"

    records: dict[str, dict] = {}
    if target.exists():
        for r in json.loads(target.read_text()):
            records[r["repo"]] = r

    shards = sorted(docs.glob(f"{stem}-shard*.json"))
    if not shards:
        print(f"no {stem}-shard*.json to merge; leaving {target.name} as it is")
        return 0

    added = 0
    for shard in shards:
        for r in json.loads(shard.read_text()):
            old = records.get(r["repo"])
            if old is None or str(r.get("built_at", "")) >= str(old.get("built_at", "")):
                records[r["repo"]] = r
                added += 1

    target.write_text(
        json.dumps(sorted(records.values(), key=lambda r: r["repo"]), indent=2) + "\n")

    signed = sum(1 for r in records.values() if r.get("result") == "SIGNED")
    print(f"merged {len(shards)} shard file(s), {added} record(s) updated -> "
          f"{target.name}: {signed}/{len(records)} signed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
