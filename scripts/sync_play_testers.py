#!/usr/bin/env python3
"""Mirror the tester roster onto Google Play.

Reads `store/testers.json`, the same committed roster the App Store side and
docs/TESTERS.md use, and applies it to the internal, alpha and beta tracks.

Two things Play does differently, both re-measured on 2026-10-01:

  * A track's tester list takes **Google Groups only**. Every track of every
    app returns `{}` today, and the resource has no field for an address:

        PUT .../testers/internal  {"testers": ["someone@gmail.com"]}
        400 INVALID_ARGUMENT  Unknown name "testers" at 'testers': Cannot find field.

    Put the roster in one Google Group and set PLAY_TESTER_GOOGLE_GROUP; this
    then attaches it everywhere in one pass. Without it, the email list is a
    Play Console action and this script only reports. See MA-033.

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
TRACKS = ["internal", "alpha", "beta"]

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

# The roster is store/testers.json, committed, so this script, the App Store
# side and docs/TESTERS.md all read one list. It used to come from
# ~/agl/.dist/tester-roster.json, which is a run artifact: on a fresh checkout
# it does not exist and this exited before doing anything. The old file is
# still honoured as a fallback.
TESTERS = M / "store" / "testers.json"
if TESTERS.exists():
    emails = sorted({t["email"].lower() for t in json.load(open(TESTERS))["external"]})
    print(f"roster: {len(emails)} external tester(s) from store/testers.json")
else:
    roster = json.load(open(ROSTER)) if ROSTER.exists() else []
    emails = sorted({r["email"].lower() for r in roster})
    print(f"roster: {len(emails)} address(es) from App Store Connect")
if not emails: sys.exit("no roster; populate store/testers.json")

if DEV_ID:
    # Play refuses any other page size: "Pagination is not currently available.
    # The page_size parameter must be set to -1."
    u = call("GET", f"{API}/developers/{DEV_ID}/users?pageSize=-1")
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
    targets = sorted(r for r, a in apps.items()
                     if a.get("deliverable", {}).get("android", True) and a.get("store_eligible", True))
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
    # All three closed tracks, not just internal: a tester list set on
    # `internal` alone leaves alpha and beta empty, so promoting a build to
    # closed testing silently has no audience.
    have = {}
    for track in TRACKS:
        cur = call("GET", f"{API}/applications/{pkg}/edits/{eid}/testers/{track}")
        have[track] = cur.get("googleGroups") or []

    if AUDIT or not GROUP:
        print(f"{repo:18} " + "  ".join(f"{t}={have[t] or 'none'}" for t in TRACKS))
        out[repo] = {"status": "audited", "googleGroups": have}
        continue

    todo = [t for t in TRACKS if GROUP not in have[t]]
    if not todo:
        print(f"{repo:18} already has {GROUP} on all {len(TRACKS)} track(s)")
        out[repo] = {"status": "already", "googleGroups": have}
        continue

    err = None
    for track in todo:
        u = call("PUT", f"{API}/applications/{pkg}/edits/{eid}/testers/{track}",
                 {"googleGroups": sorted(set(have[track] + [GROUP]))})
        if (m := fail(u)): err = f"{track}: {m}"; break
        have[track] = sorted(set(have[track] + [GROUP]))
    if err:
        print(f"{repo:18} set testers: {err}"); out[repo] = {"status": "failed", "error": err}; continue
    c = call("POST", f"{API}/applications/{pkg}/edits/{eid}:commit")
    if (m := fail(c)): print(f"{repo:18} commit: {m}"); out[repo] = {"status": "failed", "error": m}; continue
    print(f"{repo:18} {GROUP} now on {', '.join(todo)}")
    out[repo] = {"status": "synced", "googleGroups": have}

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
