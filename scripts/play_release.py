#!/usr/bin/env python3
"""Promote each app's internal-testing draft release so testers can install it.

play_upload.py leaves the internal track as a draft release. A draft is invisible
to testers, so this flips every uploaded app's internal release to "completed"
and reports the track's tester lists. Internal testing reaches only the emails on
that app's internal tester list, never the public.

    python3 scripts/play_release.py --all
    python3 scripts/play_release.py AGCleaner
    python3 scripts/play_release.py --all --production   # promote internal -> production

Production promotion is refused while an app is still a Draft in Play Console:
"Only releases with status draft may be created on draft app." Verified
2026-09-22 against all 21 uploaded apps. Google requires the first production
release of a draft app to be made in the console, with the App content
declarations (content rating, data safety, target audience, ads, app access)
completed first. None of those have an API. Once an app is published, this
promotes every later release.
"""
import json, pathlib, subprocess, sys, time

ROOT = pathlib.Path("/Users/spatchava/agl"); M = ROOT / "agl-manifest"
RESULTS = ROOT / ".dist" / "play-results.json"
OUT = ROOT / ".dist" / "play-release-results.json"
PROD_OUT = ROOT / ".dist" / "play-production-results.json"
SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"

_tok = {"v": "", "at": 0.0}
def token():
    if time.time() - _tok["at"] > 1500:
        _tok["v"] = subprocess.run(
            [GCLOUD, "auth", "print-access-token", f"--impersonate-service-account={SA}",
             "--scopes=https://www.googleapis.com/auth/androidpublisher"],
            capture_output=True, text=True).stdout.strip()
        _tok["at"] = time.time()
    return _tok["v"]

def call(method, url, body=None):
    cmd = ["curl", "-s", "--max-time", "600", "-X", method, url,
           "-H", f"Authorization: Bearer {token()}", "-H", "Content-Type: application/json"]
    cmd += ["-d", json.dumps(body)] if body is not None else ["-H", "Content-Length: 0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out) if out.strip() else {}
    except Exception: return {"error": {"message": out[:300] or "empty response"}}

def fail(d): return d["error"].get("message", "unknown")[:200] if "error" in d else None

apps = json.load(open(M / "apps.json"))["apps"]
PRODUCTION = "--production" in sys.argv
names = [a for a in sys.argv[1:] if not a.startswith("--")]
if names: apps = [a for a in apps if a["repo"] in names]
else: apps = [a for a in apps if json.load(open(RESULTS)).get(a["repo"], {}).get("status") == "uploaded"]

out = {} if PRODUCTION else (json.load(open(OUT)) if OUT.exists() else {})
for a in apps:
    repo, pkg = a["repo"], a["application_id"]
    e = call("POST", f"{API}/{pkg}/edits")
    if (m := fail(e)): print(f"{repo:18} open edit: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    eid = e["id"]
    t = call("GET", f"{API}/{pkg}/edits/{eid}/tracks/internal")
    if (m := fail(t)): print(f"{repo:18} read track: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    rel = t.get("releases") or []
    if not rel: print(f"{repo:18} internal track has no release"); out[repo] = {"status": "no-release"}; continue

    if PRODUCTION:
        vc = rel[0].get("versionCodes", [])
        u = call("PUT", f"{API}/{pkg}/edits/{eid}/tracks/production",
                 {"track": "production", "releases": [{"versionCodes": vc, "status": "completed"}]})
        if (m := fail(u)):
            print(f"{repo:18} set production: {m}"); out[repo] = {"status": "failed", "error": m}; continue
        c = call("POST", f"{API}/{pkg}/edits/{eid}:commit")
        if (m := fail(c)):
            why = "app-is-still-a-draft-in-play-console" if "draft app" in m else m
            print(f"{repo:18} blocked — {why}")
            out[repo] = {"status": "blocked", "blocker": why, "versionCodes": vc}
        else:
            print(f"{repo:18} PRODUCTION release live (versionCode {','.join(vc)})")
            out[repo] = {"status": "live-production", "versionCodes": vc}
        json.dump(out, open(PROD_OUT, "w"), indent=1)
        continue
    for r in rel:
        r["status"] = "completed"
        r.pop("userFraction", None)
    u = call("PUT", f"{API}/{pkg}/edits/{eid}/tracks/internal", {"track": "internal", "releases": rel})
    if (m := fail(u)): print(f"{repo:18} set completed: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    c = call("POST", f"{API}/{pkg}/edits/{eid}:commit")
    if (m := fail(c)): print(f"{repo:18} commit: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    vc = ",".join(rel[0].get("versionCodes", []))
    out[repo] = {"status": "live-internal", "package": pkg, "versionCodes": vc,
                 "at": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
    print(f"{repo:18} internal release LIVE (versionCode {vc})")
    json.dump(out, open(PROD_OUT if PRODUCTION else OUT, "w"), indent=1)

json.dump(out, open(PROD_OUT if PRODUCTION else OUT, "w"), indent=1)
if PRODUCTION:
    n = sum(1 for v in out.values() if v.get("status") == "live-production")
    print(f"\nlive on production: {n}/{len(out)}  -> {PROD_OUT}")
else:
    n = sum(1 for v in out.values() if v.get("status") == "live-internal")
    print(f"\nlive on internal testing: {n}/{len(out)}  -> {OUT}")
