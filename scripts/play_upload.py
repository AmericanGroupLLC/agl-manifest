#!/usr/bin/env python3
"""Upload every signed bundle to Google Play's internal testing track.

Uses american-group-publisher@american-group-llc.iam.gserviceaccount.com, which
already holds Play access (verified 2026-09-17: it can open an edit on both a
Production app and a Draft one). No long-lived key is created — gcloud mints a
short-lived token by impersonation, so nothing durable lands on disk.

    python3 scripts/play_upload.py CalcMaster
    python3 scripts/play_upload.py --all
    python3 scripts/play_upload.py --all --status completed   # CI: reach testers

Per app: open an edit, upload the .aab, point the internal track at it, commit.

The release status defaults to **draft** — nothing reaches a tester until a
human promotes it — because that is the right default for a manual run. Pass
`--status completed` to have Play publish the internal-track release straight
away, which is what the CI pipeline uses.

Two things this script does **not** do, both measured rather than assumed:

* It does not give anyone access. The internal track only distributes to a
  Google Group (`testers.update` accepts no other field), and the decision on
  this account is to use no groups. Delivery to the people already on the Play
  Console account is `scripts/play_internal_share.py` instead.
* It does not clear `NOT_PUBLISHED` for internal app sharing. Verified
  2026-09-22 on AGCleaner: a `completed` internal release at version code 2
  coexists with sharing still returning `NOT_PUBLISHED`, because that gate is
  the app's Draft state in Console, not the track's.
"""
import json, pathlib, subprocess, sys, time

ROOT = pathlib.Path("/Users/spatchava/agl"); M = ROOT / "agl-manifest"
DIST = ROOT / ".dist"; LOGS = DIST / "play-logs"; LOGS.mkdir(parents=True, exist_ok=True)
RESULTS = DIST / "play-results.json"
SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
UPLOAD = "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications"

_tok = {"v": "", "at": 0.0}
def token():
    if time.time() - _tok["at"] > 1500:      # a 43-app run outlives one token
        _tok["v"] = subprocess.run(
            [GCLOUD, "auth", "print-access-token", f"--impersonate-service-account={SA}",
             "--scopes=https://www.googleapis.com/auth/androidpublisher"],
            capture_output=True, text=True).stdout.strip()
        _tok["at"] = time.time()
    return _tok["v"]

def call(method, url, body=None, data_file=None, ctype="application/json"):
    cmd = ["curl", "-s", "--max-time", "1800", "-X", method, url,
           "-H", f"Authorization: Bearer {token()}", "-H", f"Content-Type: {ctype}"]
    if data_file: cmd += ["--data-binary", f"@{data_file}"]
    elif body is not None: cmd += ["-d", json.dumps(body)]
    else: cmd += ["-H", "Content-Length: 0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out)
    except Exception: return {"error": {"message": out[:300] or "empty response"}}

def fail(d): return d["error"].get("message", "unknown")[:200] if "error" in d else None

apps = json.load(open(M / "apps.json"))["apps"]
names = [a for a in sys.argv[1:] if not a.startswith("--")]
STATUS = "completed" if "--status" in sys.argv and \
    sys.argv[sys.argv.index("--status") + 1] == "completed" else "draft"
if STATUS == "completed":
    names = [n for n in names if n != "completed"]
# portfolio-board publishes AGL's own internal roadmap and is marked
# `_blocked` in its store JSON, so the manifest sets store_eligible false
# and the portfolio that reaches a store is 42 apps, not 43. Naming it
# explicitly still works; only the sweep skips it.
if names: apps = [a for a in apps if a["repo"] in names]
else: apps = [a for a in apps if a.get("store_eligible", True)]
results = json.load(open(RESULTS)) if RESULTS.exists() else {}

for a in apps:
    repo, pkg = a["repo"], a["application_id"]
    if results.get(repo, {}).get("status") == "uploaded":
        print(f"{repo:18} already uploaded"); continue
    aab = next(iter(sorted(DIST.glob(f"{repo}-*.aab"))), None)
    if not aab:
        print(f"{repo:18} no .aab staged"); results[repo] = {"status": "no-aab"}; continue
    t0 = time.time(); step = "open edit"
    try:
        e = call("POST", f"{API}/{pkg}/edits")
        if fail(e): raise RuntimeError(fail(e))
        eid = e["id"]

        step = "upload bundle"
        u = call("POST", f"{UPLOAD}/{pkg}/edits/{eid}/bundles?uploadType=media",
                 data_file=str(aab), ctype="application/octet-stream")
        if fail(u): raise RuntimeError(fail(u))
        vc = u["versionCode"]

        step = "assign track"
        t = call("PUT", f"{API}/{pkg}/edits/{eid}/tracks/internal",
                 {"track": "internal",
                  "releases": [{"versionCodes": [str(vc)], "status": STATUS}]})
        if fail(t): raise RuntimeError(fail(t))

        step = "commit"
        c = call("POST", f"{API}/{pkg}/edits/{eid}:commit")
        if fail(c): raise RuntimeError(fail(c))

        results[repo] = {"status": "uploaded", "package": pkg, "versionCode": vc,
                         "aab": aab.name, "seconds": round(time.time() - t0),
                         "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        print(f"{repo:18} uploaded  versionCode {vc}  ({results[repo]['seconds']}s)", flush=True)
    except Exception as ex:
        results[repo] = {"status": "failed", "package": pkg, "step": step,
                         "error": str(ex)[:220], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        print(f"{repo:18} FAILED at {step}: {str(ex)[:150]}", flush=True)
    json.dump(results, open(RESULTS, "w"), indent=1)

ok = sum(1 for v in results.values() if v["status"] == "uploaded")
print(f"\nuploaded {ok}/{len(results)} -> {RESULTS}")
