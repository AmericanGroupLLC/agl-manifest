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

Idempotent: an AdMob app is matched to an existing one by the package name or
bundle id AdMob records in linkedAppInfo, falling back to a punctuation- and
case-insensitive display-name match, and an ad unit with the same display name
is left alone. Results go to
~/agl/.dist/admob-results.json, and the ids are written into
docs/admob-ids.json, which is what the build reads.
"""
import argparse, json, pathlib, subprocess, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
M = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / ".dist"; DIST.mkdir(exist_ok=True)
API = "https://admob.googleapis.com/v1beta"
GCLOUD = str(pathlib.Path.home() / "google-cloud-sdk/bin/gcloud")
QUOTA_PROJECT = (subprocess.run([GCLOUD, "config", "get-value", "project"],
                                capture_output=True, text=True).stdout.strip()
                 or "americangroupllc-5bdfc")

# One banner and one interstitial per app per platform: that is what agl_ads
# consumes. Rewarded is deliberately absent — no app shows a rewarded ad.
AD_FORMATS = [("Banner", "BANNER"), ("Interstitial", "INTERSTITIAL")]


def _norm(name):
    """Compare display names the way a person would: case and punctuation
    drift between AdMob and the store copy, so "CalcMaster: World Calc" and
    "calcmaster world calc" are the same app."""
    return "".join(c for c in (name or "").lower() if c.isalnum())

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
    # ADC needs a quota project named on every AdMob call, or the API answers
    # "requires a quota project, which is not set by default".
    headers = {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}
    if QUOTA_PROJECT:
        headers["x-goog-user-project"] = QUOTA_PROJECT
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
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
ap.add_argument("--sync", action="store_true",
                help="create nothing; just pull the ids AdMob already holds "
                     "into docs/admob-ids.json")
args = ap.parse_args()
if args.sync:
    args.dry_run = True   # --sync must never create anything

accounts, err = paged(f"{API}/accounts", "account")
if err: sys.exit(f"could not list AdMob accounts: {err}")
if not accounts: sys.exit("the credential sees no AdMob account")
publisher = accounts[0]["name"]          # accounts/pub-XXXXXXXXXXXXXXXX
print(f"AdMob account: {publisher}")

existing_apps, err = paged(f"{API}/{publisher}/apps", "apps")
if err: sys.exit(f"could not list AdMob apps: {err}")
# Matching on the display name alone was not enough. AdMob's names drifted from
# the store copy this script derives them from — the account holds "CalcMaster"
# where store/apps says "CalcMaster: World Calc", and "Case Tracker for USCIS"
# where it says "USCIS Case Lookup" — so a run would have created a second
# AdMob app for all seven that already exist. linkedAppInfo.appStoreId carries
# the package name or bundle id and is the identifier that cannot drift, so it
# is tried first; the name is only the fallback for an app AdMob has not linked
# to a store listing yet.
by_store, by_name = {}, {}
for a in existing_apps:
    plat = a.get("platform")
    linked = a.get("linkedAppInfo") or {}
    if linked.get("appStoreId"):
        by_store[(linked["appStoreId"], plat)] = a
    for nm in {(a.get("manualAppInfo") or {}).get("displayName"),
               linked.get("displayName")} - {None}:
        by_name.setdefault((_norm(nm), plat), a)
print(f"AdMob already holds {len(existing_apps)} app(s)")

existing_units, _ = paged(f"{API}/{publisher}/adUnits", "adUnits")
units_by_app = {}
for u in existing_units:
    units_by_app.setdefault(u.get("appId"), set()).add(u.get("displayName"))

apps = json.load(open(M / "apps.json"))["apps"]
if args.apps:
    want = {s.strip() for s in args.apps.split(",")}
    apps = [a for a in apps if a["repo"] in want]

# --sync: write back exactly what AdMob holds today, in the shape the build
# reads. This is how ids created in the AdMob console reach the repository —
# the v1beta write methods are not granted to this publisher (MA-027), so for
# now every id is made by hand and has to be collected rather than returned.
if args.sync:
    target = M / "docs/admob-ids.json"
    merged = json.loads(target.read_text()) if target.exists() else {}
    units_by_app_id = {}
    for u in existing_units:
        units_by_app_id.setdefault(u.get("appId"), []).append(u)
    touched = 0
    for a in apps:
        repo = a["repo"]
        sp = M / "store/apps" / f"{repo}.json"
        display = repo
        if sp.exists():
            display = (json.load(open(sp)).get("copy", {}).get("en", {}) or {}).get("name") or repo
        rec = merged.setdefault(repo, {})
        for platform, store_id, prefix in (("ANDROID", a["application_id"], "android"),
                                           ("IOS", a["bundle_id"], "ios")):
            app = (by_store.get((store_id, platform))
                   or by_name.get((_norm(display), platform)))
            if not app:
                continue
            rec[f"{prefix}_app_id"] = app["appId"]
            for u in units_by_app_id.get(app["appId"], []):
                fmt = (u.get("adFormat") or "").lower()
                if fmt in ("banner", "interstitial"):
                    rec[f"{prefix}_{fmt}"] = u.get("adUnitId")
            touched += 1
    target.write_text(json.dumps(merged, indent=1) + "\n")
    have = sum(1 for r in merged.values() for k in ("android_app_id", "ios_app_id") if r.get(k))
    print(f"\nsynced {touched} platform record(s); {have} of 86 app ids now recorded")
    print(f"-> {target}")
    raise SystemExit(0)

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
        app = by_store.get((store_id, platform)) or by_name.get((_norm(display), platform))
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
            app = d
            by_store[(store_id, platform)] = app
            by_name[(_norm(display), platform)] = app
            created_apps += 1
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
# docs/admob-ids.json is the file the build reads. A run that created nothing
# must never replace it — an earlier version of this script overwrote the real
# ids with a page of "The caller does not have permission" records. Merge only
# the entries that actually carry an appId.
if not args.dry_run and (created_apps or created_units):
    target = M / "docs/admob-ids.json"
    merged = json.loads(target.read_text()) if target.exists() else {}
    for repo, rec in out.items():
        keep = {k: v for k, v in rec.items()
                if isinstance(v, dict) and v.get("appId") or k == "units"}
        if keep:
            merged.setdefault(repo, {}).update(keep)
    target.write_text(json.dumps(merged, indent=1) + "\n")
    print("-> docs/admob-ids.json")
elif not args.dry_run:
    print("nothing was created, so docs/admob-ids.json is left alone")
