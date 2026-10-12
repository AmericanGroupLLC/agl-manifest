#!/usr/bin/env python3
"""Every build-time credential the apps read, per app, and whether a release build gets it.

    python3 scripts/api_vendor_audit.py          # -> docs/api-vendor-keys.json

Scans each app's lib/ for `String.fromEnvironment('<KEY>')` whose name looks
like a credential or partner id (API keys, client ids/secrets, affiliate
markers and tags). AdMob unit ids and Supabase are excluded — those are
handled by admob_defines() and committed config.

`passed_by_release_build` is measured against what the delivery path really
passes: build_release.py and build_ipa.py add only admob_defines(), and
ship.yml holds no third-party secret. So a key with no default is empty in
every shipped build, and the feature behind it is off.

Read-only and local: no network, no secrets read. The signup list that
explains each vendor is docs/API_VENDORS_AND_AFFILIATES.md.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

OUT = M / "docs/api-vendor-keys.json"
DEFINE = re.compile(r"(?:String|bool|int)\.fromEnvironment\(\s*'([A-Z0-9_]+)'\s*"
                    r"(?:,\s*defaultValue:\s*(?:'([^']*)'|([^\)]+)))?", re.S)
CREDENTIAL = re.compile(r"KEY|TOKEN|SECRET|CLIENT_ID|APP_ID|AFFILIATE|_TAG|PARTNER|PUBLISHER|"
                        r"TRACKING|CAMPAIGN|_SID|DSN|USERNAME|PASSWORD|_ID$|ACCOUNT|MERCHANT|"
                        r"REFERRAL|AFF_|MARKER")
NOT_VENDOR = re.compile(r"^(ADMOB_|SUPABASE_|FLAVOR$|APP_ENV$|BACKEND|SCREENSHOT$|ENV$|"
                        r"API_BASE_URL$|API_URL$|USE_|ENABLE_|DEBUG|IAP_)")


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())["apps"]
    passed = set()  # nothing beyond ADMOB_* reaches a release build today
    report = {}
    for a in apps:
        lib = ROOT / a["repo"] / (a.get("dir") or ".") / "lib"
        keys: dict[str, dict] = {}
        for f in sorted(lib.rglob("*.dart")):
            text = f.read_text(errors="ignore")
            for m in DEFINE.finditer(text):
                k = m.group(1)
                if NOT_VENDOR.search(k) or not CREDENTIAL.search(k):
                    continue
                default = m.group(2) if m.group(2) is not None else (m.group(3) or "").strip()
                rec = keys.setdefault(k, {"default": None, "sites": []})
                if default and default not in ("''", '""'):
                    rec["default"] = default
                line = text[:m.start()].count("\n") + 1
                rec["sites"].append(f"{f.relative_to(ROOT / a['repo'])}:{line}")
        for k, rec in keys.items():
            rec["passed_by_release_build"] = k in passed
            rec["effective_in_release"] = ("default" if rec["default"] else "EMPTY")
        report[a["repo"]] = keys
    OUT.write_text(json.dumps({"apps": report}, indent=1) + "\n")
    distinct = {k for v in report.values() for k in v}
    empty = {k for v in report.values() for k, r in v.items() if not r["default"]}
    print(f"  {len(distinct)} credential keys across {sum(1 for v in report.values() if v)} apps; "
          f"{len(empty)} are empty in every release build")
    print(f"  -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
