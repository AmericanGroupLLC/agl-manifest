#!/usr/bin/env python3
"""Register every app in the Firebase project and write its real config files.

Crashlytics is wired into all 43 apps but reports nothing, because no app has
google-services.json / GoogleService-Info.plist (docs/MANUAL_ACTIONS.md MA-006).
Those files are not secret — Google documents them as shipping inside the
binary — and the Firebase Management API can both create the app records and
return the configs, so this does not need a console.

    python3 scripts/firebase_register.py --dry-run
    python3 scripts/firebase_register.py --all --commit

Two things the API does that the console does not, both handled here:

*   `androidApps/{id}/config` returns the **project-wide** google-services.json
    listing every client registered so far, and it grows with each new app. An
    app must ship only its own client, so the JSON is filtered to the matching
    package before it is written — which is what a console download gives you.
*   App creation is usually a long-running operation, but sometimes the
    resource comes back directly. Both shapes are accepted.

Registration for every app happens before any config is downloaded, so no app
gets a file that is missing a sibling registered a moment later.
"""
import base64, json, pathlib, subprocess, sys, time

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402
# A Firebase project holds 30 apps, and each app here needs two slots (android +
# ios), so 15 repos fill a project. 43 repos need three — and agl4 was added on
# 2026-10-04 because all three were exactly full (47 android + 43 ios = 90 of 90)
# and GroceryMatch needed one more Android client after its package was recased
# to match the Play record.
PROJECTS = ["americangroupllc-5bdfc", "americangroupllc-agl2", "americangroupllc-agl3",
            "americangroupllc-agl4"]
PROJECT = PROJECTS[0]   # quota project for every call; only it needs to be billable
ACCOUNT = "rainbow472.sri@gmail.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
BASE = "https://firebase.googleapis.com/v1beta1"
DRY = "--dry-run" in sys.argv; COMMIT = "--commit" in sys.argv
apps = json.load(open(M / "apps.json"))["apps"]
names = [a for a in sys.argv[1:] if not a.startswith("--")]
sel = apps if "--all" in sys.argv else [a for a in apps if a["repo"] in names]

_tok = {"v": "", "at": 0.0}
def token():
    # A 43-app run outlasts an access token, and the failure looks like
    # "Request had invalid authentication credentials" halfway through.
    if time.time() - _tok["at"] > 1500:
        _tok["v"] = subprocess.run([GCLOUD, "auth", "print-access-token", f"--account={ACCOUNT}"],
                                   capture_output=True, text=True).stdout.strip()
        _tok["at"] = time.time()
    return _tok["v"]

def api(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {token()}", "-H", f"x-goog-user-project: {PROJECT}",
           "-H", "Content-Type: application/json"]
    cmd += ["-d", json.dumps(body)] if body is not None else ["-H", "Content-Length: 0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try: return json.loads(out)
    except Exception: return {"error": {"message": out[:300]}}

def listing(kind, key, proj):
    got, tok = {}, None
    while True:
        u = f"{BASE}/projects/{proj}/{kind}?pageSize=100" + (f"&pageToken={tok}" if tok else "")
        d = api("GET", u)
        if "error" in d: raise SystemExit(f"list {kind} in {proj}: {d['error'].get('message')}")
        for a in d.get("apps", []): got[a[key]] = (proj, a["appId"])
        tok = d.get("nextPageToken")
        if not tok: return got

def create(kind, body, proj):
    # Firebase caps "Provision requests per minute"; a 43-app run trips it
    # immediately, so back off and retry rather than losing the app.
    for attempt in range(8):
        r = api("POST", f"{BASE}/projects/{proj}/{kind}", body)
        msg = r.get("error", {}).get("message", "")
        if "Quota exceeded" not in msg and "RESOURCE_EXHAUSTED" not in msg: break
        time.sleep(min(20 * (attempt + 1), 90))
    if "error" in r: raise RuntimeError(r["error"].get("message", "create failed")[:200])
    if r.get("appId"): return (proj, r["appId"])             # returned directly
    if not r.get("name"): raise RuntimeError(f"unexpected create response: {json.dumps(r)[:200]}")
    for _ in range(60):                                      # long-running operation
        if r.get("done"):
            if "error" in r: raise RuntimeError(str(r["error"])[:200])
            return (proj, r["response"]["appId"])
        time.sleep(3); r = api("GET", f"{BASE}/{r['name']}")
    raise RuntimeError("operation did not finish")

def config(kind, where):
    proj, app_id = where
    d = api("GET", f"{BASE}/projects/{proj}/{kind}/{app_id}/config")
    if "error" in d: raise RuntimeError(d["error"].get("message", "")[:200])
    return d["configFilename"], base64.b64decode(d["configFileContents"])

def only_this_package(blob, pkg):
    """Keep just this app's client, as a console download would."""
    d = json.loads(blob)
    mine = [c for c in d.get("client", [])
            if c["client_info"]["android_client_info"]["package_name"] == pkg]
    if not mine: raise RuntimeError(f"no client for {pkg} in the project config")
    d["client"] = mine
    return json.dumps(d, indent=2).encode() + b"\n"

# ---- --debug-variant: a `<package>.debug` client for debug builds ----
# Several apps give their debug buildType applicationIdSuffix ".debug", and the
# Google Services plugin fails the build when google-services.json has no
# client for the package being built ("No matching client found for package
# name '...debug'"), so a debug build never reaches an emulator. This registers
# the debug package in the *same* project as the app — one google-services.json
# describes one project — and writes the file with both clients, so release
# builds read exactly what they read before. Android only, and never commits.
#
#     python3 scripts/firebase_register.py --debug-variant --dry-run TripNest
#     python3 scripts/firebase_register.py --debug-variant TripNest Photriya
#
# When the app's own project is full (30 apps), the debug client can live in
# another project instead: --debug-project=<id> registers it there and writes
# android/app/src/debug/google-services.json holding only the debug client.
# The Google Services plugin reads src/<buildType>/ before android/app/, so
# debug builds use that file and release builds keep the app's own one.
#
#     python3 scripts/firebase_register.py --debug-variant \
#         --debug-project=americangroupllc-agl4 daily-pulse GadgetNest
if "--debug-variant" in sys.argv:
    SUFFIX = ".debug"
    other = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--debug-project=")), None)
    found = {}
    for proj in PROJECTS + ([other] if other and other not in PROJECTS else []):
        found.update(listing("androidApps", "packageName", proj))
    for a in sel:
        repo, pkg = a["repo"], a["application_id"]
        dbg = pkg + SUFFIX
        if pkg not in found:
            print(f"{repo:18} SKIP    {pkg} is not registered in any project")
            continue
        proj = other or found[pkg][0]
        if dbg not in found:
            if DRY:
                print(f"{repo:18} would register {dbg} in {proj}")
                continue
            try:
                found[dbg] = create("androidApps",
                                    {"packageName": dbg, "displayName": f"{repo} (debug)"}, proj)
                print(f"{repo:18} CREATED {dbg} in {proj}", flush=True)
                time.sleep(7)   # stay under the provisioning rate limit
            except Exception as e:
                # A full project says "Too many Apps"; a debug client cannot go
                # anywhere else, since the file it lands in names one project.
                print(f"{repo:18} FAILED  {dbg} in {proj}: {e}", flush=True)
                continue
        elif DRY:
            print(f"{repo:18} already registered {dbg} in {proj}")
            continue
        try:
            _, blob = config("androidApps", found[dbg])
            cfg = json.loads(blob)
            want = {dbg} if other else {pkg, dbg}
            cfg["client"] = [c for c in cfg.get("client", [])
                             if c["client_info"]["android_client_info"]["package_name"] in want]
            have = {c["client_info"]["android_client_info"]["package_name"] for c in cfg["client"]}
            if have != want:
                raise RuntimeError(f"project config has {sorted(have)}, wanted {sorted(want)}")
            d = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
            out = d / ("android/app/src/debug/google-services.json" if other
                       else "android/app/google-services.json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(json.dumps(cfg, indent=2).encode() + b"\n")
            print(f"{repo:18} WROTE   {out.relative_to(ROOT)} (clients: {', '.join(sorted(want))})",
                  flush=True)
        except Exception as e:
            print(f"{repo:18} FAILED  writing config: {e}", flush=True)
    raise SystemExit(0)

# ---- phase 1: register everything, so no config is written half-populated ----
android, ios = {}, {}
capacity = {}
for proj in PROJECTS:
    a = listing("androidApps", "packageName", proj); i = listing("iosApps", "bundleId", proj)
    android.update(a); ios.update(i)
    capacity[proj] = 30 - len(a) - len(i)
    print(f"  {proj}: {len(a)} android + {len(i)} ios, {capacity[proj]} slots free")

def room_for_pair():
    """A repo needs one android and one ios slot in the same project."""
    for proj in PROJECTS:
        if capacity[proj] >= 2: return proj
    raise SystemExit("every Firebase project is full — add another project")
print(f"registered before: {len(android)} android, {len(ios)} ios")
for a in sel:
    # Google reports a full project as "Too many Apps"; believe it over any
    # count we tracked, and move the app to the next project.
    need = [(k, key, v, s) for k, key, v, s in
            (("androidApps", "packageName", a["application_id"], android),
             ("iosApps", "bundleId", a["bundle_id"], ios)) if v not in s]
    if not need: continue
    if DRY:
        print(f"{a['repo']:18} would register {[v for _, _, v, _ in need]}"); continue
    # both halves of a repo must live in one project, or its two configs disagree
    proj = android.get(a["application_id"], (None,))[0] or ios.get(a["bundle_id"], (None,))[0] or room_for_pair()
    for kind, key, val, store in need:
        for _ in range(len(PROJECTS)):
            try:
                store[val] = create(kind, {key: val, "displayName": a["repo"]}, proj)
                capacity[proj] -= 1
                print(f"{a['repo']:18} {kind[:-4]:7} CREATED {val} in {proj}", flush=True)
                time.sleep(7)   # stay under the provisioning rate limit
                break
            except Exception as e:
                if "Too many Apps" in str(e):
                    capacity[proj] = 0
                    print(f"{a['repo']:18} {proj} is full — trying the next project", flush=True)
                    try: proj = room_for_pair()
                    except SystemExit as s: print(s); raise
                    continue
                print(f"{a['repo']:18} {kind[:-4]:7} FAILED  {val}  {e}")
                break
if DRY: raise SystemExit(0)
print(f"registered after: {len(android)} android, {len(ios)} ios\n")

# ---- phase 2: download, filter, write, commit ----
for a in sel:
    repo = a["repo"]; d = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
    pkg, bid = a["application_id"], a["bundle_id"]
    line = [f"{repo:18}"]
    try:
        fn, blob = config("androidApps", android[pkg])
        blob = only_this_package(blob, pkg)
        p = d / "android/app" / fn; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(blob)
        got = json.loads(blob)
        assert got["project_info"]["project_id"] in PROJECTS
        assert len(got["client"]) == 1
        line.append(f"{fn}({len(blob)}B, 1 client)")

        fn, blob = config("iosApps", ios[bid])
        p = d / "ios/Runner" / fn; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(blob)
        line.append(f"{fn}({len(blob)}B)")
        print(" ".join(line))

        if COMMIT:
            sub = a["dir"] if a["dir"] != "." else ""
            base = pathlib.Path(sub) if sub else pathlib.Path()
            paths = [str(base / "android/app/google-services.json"), str(base / "ios/Runner/GoogleService-Info.plist")]
            r = lambda *c: subprocess.run(c, cwd=ROOT / repo, capture_output=True, text=True)
            r("git", "add", "--", *paths)
            if r("git", "diff", "--cached", "--quiet").returncode:
                r("git", "commit", "-q", "-m",
                  "Add the Firebase configs so crash reporting actually reports\n\n"
                  f"Registered {pkg} and {bid} in {android[pkg][0]} and pulled the real\n"
                  "configs from the Firebase Management API. google-services.json is\n"
                  "filtered to this app's own client, as a console download would be.\n"
                  "The Gradle plugins apply themselves once the file exists, so no code\n"
                  "change is needed.")
                br = r("git", "branch", "--show-current").stdout.strip()
                dflt = r("git", "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD").stdout.strip().replace("origin/", "") or "main"
                p1 = r("git", "push", "-q", "origin", br); p2 = r("git", "push", "-q", "origin", f"HEAD:{dflt}")
                if p1.returncode or p2.returncode:
                    print(f"    push problem: {p1.stderr.strip()[-70:]} {p2.stderr.strip()[-70:]}")
    except Exception as e:
        print(" ".join(line) + f"  FAILED {type(e).__name__}: {str(e)[:180]}")
