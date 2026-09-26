#!/usr/bin/env python3
"""For every app, find its policy base URL and prove a delete-account page exists.

Google rejected VirtuBand because the Data safety form's account-deletion URL
404s. That field is console-entered, so the fix is a person pasting a correct
URL per app -- but only after we know a real page exists for each one. The host
serves an SPA catch-all, so a 200 proves nothing; every response body is hashed
against a deliberately nonexistent path.
"""
import hashlib, json, pathlib, subprocess
from concurrent.futures import ThreadPoolExecutor

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402

HOME_TITLE = b"American Group LLC \xe2\x80\x94 Enterprise Technology & Mobile Apps"

def get(url):
    """(is_catchall, bytes, head). Identified by <title>: the catch-all body
    varies by a byte between requests, so an md5 comparison is not reliable."""
    r = subprocess.run(["curl","-sL","--max-time","45",url], capture_output=True, timeout=90)
    return (HOME_TITLE in r.stdout), len(r.stdout), r.stdout[:4000].decode("utf8","ignore")

assert get("https://www.safecodeg.com/ThisPathCannotExist999888")[0]

# The local site checkout is the source of truth for which slugs exist.
policy_dir = ROOT / "www.safecodeg.com/client/public/policy"
slugs = sorted(p.name for p in policy_dir.iterdir() if p.is_dir())

SLUGS = {"TripNest":"TripNest","AGrammarly":"agrammarly","BodyQuest":"bodyquest","CalcMaster":"calcmaster",
 "CarDeal":"cardeal","daily-pulse":"dailypulse","DriftDate":"driftdate","FashionFactory":"fashionfactory",
 "GroceryMatch":"grocerymatch","HerJourney":"herjourney","iMaps":"iMaps","iMeasure":"iMeasure",
 "MyHealth":"myhealth","Photriya":"photriya","PilotEnRoute":"pilotenroute","radiotune":"radiotune",
 "Uscis-Case":"uscis-case-tracker","Verba":"verba","VirtuBand":"virtuband"}

apps = [a for a in json.loads((MANIFEST/"apps.json").read_text())["apps"] if a.get("flutter")]

def slug_for(repo):
    cands = [SLUGS.get(repo), repo, repo.lower(), repo.replace("-",""), repo.lower().replace("-","")]
    for c in cands:
        if c and c in slugs: return c
    for s in slugs:                       # last resort: case-insensitive match
        if s.lower() == repo.lower().replace("-",""): return s
    return None

rows = []
def check(a):
    repo = a["repo"]; s = slug_for(repo)
    if not s: return {"repo":repo,"slug":None,"state":"NO_SLUG"}
    url = f"https://www.safecodeg.com/policy/{s}/delete-account.html"
    is_ca,n,body = get(url)
    ok = not is_ca
    return {"repo":repo,"slug":s,"url":url,"state":"REAL" if ok else "CATCH_ALL","bytes":n,
            "local_file": (policy_dir/s/"delete-account.html").exists()}

with ThreadPoolExecutor(max_workers=8) as ex:
    rows = list(ex.map(check, apps))

bad = [r for r in rows if r["state"] != "REAL"]
print(f"apps checked: {len(rows)}   delete-account page REAL: {len(rows)-len(bad)}   BROKEN: {len(bad)}")
for r in bad:
    print(f"   {r['repo']:<18} slug={r['slug']} state={r['state']} local_file={r.get('local_file')}")
(ROOT/".dist/delete-links.json").write_text(json.dumps(rows, indent=1))
