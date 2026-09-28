#!/usr/bin/env python3
"""Print the apps belonging to one shard, as a comma-separated list.

    python3 scripts/shard_apps.py 2/6            # every Flutter app, shard 2
    python3 scripts/shard_apps.py 2/6 --spec A,B # shard an explicit list

Used by the validate job, which analysed and tested all 43 apps serially and
took 60 of the pipeline's 146 minutes — long enough to be the bottleneck once
the Android build was sharded six ways and finished in about 50.

Round-robin, not contiguous slices, and for the same reason build_release.py
uses round-robin: the list is in name order, the slow apps are not evenly
spread, and contiguous blocks leave one runner working long after the rest
have gone home.

Prints nothing for an empty shard, which the caller must treat as "skip"
rather than as "every app" — an empty apps list means *all* to fastlane, so
getting this wrong runs the whole portfolio on six runners at once.
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
    ap.add_argument("shard", metavar="I/N", help="1-based shard, e.g. 2/6")
    ap.add_argument("--spec", default="all",
                    help="'all' or a comma-separated list of repo names")
    args = ap.parse_args()

    try:
        i, n = (int(x) for x in args.shard.split("/", 1))
    except ValueError:
        print(f"shard wants I/N, got {args.shard!r}", file=sys.stderr)
        return 2
    if not 1 <= i <= n:
        print(f"shard {args.shard} is out of range", file=sys.stderr)
        return 2

    apps = [a["repo"] for a in
            json.loads((MANIFEST / "apps.json").read_text())["apps"]
            if a.get("flutter")]
    if args.spec not in ("", "all"):
        wanted = [s.strip() for s in args.spec.split(",") if s.strip()]
        apps = [a for a in apps if a in wanted]

    print(",".join(a for k, a in enumerate(apps) if k % n == i - 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
