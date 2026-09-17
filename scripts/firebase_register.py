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

ROOT = pathlib.Path("/Users/spatchava/agl"); M = ROOT / "agl-manifest"
# A Firebase project holds 30 apps, and each app here needs two slots (android +
# ios), so 15 repos fill a project. 43 repos need three.
PROJECTS = ["americangroupllc-5bdfc", "americangroupllc-agl2", "americangroupllc-agl3"]
PROJECT = PROJECTS[0]   # quota project for every call; only it needs to be billable
ACCOUNT = "rainbow472.sri@gmail.com"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
BASE = "https://firebase.googleapis.com/v1beta1"
DRY = "--dry-run" in sys.argv; COMMIT = "--commit" in sys.argv
apps = json.load(open(M / "apps.json"))["apps"]
names = [a for a in sys.argv[1:] if not a.startswith("--")]
sel = apps if "--all" in sys.argv else [a for a in apps if a["repo"] in names]

TOK = subprocess.run([GCLOUD, "auth", "print-access-token", f"--account={ACCOUNT}"],
                     capture_output=True, text=True).stdout.strip()

def api(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {TOK}", "-H", f"x-goog-user-project: {PROJECT}",
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
    need = [(k, key, v, s) for k, key, v, s in
            (("androidApps", "packageName", a["application_id"], android),
             ("iosApps", "bundleId", a["bundle_id"], ios)) if v not in s]
    if not need: continue
    if DRY:
        print(f"{a['repo']:18} would register {[v for _, _, v, _ in need]}"); continue
    # both halves of a repo must live in one project, or its two configs disagree
    proj = android.get(a["application_id"], (None,))[0] or ios.get(a["bundle_id"], (None,))[0] or room_for_pair()
    for kind, key, val, store in need:
        try:
            store[val] = create(kind, {key: val, "displayName": a["repo"]}, proj)
            capacity[proj] -= 1
            print(f"{a['repo']:18} {kind[:-4]:7} CREATED {val} in {proj}", flush=True)
            time.sleep(7)   # stay under the provisioning rate limit
        except Exception as e:
            print(f"{a['repo']:18} {kind[:-4]:7} FAILED  {val}  {e}")
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
