#!/usr/bin/env python3
"""Build dynamic shard matrices for GitHub Actions jobs."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Any


def _load_apps(path: pathlib.Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    return data.get("apps", [])


def _select_apps(apps: list[dict[str, Any]], spec: str, platform: str) -> list[str]:
    pool = [a for a in apps if a.get("flutter")]
    if platform == "android":
        pool = [a for a in pool if (a.get("deliverable") or {}).get("android")]
    elif platform == "ios":
        pool = [a for a in pool if (a.get("deliverable") or {}).get("ios")]

    spec = (spec or "all").strip()
    if spec in ("", "all"):
        return sorted([a["repo"] for a in pool], key=str.lower)
    if spec == "android-deliverable":
        return sorted(
            [a["repo"] for a in pool if (a.get("deliverable") or {}).get("android")],
            key=str.lower,
        )
    if spec == "ios-deliverable":
        return sorted(
            [a["repo"] for a in pool if (a.get("deliverable") or {}).get("ios")],
            key=str.lower,
        )
    if spec == "ads":
        return sorted([a["repo"] for a in pool if a.get("ads")], key=str.lower)

    wanted = {x.strip() for x in spec.split(",") if x.strip()}
    return sorted([a["repo"] for a in pool if a["repo"] in wanted], key=str.lower)


def _load_costs(path: pathlib.Path | None) -> dict[str, float]:
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text())
    if isinstance(data, dict):
        return {str(k): float(v) for k, v in data.items()}
    return {}


def _shard(apps: list[str], shard_count: int, costs: dict[str, float]) -> dict[str, Any]:
    if shard_count < 1:
        shard_count = 1
    if not apps:
        return {"include": [{"shard": 1, "apps": "", "weight": 0.0, "count": 0}]}

    bins: list[dict[str, Any]] = [{"apps": [], "weight": 0.0} for _ in range(shard_count)]
    weighted = sorted(apps, key=lambda a: costs.get(a, 1.0), reverse=True)
    for app in weighted:
        i = min(range(shard_count), key=lambda idx: bins[idx]["weight"])
        w = costs.get(app, 1.0)
        bins[i]["apps"].append(app)
        bins[i]["weight"] += w

    include = []
    shard = 0
    for b in bins:
        if not b["apps"]:
            continue
        shard += 1
        include.append(
            {
                "shard": shard,
                "apps": ",".join(sorted(b["apps"], key=str.lower)),
                "weight": round(b["weight"], 2),
                "count": len(b["apps"]),
            }
        )
    return {"include": include}


def _shard_count(selected: list[str], pool: list[str], max_shards: int,
                 costs: dict[str, float]) -> int:
    """Shards in proportion to the work, measured against the whole pool.

    `--shards` is what the full pool ("all") needs. A list naming most of the
    pool needs about as many; a list of three apps needs one. Explicit lists
    used to get a single shard whatever their size, and a dispatch naming 42
    apps ran them in one iOS and one Android job: Android hit its 180-minute
    timeout and the last 9 iOS apps failed in about a second each on a runner
    that had already built 33 (ship run 38536298465).
    """
    if max_shards < 1:
        return 1
    total = sum(costs.get(a, 1.0) for a in pool)
    if not selected or total <= 0:
        return 1
    per_shard = total / max_shards
    wanted = sum(costs.get(a, 1.0) for a in selected)
    return max(1, min(max_shards, math.ceil(round(wanted / per_shard, 6))))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="all")
    ap.add_argument("--platform", choices=["validate", "android", "ios"], required=True)
    ap.add_argument("--shards", type=int, required=True)
    ap.add_argument("--manifest", default="apps.json")
    ap.add_argument("--costs", default="")
    # Apps to leave out, e.g. the ones that failed validation in this run.
    ap.add_argument("--exclude", default="")
    args = ap.parse_args()

    apps = _load_apps(pathlib.Path(args.manifest))
    selected = _select_apps(apps, args.spec, args.platform)
    excluded = {x.strip() for x in args.exclude.split(",") if x.strip()}
    selected = [a for a in selected if a not in excluded]
    pool = _select_apps(apps, "all", args.platform)
    costs = _load_costs(pathlib.Path(args.costs) if args.costs else None)
    matrix = _shard(selected, _shard_count(selected, pool, args.shards, costs), costs)
    print(json.dumps(matrix))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
