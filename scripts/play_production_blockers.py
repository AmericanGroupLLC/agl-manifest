#!/usr/bin/env python3
"""Ask Google Play, per app, what stands between it and a live production release.

Two kinds of blocker exist and only one of them is visible to the API:

* **Track state** — is there a production release, and is it `draft` (staged,
  invisible) or `completed` (live)? The API answers this.
* **App content declarations** — content rating, advertising ID, photo/video
  permissions, data safety, target audience. Google exposes *no* API for these;
  they are Play Console forms. Their absence is what makes a never-published app
  a "Draft app", and a Draft app refuses a completed production release with
  "Only releases with status draft may be created on draft app".

So this script reports the half it can measure and records the API's own refusal
as evidence for the half it cannot.

    python3 scripts/play_production_blockers.py          # every app
    python3 scripts/play_production_blockers.py AGCleaner
"""
import json, pathlib, subprocess, sys, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402

API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
OUT = MANIFEST / "docs" / "play-production-blockers.json"


SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")


def token():
    """Impersonate the publisher service account.

    The key file is read through gcloud rather than googleauth: the system
    `bundle` on this machine is Ruby 2.6 and cannot load the gem.
    """
    r = subprocess.run(
        [GCLOUD, "auth", "print-access-token", f"--impersonate-service-account={SA}",
         "--scopes=https://www.googleapis.com/auth/androidpublisher"],
        capture_output=True, text=True, timeout=300)
    if not r.stdout.strip():
        raise RuntimeError(r.stderr[-300:])
    return r.stdout.strip()


def call(method, url, tok, body=None, attempts=4):
    """One Android Publisher call, retrying the ones that mean "later".

    A full 43-app sweep opens 43 edits in a row and Google starts answering 503
    "The service is currently unavailable" partway through. Reported raw, that
    reads as an app having lost its production release, which is how AeroSwift
    and AGCleaner briefly appeared to. Back off and ask again instead.
    """
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status, json.loads(r.read() or "{}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            if e.code in (429, 500, 503) and attempt < attempts - 1:
                time.sleep(3 * (attempt + 1))
                continue
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, {"raw": raw[:300]}


def main():
    tok = token()
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    apps = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    if names:
        apps = [a for a in apps if a["repo"] in names]

    rows = []
    for a in apps:
        pkg = a.get("application_id") or a.get("bundle_id")
        rec = {"repo": a["repo"], "package": pkg}
        code, edit = call("POST", f"{API}/{pkg}/edits", tok)
        if code != 200:
            rec["state"] = "NO_LISTING" if code == 404 else f"HTTP_{code}"
            rec["blocker"] = str(edit.get("error", {}).get("message", edit))[:160]
            rows.append(rec)
            print(f"{rec['repo']:18} {rec['state']:22} {rec['blocker']}")
            continue
        eid = edit["id"]
        for track in ("internal", "production"):
            c, t = call("GET", f"{API}/{pkg}/edits/{eid}/tracks/{track}", tok)
            rels = t.get("releases", []) if c == 200 else []
            rec[track] = [
                {"versionCodes": r.get("versionCodes", []),
                 "status": r.get("status"),
                 "countryTargeting": bool(r.get("countryTargeting"))}
                for r in rels
            ]
        call("DELETE", f"{API}/{pkg}/edits/{eid}", tok)

        prod = rec.get("production") or []
        if any(r["status"] == "completed" for r in prod):
            rec["state"] = "LIVE_PRODUCTION"
            rec["blocker"] = None
        elif any(r["status"] == "draft" for r in prod):
            rec["state"] = "PRODUCTION_DRAFT_STAGED"
            rec["blocker"] = "console-only: App content declarations + press Publish"
        elif rec.get("internal"):
            rec["state"] = "INTERNAL_ONLY"
            rec["blocker"] = "no production release staged"
        else:
            rec["state"] = "LISTING_EMPTY"
            rec["blocker"] = "no bundle uploaded"
        rows.append(rec)
        print(f"{rec['repo']:18} {rec['state']:24} {rec['blocker'] or 'none'}")

    OUT.parent.mkdir(exist_ok=True)
    # A filtered run measures a few apps and must not replace the sheet for all
    # 43. `python3 scripts/play_production_blockers.py AGrammarly` once cut the
    # file down to a single row, which then read as "the portfolio is one app".
    # Merge on repo instead, keeping the rows this run did not look at.
    if names and OUT.exists():
        kept = {r["repo"]: r for r in json.loads(OUT.read_text()).get("apps", [])}
        kept.update({r["repo"]: r for r in rows})
        rows_out = sorted(kept.values(), key=lambda r: r["repo"].lower())
    else:
        rows_out = rows
    OUT.write_text(json.dumps({"apps": rows_out}, indent=1) + "\n")
    tally = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    print("\n" + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
