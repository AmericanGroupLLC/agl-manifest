#!/usr/bin/env python3
"""Predelivery check 1.8: no notification cancel that can freeze iOS 27.

    python3 scripts/notify_cancel_check.py              # every app in apps.json
    python3 scripts/notify_cancel_check.py Verba MyHealth

flutter_local_notifications' `cancel(id)` calls
`removePendingNotificationRequests(withIdentifiers:)` on the main thread. On
iOS 27.0 that call waits for SpringBoard's notification server; on the
simulator the server came up 7.5 h after a boot, and until then the app was
frozen — Verba never left its launch screen, FashionFactory froze on the
first "Save order" (2026-10-14; packages/agl_notify/README.md). Apps cancel
through `AglNotify` (packages/agl_notify), which lists pending/delivered first
and only cancels ids that are there.

Rule: in every lib/ file that imports flutter_local_notifications, a
`.cancel` / `.cancelAll` / `.cancelAllPendingNotifications` on a
FlutterLocalNotificationsPlugin variable must sit on the line that wires it
into AglNotify (`cancelId:` / `cancelEverything:`). Anything else FAILs.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

PASS, FAIL, NA = "PASS", "FAIL", "n/a"
DECL = [re.compile(r"FlutterLocalNotificationsPlugin\??\s+(\w+)"),
        re.compile(r"(\w+)\s*=\s*FlutterLocalNotificationsPlugin\(")]


def scan(lib: pathlib.Path) -> tuple[str, str]:
    """(status, detail) for one app's lib/ directory."""
    offenders, wired, files = [], 0, 0
    for f in sorted(lib.rglob("*.dart")) if lib.is_dir() else []:
        src = f.read_text(errors="ignore")
        if "package:flutter_local_notifications/" not in src:
            continue
        files += 1
        names = {m.group(1) for rx in DECL for m in rx.finditer(src)} - {"get", "Function"}
        calls = [re.compile(rf"\b{re.escape(n)}\s*\.\s*(cancel|cancelAll|cancelAllPendingNotifications)\b")
                 for n in names]
        for i, line in enumerate(src.splitlines(), 1):
            if line.strip().startswith("//") or not any(c.search(line) for c in calls):
                continue
            if "cancelId:" in line or "cancelEverything:" in line:
                wired += 1
            else:
                offenders.append(f"{f.relative_to(lib.parent)}:{i}")
    if not files:
        return NA, "does not use flutter_local_notifications"
    if offenders:
        return FAIL, (f"{len(offenders)} direct plugin cancel(s) — freezes the main thread on iOS 27; "
                      f"cancel through AglNotify (packages/agl_notify): " + ", ".join(offenders[:6]))
    return PASS, (f"{wired} plugin cancel(s), all wired through AglNotify" if wired
                  else "flutter_local_notifications used, no cancel call")


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())
    apps = apps if isinstance(apps, list) else apps.get("apps", [])
    want = set(sys.argv[1:])
    bad = 0
    for a in apps:
        repo = a.get("repo") or a.get("name")
        if want and repo not in want:
            continue
        st, detail = scan(ROOT / repo / (a.get("dir") or ".") / "lib")
        bad += st == FAIL
        if st != NA or want:
            print(f"{st:4}  {repo}: {detail}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
