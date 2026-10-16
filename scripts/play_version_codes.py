#!/usr/bin/env python3
"""Ask Play what version code each app is already using.

    python3 scripts/play_version_codes.py          # -> ~/agl/.dist/play-version-codes.json

Play refuses a bundle whose version code it has seen before —
`Version code 2 has already been used.` — and the code is baked into the .aab
at build time from `pubspec.yaml`'s `version: x.y.z+N`. So a rebuild alone
cannot fix a collision; the build number has to be raised past whatever Play
already holds, which is what this reports.

Reads the *edits* API rather than a local record, because a local record only
knows about uploads this machine made. Anything uploaded from CI, from another
machine, or by hand in the console would be invisible and the collision would
come back.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import urllib.error
import urllib.request
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT, play_key  # noqa: E402

ROOT = _ROOT
M = _MANIFEST
KEY = play_key()  # honours $PLAY_SERVICE_ACCOUNT on a runner
BASE = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
OUT = ROOT / ".dist/play-version-codes.json"


def token() -> str:
    """This python has no google-auth; agl-manifest's bundle carries googleauth."""
    script = (
        'require "googleauth"; '
        f'c=Google::Auth::ServiceAccountCredentials.make_creds('
        f'json_key_io: File.open("{KEY}"), '
        'scope: "https://www.googleapis.com/auth/androidpublisher"); '
        'print c.fetch_access_token!["access_token"]'
    )
    r = subprocess.run(["bundle", "exec", "ruby", "-e", script], cwd=str(M),
                       capture_output=True, text=True, timeout=300)
    if not r.stdout.strip():
        raise RuntimeError(f"no Play token: {r.stderr[-300:]}")
    return r.stdout.strip()


def call(method: str, url: str, tok: str):
    req = urllib.request.Request(
        url, method=method, headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read() or b"{}"
            return r.status, json.loads(body)
    except urllib.error.HTTPError as e:
        raw = (e.read() or b"").decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:200]}


def read_codes(pkg: str, tok: str, attempts: int = 3) -> dict:
    """Every version code Play has used for `pkg`, from a throwaway edit.

    A failed read is never "no codes". Ship run 38812509219 ran this on six
    Android shards at once; in the shard that built AGRecorder (and in the one
    that built MyCard and Photriya) the bundles read for that app failed, the
    status was ignored, the empty answer became highest=0, nothing was bumped,
    and Play refused all three: "Version code 4 has already been used" (every
    other shard saw 7-8). So check each status, retry with a fresh edit, and
    report ERROR rather than a code that is not true."""
    import time
    detail = ""
    for attempt in range(1, attempts + 1):
        status, edit = call("POST", f"{BASE}/{pkg}/edits", tok)
        if status == 404:
            return {"state": "NO_LISTING", "detail": (edit.get("error") or {}).get("message", "")[:90]}
        if status == 200:
            eid = edit["id"]
            # bundles.list is every .aab Play has accepted, including ones no
            # track points at; apks.list adds codes used by APK uploads.
            bs, bundles = call("GET", f"{BASE}/{pkg}/edits/{eid}/bundles", tok)
            as_, apks = call("GET", f"{BASE}/{pkg}/edits/{eid}/apks", tok)
            call("DELETE", f"{BASE}/{pkg}/edits/{eid}", tok)
            if bs == 200 and as_ == 200:
                codes = [b.get("versionCode") for b in bundles.get("bundles", []) + apks.get("apks", [])
                         if isinstance(b.get("versionCode"), int)]
                highest = max(codes) if codes else 0
                return {"state": "OK", "highest": highest, "count": len(codes), "next": highest + 1}
            detail = f"bundles HTTP {bs}, apks HTTP {as_}: {str(bundles if bs != 200 else apks)[:90]}"
        else:
            detail = f"edit HTTP {status}: {(edit.get('error') or {}).get('message', str(edit))[:90]}"
        time.sleep(5 * attempt)
    return {"state": "ERROR", "detail": detail}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT),
                    help="where to write the result; CI keeps it in RUNNER_TEMP")
    ap.add_argument("--apps", default="all",
                    help="'all' or comma-separated repos. Each ship.yml Android shard asks only for "
                         "its own apps: six shards opening an edit on all 43 packages at once is "
                         "what made the reads fail (run 38812509219)")
    args = ap.parse_args()
    out = pathlib.Path(args.out)

    tok = token()
    apps = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps not in ("", "all"):
        wanted = {x.strip().lower() for x in args.apps.split(",") if x.strip()}
        apps = [a for a in apps if a["repo"].lower() in wanted]
    result = {}
    for a in apps:
        repo, pkg = a["repo"], a["application_id"]
        result[repo] = read_codes(pkg, tok)
        r = result[repo]
        print(f"{repo:18} " + (f"highest={r['highest']:<4} next={r['next']}" if r["state"] == "OK"
                               else f"{r['state']} {r.get('detail', '')}"))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    live = [v for v in result.values() if v["state"] == "OK"]
    print(f"\n{len(live)} app(s) with a Play listing -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
