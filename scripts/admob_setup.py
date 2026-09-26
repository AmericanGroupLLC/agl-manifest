#!/usr/bin/env python3
"""Create an AdMob app for every app on both platforms, plus its ad units.

43 apps x 2 platforms = 86 AdMob apps. The **v1beta** API can do this; v1
cannot — it exposes only list/get/report. v1beta adds `accounts.apps.create`
and `accounts.adUnits.create`, which is what this uses.

Auth is the catch. AdMob has no service-account path: it authorises as the
AdMob account owner, so the credential has to come from an interactive consent,
once:

    gcloud auth application-default login \\
      --scopes=https://www.googleapis.com/auth/admob.monetization,https://www.googleapis.com/auth/admob.readonly

Then:

    python3 scripts/admob_setup.py --dry-run     # show every app and unit it would create
    python3 scripts/admob_setup.py               # create them
    python3 scripts/admob_setup.py --apps CalcMaster,iMaps

Idempotent: an AdMob app whose display name and platform already exist is
reused, and an ad unit with the same display name is left alone. Results go to
~/agl/.dist/admob-results.json, and the ids are written into
docs/admob-ids.json, which is what the build reads.
"""
import argparse, json, pathlib, subprocess, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
M = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / ".dist"; DIST.mkdir(exist_ok=True)
API = "https://admob.googleapis.com/v1beta"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")

# One banner and one interstitial per app per platform: that is what agl_ads
# consumes. Rewarded is deliberately absent — no app shows a rewarded ad.
AD_FORMATS = [("Banner", "BANNER"), ("Interstitial", "INTERSTITIAL")]

_tok = {"v": "", "at": 0.0}
def token():
    if time.time() - _tok["at"] > 1500:
        r = subprocess.run([GCLOUD, "auth", "application-default", "print-access-token"],
                           capture_output=True, text=True)
        if not r.stdout.strip():
            sys.exit(
                "No application-default credentials with the AdMob scope.\n\n"
                "  gcloud auth application-default login \\\n"
                "    --scopes=https://www.googleapis.com/auth/admob.monetization,"
                "https://www.googleapis.com/auth/admob.readonly\n\n"
                "AdMob authorises as the account owner; there is no service-account path.")
        _tok["v"] = r.stdout.strip(); _tok["at"] = time.time()
    return _tok["v"]

def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: return json.loads(raw)
        except Exception: return {"error": {"message": raw[:300], "code": e.code}}

def fail(d): return d["error"].get("message", "unknown")[:200] if "error" in d else None

def paged(url, key):
    out, tokn = [], None
    while True:
        u = url + (f"?pageToken={tokn}" if tokn else "")
        d = call("GET", u)
        if fail(d): return out, fail(d)
        out += d.get(key, [])
        tokn = d.get("nextPageToken")
        if not tokn: return out, None

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--apps", default="")
args = ap.parse_args()

accounts, err = paged(f"{API}/accounts", "account")
if err: sys.exit(f"could not list AdMob accounts: {err}")
if not accounts: sys.exit("the credential sees no AdMob account")
publisher = accounts[0]["name"]          # accounts/pub-XXXXXXXXXXXXXXXX
print(f"AdMob account: {publisher}")

existing_apps, err = paged(f"{API}/{publisher}/apps", "apps")
if err: sys.exit(f"could not list AdMob apps: {err}")
by_key = {}
for a in existing_apps:
    nm = (a.get("linkedAppInfo") or a.get("manualAppInfo") or {}).get("displayName")
    by_key[(nm, a.get("platform"))] = a
print(f"AdMob already holds {len(existing_apps)} app(s)")

existing_units, _ = paged(f"{API}/{publisher}/adUnits", "adUnits")
units_by_app = {}
for u in existing_units:
    units_by_app.setdefault(u.get("appId"), set()).add(u.get("displayName"))

apps = json.load(open(M / "apps.json"))["apps"]
if args.apps:
    want = {s.strip() for s in args.apps.split(",")}
    apps = [a for a in apps if a["repo"] in want]

out = {}
created_apps = created_units = 0
for a in apps:
    repo = a["repo"]
    sp = M / "store/apps" / f"{repo}.json"
    display = repo
    if sp.exists():
        display = (json.load(open(sp)).get("copy", {}).get("en", {}) or {}).get("name") or repo
    rec = out.setdefault(repo, {})
    for platform, store_id in (("ANDROID", a["application_id"]), ("IOS", a["bundle_id"])):
        key = (display, platform)
        app = by_key.get(key)
        if app is None:
            if args.dry_run:
                print(f"{repo:18} {platform:8} WOULD CREATE {display!r}")
                rec[platform] = {"status": "would-create"}
                continue
            # linkedAppInfo binds the AdMob app to the store listing. It is only
            # accepted once the listing is public; until then AdMob takes the
            # name alone and the link can be made later in the console.
            body = {"platform": platform, "manualAppInfo": {"displayName": display}}
            d = call("POST", f"{API}/{publisher}/apps", body)
            if (m := fail(d)):
                print(f"{repo:18} {platform:8} create failed: {m}")
                rec[platform] = {"status": "failed", "error": m}
                continue
            app = d; by_key[key] = app; created_apps += 1
            print(f"{repo:18} {platform:8} created {app.get('appId')}")
        rec[platform] = {"appId": app.get("appId"), "name": app.get("name")}

        have = units_by_app.get(app.get("appId"), set())
        for label, fmt in AD_FORMATS:
            dn = f"{display} {label}"
            if dn in have:
                continue
            if args.dry_run:
                print(f"{repo:18} {platform:8} WOULD CREATE unit {dn!r} ({fmt})")
                continue
            u = call("POST", f"{API}/{publisher}/adUnits",
                     {"appId": app.get("appId"), "displayName": dn, "adFormat": fmt,
                      "adTypes": ["RICH_MEDIA", "VIDEO"]})
            if (m := fail(u)):
                print(f"{repo:18} {platform:8} unit {label} failed: {m}")
                rec.setdefault("unit_errors", []).append(f"{platform} {label}: {m}")
                continue
            created_units += 1
            rec.setdefault("units", {})[f"{platform}_{label.upper()}"] = u.get("adUnitId")
            print(f"{repo:18} {platform:8} unit {label} -> {u.get('adUnitId')}")

json.dump(out, open(DIST / "admob-results.json", "w"), indent=1)
print(f"\napps created: {created_apps}   ad units created: {created_units}")
print(f"-> {DIST / 'admob-results.json'}")
if not args.dry_run:
    (M / "docs/admob-ids.json").write_text(json.dumps(out, indent=1) + "\n")
    print("-> docs/admob-ids.json")
