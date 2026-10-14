#!/usr/bin/env python3
"""Turn the validate shards' per-app verdicts into the build matrices.

One app's failing test used to skip every build: ship run 38534910952 lost all
43 builds to a single Uscis-Case test, because the build jobs needed the whole
validate matrix to succeed. Each validate shard now uploads the verdicts that
`fastlane validate` writes (AGL_BATCH_RESULTS), and this drops only the apps
that failed from the Android and iOS matrices.

An app counts as failed unless a shard positively recorded it as passed - a
shard that died before writing its file (setup failure, timeout, cancelled)
fails all of its apps rather than letting them through untested.

Writes to $GITHUB_OUTPUT: failed (csv), apps (spec for release/internal),
android_matrix, ios_matrix; and a table to $GITHUB_STEP_SUMMARY.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import resolve_matrix  # noqa: E402


def collect(validate_matrix: str, results_dir: pathlib.Path) -> tuple[list[str], list[str], dict[str, str]]:
    validated: list[str] = []
    for shard in json.loads(validate_matrix).get("include", []):
        validated += [a for a in (shard.get("apps") or "").split(",") if a]
    passed: set[str] = set()
    reasons: dict[str, str] = {}
    for f in sorted(results_dir.glob("**/*.json")) if results_dir.exists() else []:
        try:
            data = json.loads(f.read_text())
        except (OSError, ValueError) as e:
            print(f"::warning::unreadable validate result {f}: {e}")
            continue
        passed.update(data.get("passed") or [])
        reasons.update(data.get("failed") or {})
    failed = {a: reasons.get(a, "no verdict recorded (the validate shard did not finish)")
              for a in validated if a not in passed}
    ok = [a for a in validated if a in passed]
    return validated, ok, failed


def matrix(spec: str, platform: str, shards: int, exclude: list[str], manifest: str, costs: str) -> str:
    apps = resolve_matrix._load_apps(pathlib.Path(manifest))
    selected = [a for a in resolve_matrix._select_apps(apps, spec, platform) if a not in set(exclude)]
    pool = resolve_matrix._select_apps(apps, "all", platform)
    c = resolve_matrix._load_costs(pathlib.Path(costs) if costs else None)
    return json.dumps(resolve_matrix._shard(selected, resolve_matrix._shard_count(selected, pool, shards, c), c))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--validate-matrix", required=True)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--android-shards", type=int, default=6)
    ap.add_argument("--ios-shards", type=int, default=4)
    ap.add_argument("--manifest", default="apps.json")
    ap.add_argument("--costs", default="")
    args = ap.parse_args()

    validated, ok, failed = collect(args.validate_matrix, pathlib.Path(args.results_dir))
    bad = sorted(failed, key=str.lower)
    # Downstream jobs read an empty list as "every app", so when nothing
    # passed the spec is empty and the release job's `if:` skips it.
    spec_out = args.spec if not bad else ",".join(ok)
    out = {
        "failed": ",".join(bad),
        "apps": spec_out,
        "android_matrix": matrix(args.spec, "android", args.android_shards, bad, args.manifest, args.costs),
        "ios_matrix": matrix(args.spec, "ios", args.ios_shards, bad, args.manifest, args.costs),
    }

    lines = ["### Validation gate", "",
             f"{len(ok)}/{len(validated)} apps passed analyze and test."]
    if bad:
        lines += ["", "**Failed validation - not built, not released:**", "",
                  "| app | reason |", "| --- | --- |"]
        lines += [f"| {a} | {failed[a].replace('|', '/')} |" for a in bad]
        print(f"::error::validation failed for {len(bad)} app(s), which are not built or released: {', '.join(bad)}")
    for k in ("android_matrix", "ios_matrix"):
        inc = json.loads(out[k])["include"]
        lines.append(f"\n{k}: {len([s for s in inc if s['apps']])} shard(s), "
                     f"{sum(s['count'] for s in inc)} app(s)")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            for k, v in out.items():
                fh.write(f"{k}={v}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
