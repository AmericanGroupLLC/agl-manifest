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

ROOT = pathlib.Path("/Users/spatchava/agl")
M = ROOT / "agl-manifest"
KEY = ROOT / ".secrets/play-publisher-agl.json"
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT),
                    help="where to write the result; CI keeps it in RUNNER_TEMP")
    args = ap.parse_args()
    out = pathlib.Path(args.out)

    tok = token()
    apps = json.loads((M / "apps.json").read_text())["apps"]
    result = {}
    for a in apps:
        repo, pkg = a["repo"], a["application_id"]
        status, edit = call("POST", f"{BASE}/{pkg}/edits", tok)
        if status != 200:
            msg = (edit.get("error") or {}).get("message", str(edit))[:90]
            result[repo] = {"state": "NO_LISTING" if status == 404 else "ERROR",
                         "detail": msg}
            print(f"{repo:18} {result[repo]['state']}")
            continue
        eid = edit["id"]
        # bundles.list is the authoritative set of version codes Play has ever
        # accepted for this package, including ones no track points at.
        _, bundles = call("GET", f"{BASE}/{pkg}/edits/{eid}/bundles", tok)
        codes = [b.get("versionCode") for b in bundles.get("bundles", [])
                 if isinstance(b.get("versionCode"), int)]
        call("DELETE", f"{BASE}/{pkg}/edits/{eid}", tok)
        highest = max(codes) if codes else 0
        result[repo] = {"state": "OK", "highest": highest, "count": len(codes),
                     "next": highest + 1}
        print(f"{repo:18} highest={highest:<4} next={highest + 1}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    live = [v for v in result.values() if v["state"] == "OK"]
    print(f"\n{len(live)} app(s) with a Play listing -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
