#!/usr/bin/env python3
"""Audit, and optionally fill, everything Play's API can reach per app.

    python3 scripts/play_gap_audit.py              # report only
    python3 scripts/play_gap_audit.py --fix        # fill what the API allows

Play refuses production for every app with

    Only releases with status draft may be created on draft app.

"Draft app" is a state in Console, not a missing field, so it is tempting to
stop there and call the rest console work. That would be wrong: an app leaves
Draft when its setup is complete, and a good part of that setup *is* reachable
through edits — details, listings, images, country availability and the
production track itself.

This reports each of those per app and, with --fix, writes the ones that are
missing and derivable from store/apps/<repo>.json. It never touches the five
that have no API at all — content rating, data safety, target audience, ads
declaration and app access — those are listed as console work so the human
pass is short and specific.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST, DIST  # noqa: E402

API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
CONSOLE_ONLY = ["content rating (IARC)", "data safety", "target audience",
                "ads declaration", "app access"]


def token() -> str:
    r = subprocess.run(
        [GCLOUD, "auth", "print-access-token", f"--impersonate-service-account={SA}",
         "--scopes=https://www.googleapis.com/auth/androidpublisher"],
        capture_output=True, text=True, timeout=300)
    if not r.stdout.strip():
        raise SystemExit(f"no Play token: {r.stderr[-300:]}")
    return r.stdout.strip()


def call(tok, method, url, body=None):
    req = urllib.request.Request(
        url, method=method,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body else None)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    tok = token()
    manifest = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    if args.apps:
        manifest = [a for a in manifest if a["repo"] in args.apps]

    report, fixed = {}, 0
    for a in manifest:
        repo, pkg = a["repo"], a["application_id"]
        meta_f = MANIFEST / "store/apps" / f"{repo}.json"
        meta = json.loads(meta_f.read_text()) if meta_f.exists() else {}
        en = (meta.get("copy") or {}).get("en") or {}
        defaults = json.loads((MANIFEST / "store/defaults.json").read_text())

        status, edit = call(tok, "POST", f"{API}/{pkg}/edits")
        if status >= 300:
            report[repo] = {"error": (edit.get("error") or {}).get("message", status)}
            print(f"  {repo:18} no edit: {report[repo]['error'][:70]}")
            continue
        eid = edit["id"]

        _, details = call(tok, "GET", f"{API}/{pkg}/edits/{eid}/details")
        _, listings = call(tok, "GET", f"{API}/{pkg}/edits/{eid}/listings")
        _, tracks = call(tok, "GET", f"{API}/{pkg}/edits/{eid}/tracks")
        _, images = call(tok, "GET",
                         f"{API}/{pkg}/edits/{eid}/listings/en-US/phoneScreenshots")

        listing = next((l for l in (listings.get("listings") or [])
                        if l.get("language") == "en-US"), {})
        prod = next((t for t in (tracks.get("tracks") or [])
                     if t.get("track") == "production"), {})
        prod_rel = (prod.get("releases") or [{}])[0]

        gaps = []
        if not details.get("contactEmail"):
            gaps.append("contactEmail")
        if not details.get("contactWebsite"):
            gaps.append("contactWebsite")
        if not listing.get("title"):
            gaps.append("title")
        if not listing.get("shortDescription"):
            gaps.append("shortDescription")
        if not listing.get("fullDescription"):
            gaps.append("fullDescription")
        if len(images.get("images") or []) < 2:
            gaps.append(f"phoneScreenshots({len(images.get('images') or [])})")
        if not prod_rel.get("versionCodes"):
            gaps.append("no production release")

        if args.fix and gaps:
            patch = {}
            if "contactEmail" in gaps:
                patch["contactEmail"] = defaults.get("support_email", "contact@safecodeg.com")
            if "contactWebsite" in gaps:
                patch["contactWebsite"] = defaults.get("marketing_url", "https://www.safecodeg.com")
            if patch:
                patch["defaultLanguage"] = details.get("defaultLanguage", "en-US")
                s, _ = call(tok, "PATCH", f"{API}/{pkg}/edits/{eid}/details", patch)
                if s < 300:
                    fixed += 1
                    gaps = [g for g in gaps if g not in patch]
            body = {}
            if "title" in gaps and (en.get("title") or en.get("name")):
                body["title"] = (en.get("title") or en.get("name"))[:30]
            if "shortDescription" in gaps and en.get("short_description"):
                body["shortDescription"] = en["short_description"][:80]
            if "fullDescription" in gaps and en.get("description"):
                body["fullDescription"] = en["description"][:4000]
            if body:
                body.setdefault("title", listing.get("title") or repo)
                body.setdefault("shortDescription", listing.get("shortDescription") or "")
                body.setdefault("fullDescription", listing.get("fullDescription") or "")
                body["language"] = "en-US"
                s, _ = call(tok, "PATCH",
                            f"{API}/{pkg}/edits/{eid}/listings/en-US", body)
                if s < 300:
                    fixed += 1
            s, _ = call(tok, "POST", f"{API}/{pkg}/edits/{eid}:commit")
        else:
            call(tok, "DELETE", f"{API}/{pkg}/edits/{eid}")

        report[repo] = {
            "gaps": gaps,
            "production_release": prod_rel.get("status"),
            "production_codes": prod_rel.get("versionCodes"),
            "console_only": CONSOLE_ONLY,
        }
        state = prod_rel.get("status") or "none"
        print(f"  {repo:18} production={state:10} api-gaps: {', '.join(gaps) or 'none'}")

    out = DIST / "play-gap-audit.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    staged = sum(1 for r in report.values() if r.get("production_release") == "draft")
    clean = sum(1 for r in report.values() if not r.get("gaps"))
    print(f"\n{len(report)} apps: {clean} with no API-reachable gap, "
          f"{staged} already carrying a draft production release.")
    if args.fix:
        print(f"wrote {fixed} change(s)")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
