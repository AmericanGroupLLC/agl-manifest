#!/usr/bin/env python3
"""Set the Play listing's support email, which Play requires before publishing.

`edits.details` carries contactEmail, contactWebsite and contactPhone. Nine apps
had no support email at all, which Play flags on the store listing page.

    python3 scripts/play_contact.py --all
    python3 scripts/play_contact.py AeroSwift
"""
import json, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
M = pathlib.Path(__file__).resolve().parents[1]
SA = "american-group-publisher@american-group-llc.iam.gserviceaccount.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
EMAIL = "contact@americangroup.ai"
SITE = "https://www.americangroup.ai"

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
    cmd = ["curl", "-s", "--max-time", "300", "-X", method, url,
           "-H", f"Authorization: Bearer {token()}", "-H", "Content-Type: application/json"]
    cmd += ["-d", json.dumps(body)] if body is not None else ["-H", "Content-Length: 0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out) if out.strip() else {}
    except Exception: return {"error": {"message": out[:200]}}

def fail(d): return d["error"].get("message", "unknown")[:160] if "error" in d else None

apps = json.load(open(M / "apps.json"))["apps"]
names = [a for a in sys.argv[1:] if not a.startswith("--")]
if names: apps = [a for a in apps if a["repo"] in names]
elif "--all" not in sys.argv: sys.exit("pass --all or one or more app names")

set_ = already = 0; failed = []
for a in apps:
    repo, pkg = a["repo"], a["application_id"]
    e = call("POST", f"{API}/{pkg}/edits")
    if fail(e): continue          # no Play entry for this app
    eid = e["id"]
    det = call("GET", f"{API}/{pkg}/edits/{eid}/details")
    if det.get("contactEmail"):
        already += 1
        continue
    body = {"defaultLanguage": det.get("defaultLanguage") or "en-US",
            "contactEmail": EMAIL, "contactWebsite": det.get("contactWebsite") or SITE}
    u = call("PUT", f"{API}/{pkg}/edits/{eid}/details", body)
    if (m := fail(u)): print(f"{repo:18} {m}"); failed.append(repo); continue
    c = call("POST", f"{API}/{pkg}/edits/{eid}:commit")
    if (m := fail(c)): print(f"{repo:18} commit: {m}"); failed.append(repo); continue
    print(f"{repo:18} support email set")
    set_ += 1

print(f"\nset: {set_}  already had one: {already}  failed: {len(failed)}")
