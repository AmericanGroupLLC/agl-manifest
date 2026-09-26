#!/usr/bin/env python3
"""Regenerate docs/app-identifiers.json.

    python3 scripts/app_identifiers.py

The document claimed to be "generated from the repositories themselves - every
bundle id below is what the app actually builds today" while being hand-kept
and out of date: it listed six apps under the retired `com.americangroup.*`
scheme, a `com.americangroup.ratiotune` that has never existed anywhere, and
"Flutter apps: 36" plus five apps "not yet Flutter" long after all 43 were.

It used to also render a docs/APP_IDENTIFIERS.md table. Every column of
that table is now carried per app in `status.csv` — the single sheet — so the
second rendering was only another thing to drift out of date.

Bundle ids come from `apps.json`, which is itself
generated from an audit of the repositories; AdMob ids and the value actually
set in `Info.plist` come from `docs/release-readiness.json`, which is measured
per repo. Nothing here is typed by hand, so it cannot drift again.
"""

from __future__ import annotations

import json
import pathlib

M = pathlib.Path(__file__).resolve().parent.parent
TEST_ADMOB = "3940256099942544"


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())["apps"]
    rows = json.loads((M / "docs/release-readiness.json").read_text())
    rows = rows if isinstance(rows, list) else rows.get("apps", list(rows.values()))
    ready = {r["repo"]: r for r in rows}

    records = []
    for a in sorted(apps, key=lambda x: x["repo"].lower()):
        r = ready.get(a["repo"], {})
        gad = r.get("ios_admob_id") or ""
        records.append({
            "repo": a["repo"],
            "ios_bundle": a["bundle_id"],
            "android_id": a["application_id"],
            "admob_ios": r.get("ios_admob_id") or "",
            "admob_android": r.get("android_admob_id") or "",
            "gad_in_plist": gad,
            "flutter": bool(a.get("flutter", True)),
        })

    flutter = [x for x in records if x["flutter"]]
    with_android = [x for x in flutter
                    if x["admob_android"] and TEST_ADMOB not in x["admob_android"]]
    with_ios = [x for x in flutter
                if x["admob_ios"] and TEST_ADMOB not in x["admob_ios"]]
    mismatched = [x for x in records if x["ios_bundle"] != x["android_id"]]

    (M / "docs/app-identifiers.json").write_text(
        json.dumps(records, indent=1) + "\n")
    print(f"{len(records)} apps -> docs/app-identifiers.json "
          f"(identifiers also carried per app in status.csv)")
    print(f"  flutter {len(flutter)}, real AdMob android {len(with_android)}, "
          f"ios {len(with_ios)}, platform mismatches {len(mismatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
