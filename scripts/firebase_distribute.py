#!/usr/bin/env python3
"""Distribute every app to testers through Firebase App Distribution.

    python3 scripts/firebase_distribute.py --dry-run
    python3 scripts/firebase_distribute.py                 # Android, all apps
    python3 scripts/firebase_distribute.py --ios           # iOS as well
    python3 scripts/firebase_distribute.py CalcMaster

Why this talks to the REST API rather than the Firebase CLI:

The CLI is installed (15.32.1) but its credentials have expired, and
`firebase login --reauth` opens a browser — no use from here. The REST API
takes the gcloud token this machine already has. Two details make it work,
and neither is guessable from the error messages:

  * **`x-goog-user-project`.** Without it every call is refused with
    "Your application is authenticating by using local Application Default
    Credentials. The firebaseappdistribution.googleapis.com API requires a
    quota project".
  * **The project *number*, not the id.** `projects/americangroupllc-5bdfc`
    answers 400 INVALID_ARGUMENT; `projects/9057515422` is correct. The
    number is in google-services.json, and also inside every app id.

A 404 from `/testers` or `/releases` on a fresh project means the collection
is empty, not that the project is wrong — which is misleading, and cost a
detour before the first upload proved the path.

iOS is opt-in and comes with a caveat worth knowing before relying on it:
App Distribution installs an iOS build only on devices named in an **ad-hoc**
provisioning profile. The IPAs in .dist are App Store distribution builds, so
they upload cleanly and still will not install for a tester. TestFlight is
the right channel for those; this flag exists for when ad-hoc IPAs are built.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402

API = "https://firebaseappdistribution.googleapis.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def token() -> str:
    r = subprocess.run([GCLOUD, "auth", "print-access-token", f"--scopes={SCOPE}"],
                       capture_output=True, text=True, timeout=180)
    t = (r.stdout or "").strip()
    if not t:
        raise SystemExit(f"no gcloud token: {r.stderr[-300:]}")
    return t


def call(tok, method, url, body=None, raw=None, project=None, extra=None):
    headers = {"Authorization": f"Bearer {tok}"}
    if project:
        headers["x-goog-user-project"] = project
    headers.update(extra or {})
    data = None
    if raw is not None:
        data = raw
        headers["Content-Type"] = "application/octet-stream"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def usable(f: pathlib.Path) -> bool:
    """A readable zip with entries in it.

    Eight of the APKs in .dist are the right size and completely empty as
    archives — CalcMaster's is 43 MB and `unzip -l` lists nothing. Firebase
    rejects them with the unhelpful "Ensure you are uploading a valid IPA or
    APK", so they are filtered here and the app's .aab is used instead.
    """
    import zipfile
    try:
        with zipfile.ZipFile(f) as z:
            return bool(z.namelist())
    except Exception:
        return False


def firebase_ids(app_dir: pathlib.Path):
    """(project_id, project_number, android_app_id, ios_app_id)."""
    gs = app_dir / "android/app/google-services.json"
    if not gs.exists():
        return None
    j = json.loads(gs.read_text())
    pi = j["project_info"]
    android = next((c["client_info"]["mobilesdk_app_id"] for c in j["client"]), None)

    ios = None
    for name in ("ios/Runner/GoogleService-Info.plist",):
        p = app_dir / name
        if not p.exists():
            continue
        import plistlib
        try:
            ios = plistlib.loads(p.read_bytes()).get("GOOGLE_APP_ID")
        except Exception:
            ios = None
    return pi["project_id"], pi["project_number"], android, ios


def upload(tok, project_id, number, app_id, artifact: pathlib.Path):
    url = (f"{API}/upload/v1/projects/{number}/apps/{app_id}/releases:upload")
    code, out = call(tok, "POST", url, raw=artifact.read_bytes(), project=project_id,
                     extra={"X-Goog-Upload-File-Name": artifact.name,
                            "X-Goog-Upload-Protocol": "raw"})
    if code >= 300 or "name" not in out:
        return None, (out.get("error") or {}).get("message", str(code))[:200]

    op = out["name"]
    # The upload returns an operation, not a release. Poll it: a release that
    # is still processing cannot be distributed.
    for _ in range(40):
        time.sleep(8)
        c2, st = call(tok, "GET", f"{API}/v1/{op}", project=project_id)
        if st.get("done"):
            resp = st.get("response") or {}
            rel = (resp.get("release") or {}).get("name")
            if rel:
                return rel, resp.get("result", "")
            return None, json.dumps(st.get("error") or st)[:200]
    return None, "operation did not finish"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ios", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    roster = json.loads((M / "store/testers.json").read_text())
    emails = [t["email"] for t in roster["external"]] + \
             [t["email"] for t in roster["account_holders"]]

    manifest = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]

    tok = token()
    report, ok, failed = {}, 0, 0

    for a in manifest:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        ids = firebase_ids(d)
        if not ids:
            report[repo] = {"status": "no google-services.json"}
            print(f"  {repo:18} no google-services.json", flush=True)
            continue
        project_id, number, android_id, ios_id = ids

        targets = []
        # APK first, AAB second. Only 26 of 43 have an APK on disk but all
        # 43 have a bundle, and App Distribution accepts either — though an
        # .aab needs the Firebase project linked to Play, so it can fail
        # where the .apk would not.
        # Globbed, not a fixed name: a flavoured build lands as
        # CalcMaster-app-prod-release.apk, not CalcMaster-app-release.apk,
        # and matching the fixed name silently found nothing for those apps.
        # Newest first, not alphabetical. GroceryMatch has both
        # -app-prod-release.apk and -app-release.apk; sorting by name picked
        # the older of the two, whose applicationId predates a rename, and
        # Firebase rejected it for a package mismatch that no longer existed.
        newest = lambda g: sorted(DIST.glob(g), key=lambda f: f.stat().st_mtime,
                                  reverse=True)
        apks = newest(f"{repo}-app*release.apk")
        aabs = newest(f"{repo}-app*release.aab")
        art = next((f for f in apks + aabs if usable(f)), None)
        if android_id and art:
            targets.append(("android", android_id, art))
        elif android_id:
            report.setdefault(repo, {})["android"] = "no APK or AAB in .dist"
        if args.ios and ios_id:
            ipa = DIST / f"{repo}.ipa"
            if ipa.exists():
                targets.append(("ios", ios_id, ipa))

        if args.dry_run:
            print(f"  {repo:18} " + ", ".join(
                f"{p}:{f.name} ({f.stat().st_size // 1048576} MB)" for p, _, f in targets)
                or f"  {repo:18} nothing to send", flush=True)
            continue

        for platform, app_id, artifact in targets:
            rel, detail = upload(tok, project_id, number, app_id, artifact)
            if not rel:
                report.setdefault(repo, {})[platform] = f"upload failed: {detail}"
                print(f"  {repo:18} {platform} FAILED {detail[:90]}", flush=True)
                failed += 1
                continue
            c, out = call(tok, "POST", f"{API}/v1/{rel}:distribute",
                          body={"testerEmails": emails}, project=project_id)
            note = "" if c < 300 else \
                f" (distribute {c}: {(out.get('error') or {}).get('message','')[:70]})"
            report.setdefault(repo, {})[platform] = {
                "release": rel.rsplit("/", 1)[-1], "result": detail,
                "testers": len(emails) if c < 300 else 0}
            print(f"  {repo:18} {platform} {detail} -> {len(emails)} tester(s){note}",
                  flush=True)
            ok += 1

    out_f = DIST / "firebase-distribute.json"
    out_f.write_text(json.dumps(report, indent=1) + "\n")
    print(f"\nreleases distributed {ok}, failed {failed}")
    print(f"-> {out_f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
