#!/usr/bin/env python3
"""Deliver every signed bundle to the existing Play Console users, no groups.

Play's internal *testing track* cannot be driven by email. Google's own
discovery document is explicit — the `Testers` schema has exactly one property:

    "Testers": {"googleGroups": {"items": {"type": "string"}, ...}}

so `testers.update` accepts Google Groups and nothing else. Adding the team by
address through that API is simply not possible.

**Internal app sharing** is the route that needs neither a group nor a tester
list, and it is what this script uses. Each upload returns a
`play.google.com/apps/test/...` link that any user already on the Play Console
account can open to install.

Measured limits, so nobody expects more than it gives: the app must already
exist on Play and have been published at least once. An app with no listing
returns `404 Package not found`, and one that Play still treats as a Draft app
returns `400 UploadException: NOT_PUBLISHED`. Those apps cannot be reached by
this route, nor by the internal track, until they are published once.

Do not read `NOT_PUBLISHED` as "no bundle uploaded yet" and try to fix it by
uploading one. Verified 2026-09-22: AGCleaner's internal track already carries a
`completed` release at version code 2 and sharing still returns
`NOT_PUBLISHED`. The gate is the app's own Draft/published state in Console —
the App content declarations plus a reviewed initial rollout — not the track.

Who can install is therefore exactly "the existing users inside the account" —
listed at the top of every run so the report says who, not just how many.

    python3 scripts/play_internal_share.py --dry-run
    python3 scripts/play_internal_share.py
    python3 scripts/play_internal_share.py CalcMaster
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path("/Users/spatchava/agl")
KEY = ROOT / ".secrets/play-publisher-agl.json"
DEV_ID = "5590631437738173959"
BASE = "https://androidpublisher.googleapis.com/androidpublisher/v3"
UPLOAD = ("https://androidpublisher.googleapis.com/upload/androidpublisher/v3"
          "/applications/internalappsharing/{pkg}/artifacts/bundle?uploadType=media")
OUT = ROOT / ".dist/play-internal-share.json"


def token() -> str:
    """python3 here has no google-auth; agl-manifest's bundle carries googleauth."""
    script = (
        'require "googleauth"; '
        f'c=Google::Auth::ServiceAccountCredentials.make_creds('
        f'json_key_io: File.open("{KEY}"), '
        'scope: "https://www.googleapis.com/auth/androidpublisher"); '
        'print c.fetch_access_token!["access_token"]'
    )
    r = subprocess.run(["bundle", "exec", "ruby", "-e", script],
                       cwd=str(ROOT / "agl-manifest"),
                       capture_output=True, text=True, timeout=300)
    if not r.stdout.strip():
        raise RuntimeError(f"could not mint Play token: {r.stderr[-300:]}")
    return r.stdout.strip()


def get(url: str, tok: str):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:240]}


def console_users(tok: str) -> list[str]:
    # pageSize=-1 is mandatory: the API rejects anything else with
    # "Pagination is not currently available."
    code, d = get(f"{BASE}/developers/{DEV_ID}/users?pageSize=-1", tok)
    if code != 200:
        print(f"could not list Play Console users: {json.dumps(d)[:160]}")
        return []
    return [u.get("email", "") for u in d.get("users", []) if u.get("email")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tok = token()
    users = console_users(tok)
    humans = [u for u in users if not u.endswith(".gserviceaccount.com")]
    print(f"Play Console account users who can install: {len(humans)}")
    for u in sorted(humans):
        print(f"   {u}")
    print()

    apps = [a for a in json.loads((ROOT / "agl-manifest/apps.json").read_text())["apps"]
            if a.get("flutter")]
    if args.apps:
        apps = [a for a in apps if a["repo"] in args.apps]

    out = []
    for a in apps:
        repo = a["repo"]
        pkg = a.get("application_id") or a["bundle_id"]
        hits = sorted((ROOT / ".dist").glob(f"{repo}-*.aab"))
        rec = {"repo": repo, "package": pkg}
        if not hits:
            rec["state"] = "NO_BUNDLE"
            out.append(rec)
            print(f"{repo:<18} NO_BUNDLE", flush=True)
            continue
        aab = hits[0]
        if args.dry_run:
            rec.update(state="WOULD_UPLOAD", bundle=aab.name,
                       mb=round(aab.stat().st_size / 1048576))
            out.append(rec)
            print(f"{repo:<18} would share {aab.name} ({rec['mb']} MB)", flush=True)
            continue

        # A 60 MB body over this connection drops often enough that one
        # unretried ConnectionResetError killed a whole 43-app run.
        payload = aab.read_bytes()
        last = ""
        for attempt in range(3):
            req = urllib.request.Request(
                UPLOAD.format(pkg=pkg), data=payload, method="POST",
                headers={"Authorization": f"Bearer {tok}",
                         "Content-Type": "application/octet-stream"})
            try:
                with urllib.request.urlopen(req, timeout=1800) as r:
                    d = json.loads(r.read())
                rec.update(state="SHARED", url=d.get("downloadUrl"),
                           sha256=d.get("sha256"),
                           cert=d.get("certificateFingerprint"))
                print(f"{repo:<18} {d.get('downloadUrl')}", flush=True)
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                msg = (json.loads(body).get("error", {}).get("message", body)
                       if body.startswith("{") else body)
                # 404/NOT_PUBLISHED are verdicts, not transport failures.
                rec.update(state="NO_LISTING" if e.code == 404 else
                           ("NOT_PUBLISHED" if "NOT_PUBLISHED" in body else "FAILED"),
                           detail=str(msg)[:160])
                print(f"{repo:<18} {rec['state']}", flush=True)
                break
            except Exception as e:  # noqa: BLE001 - transport, worth retrying
                last = f"{type(e).__name__}: {e}"
                if attempt == 2:
                    rec.update(state="TRANSPORT_FAILED", detail=last[:160])
                    print(f"{repo:<18} TRANSPORT_FAILED after 3 tries", flush=True)
                else:
                    time.sleep(10 * (attempt + 1))
        out.append(rec)

    OUT.write_text(json.dumps({"console_users": users, "artifacts": out}, indent=1))
    ok = sum(1 for r in out if r.get("state") == "SHARED")
    print(f"\nshared {ok}/{len(out)}  ->  {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
