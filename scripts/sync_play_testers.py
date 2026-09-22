#!/usr/bin/env python3
"""Mirror the App Store Connect tester roster onto Google Play.

Reads the roster `distribute.rb` writes (`~/agl/.dist/tester-roster.json`, which
is App Store Connect's Users and Access plus anyone already a beta tester) and
applies it to Play.

Two things Play does differently, both measured on 2026-09-22:

  * The internal track's tester list takes **Google Groups only**.
    `GET /edits/{id}/testers/internal` returns `{}` for every app and the
    resource accepts a `googleGroups` array, not individual addresses. Put the
    roster in one Google Group and set PLAY_TESTER_GOOGLE_GROUP; this then
    attaches that group to every app's internal track in one pass. Without it,
    the email list is a Play Console action and this script only reports.

  * Play Console account users live under `developers/{id}/users`, which needs
    the numeric developer id from the Play Console URL. Set PLAY_DEVELOPER_ID
    to have this report who is on the account and who from the roster is not.

    PLAY_TESTER_GOOGLE_GROUP=agl-testers@example.com python3 scripts/sync_play_testers.py
    PLAY_DEVELOPER_ID=1234567890123456789 python3 scripts/sync_play_testers.py --audit
"""
import json, os, pathlib, subprocess, sys, time

ROOT = pathlib.Path(os.environ.get("AGL_ROOT", pathlib.Path(__file__).resolve().parents[2]))
M = pathlib.Path(__file__).resolve().parents[1]
ROOT.joinpath(".dist").mkdir(parents=True, exist_ok=True)
ROSTER = ROOT / ".dist" / "tester-roster.json"
RESULTS = ROOT / ".dist" / "play-testers-results.json"
SA = os.environ.get("PLAY_SERVICE_ACCOUNT",
                    "american-group-publisher@american-group-llc.iam.gserviceaccount.com")
GCLOUD = os.environ.get("GCLOUD", str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud"))
API = "https://androidpublisher.googleapis.com/androidpublisher/v3"
GROUP = os.environ.get("PLAY_TESTER_GOOGLE_GROUP", "").strip()
DEV_ID = os.environ.get("PLAY_DEVELOPER_ID", "").strip()
AUDIT = "--audit" in sys.argv

_tok = {"v": "", "at": 0.0}
def token():
    if time.time() - _tok["at"] > 1500:
        # In CI gcloud is already signed in as the service account, so ask it
        # for a token directly. On a developer machine, impersonate instead so
        # no long-lived key ever lands on disk.
        cmd = [GCLOUD, "auth", "print-access-token",
               "--scopes=https://www.googleapis.com/auth/androidpublisher"]
        if os.environ.get("PLAY_IMPERSONATE", "yes").lower() not in ("no", "0", "false"):
            cmd.insert(3, f"--impersonate-service-account={SA}")
        _tok["v"] = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
        _tok["at"] = time.time()
    return _tok["v"]

def call(method, url, body=None):
    cmd = ["curl", "-s", "--max-time", "300", "-X", method, url,
           "-H", f"Authorization: Bearer {token()}", "-H", "Content-Type: application/json"]
    cmd += ["-d", json.dumps(body)] if body is not None else ["-H", "Content-Length: 0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out) if out.strip() else {}
    except Exception: return {"error": {"message": out[:200] or "empty response"}}

def fail(d): return d["error"].get("message", "unknown")[:180] if "error" in d else None

roster = json.load(open(ROSTER)) if ROSTER.exists() else []
emails = sorted({r["email"].lower() for r in roster})
print(f"roster: {len(emails)} address(es) from App Store Connect")
if not emails: sys.exit("no roster; run distribute.rb --sync first")

if DEV_ID:
    u = call("GET", f"{API}/developers/{DEV_ID}/users")
    if (m := fail(u)):
        print(f"Play Console users: {m}")
    else:
        have = {x.get("email", "").lower() for x in u.get("users", [])}
        print(f"Play Console account users: {len(have)}")
        missing = [e for e in emails if e not in have]
        print(f"  on the roster but not on the Play account ({len(missing)}): {', '.join(missing) or 'none'}")
else:
    print("PLAY_DEVELOPER_ID not set — skipping the Play Console user comparison")

apps = {a["repo"]: a for a in json.load(open(M / "apps.json"))["apps"]}
relfile = ROOT / ".dist" / "play-release-results.json"
if relfile.exists():
    live = json.load(open(relfile))
    targets = [r for r, v in sorted(live.items()) if v.get("status") == "live-internal"]
else:
    # No local delivery record (a fresh CI checkout): try every Android app and
    # let Play tell us which ones have no entry.
    targets = sorted(r for r, a in apps.items() if a.get("deliverable", {}).get("android", True))
    print(f"no local release record; trying all {len(targets)} Android app(s)")
out = {}
for repo in targets:
    pkg = apps[repo]["application_id"]
    e = call("POST", f"{API}/applications/{pkg}/edits")
    if (m := fail(e)):
        if "not found" in m.lower():
            out[repo] = {"status": "no-play-entry"}
        else:
            print(f"{repo:18} open edit: {m}"); out[repo] = {"status": "failed", "error": m}
        continue
    eid = e["id"]
    cur = call("GET", f"{API}/applications/{pkg}/edits/{eid}/testers/internal")
    groups = cur.get("googleGroups") or []
    if AUDIT or not GROUP:
        print(f"{repo:18} internal testers: googleGroups={groups or 'none'}")
        out[repo] = {"status": "audited", "googleGroups": groups}
        continue
    if GROUP in groups:
        print(f"{repo:18} already has {GROUP}")
        out[repo] = {"status": "already", "googleGroups": groups}
        continue
    u = call("PUT", f"{API}/applications/{pkg}/edits/{eid}/testers/internal",
             {"googleGroups": sorted(set(groups + [GROUP]))})
    if (m := fail(u)): print(f"{repo:18} set testers: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    c = call("POST", f"{API}/applications/{pkg}/edits/{eid}:commit")
    if (m := fail(c)): print(f"{repo:18} commit: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    print(f"{repo:18} internal testers now include {GROUP}")
    out[repo] = {"status": "synced", "googleGroups": sorted(set(groups + [GROUP]))}

json.dump(out, open(RESULTS, "w"), indent=1)
done = sum(1 for v in out.values() if v.get("status") in ("synced", "already"))
reachable = sum(1 for v in out.values() if v.get("status") != "no-play-entry")
missing = sum(1 for v in out.values() if v.get("status") == "no-play-entry")
print(f"\n{done}/{reachable} app(s) with a Play entry carry the tester group"
      + (f"; {missing} app(s) have no Play entry" if missing else "")
      + f"  -> {RESULTS}")
if not GROUP:
    print("\nSet PLAY_TESTER_GOOGLE_GROUP to a Google Group holding the roster and re-run "
          "to attach it everywhere; Play's API takes no individual addresses.")
