#!/usr/bin/env python3
"""Build dynamic shard matrices for GitHub Actions jobs."""

from __future__ import annotations

import argparse
import json
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="all")
    ap.add_argument("--platform", choices=["validate", "android", "ios"], required=True)
    ap.add_argument("--shards", type=int, required=True)
    ap.add_argument("--manifest", default="apps.json")
    ap.add_argument("--costs", default="")
    args = ap.parse_args()

    apps = _load_apps(pathlib.Path(args.manifest))
    selected = _select_apps(apps, args.spec, args.platform)
    explicit = args.spec.strip() not in ("", "all", "android-deliverable", "ios-deliverable", "ads")
    costs = _load_costs(pathlib.Path(args.costs) if args.costs else None)
    matrix = _shard(selected, 1 if explicit else args.shards, costs)
    print(json.dumps(matrix))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
