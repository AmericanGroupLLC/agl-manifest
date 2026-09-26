#!/usr/bin/env python3
"""Ask Google Play what is actually there, per package.

The local upload-evidence file is not trustworthy: a single-app run overwrites
it wholesale, so it reflects the last invocation rather than the portfolio. The
API is the only ground truth for "does this listing exist" and "what version
code is in the internal track".
"""
import json, pathlib, subprocess, urllib.error, urllib.request

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402
KEY = ROOT / ".secrets/play-publisher-agl.json"
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"

def token():
    s = ('require "googleauth"; '
         f'c=Google::Auth::ServiceAccountCredentials.make_creds(json_key_io: File.open("{KEY}"), '
         'scope: "https://www.googleapis.com/auth/androidpublisher"); '
         'print c.fetch_access_token!["access_token"]')
    r = subprocess.run(["bundle", "exec", "ruby", "-e", s], cwd=str(MANIFEST),
                       capture_output=True, text=True, timeout=300)
    if not r.stdout.strip():
        raise RuntimeError(r.stderr[-300:])
    return r.stdout.strip()

def call(method, url, tok, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"raw": raw[:200]}

tok = token()
apps = [a for a in json.loads((MANIFEST / "apps.json").read_text())["apps"] if a.get("flutter")]
out = []
for a in apps:
    pkg = a.get("application_id") or a["bundle_id"]
    code, edit = call("POST", f"{API}/{pkg}/edits", tok)
    rec = {"repo": a["repo"], "package": pkg}
    if code != 200:
        msg = str(edit.get("error", {}).get("message", edit))[:150]
        rec["state"] = "NO_LISTING" if code == 404 else f"HTTP_{code}"
        rec["detail"] = msg
    else:
        eid = edit["id"]
        c2, tr = call("GET", f"{API}/{pkg}/edits/{eid}/tracks/internal", tok)
        vcs = []
        if c2 == 200:
            for rel in tr.get("releases", []):
                vcs += [(v, rel.get("status")) for v in rel.get("versionCodes", [])]
        rec["state"] = "HAS_BUNDLE" if vcs else "LISTING_EMPTY"
        rec["internal"] = [f"{v}:{s}" for v, s in vcs]
        call("DELETE", f"{API}/{pkg}/edits/{eid}", tok)  # don't leave edits dangling
    out.append(rec)
    print(f"{rec['repo']:<20} {rec['state']:<14} {rec.get('internal') or rec.get('detail','')}", flush=True)

(ROOT / ".dist/play-state.json").write_text(json.dumps(out, indent=1))
from collections import Counter
print("\n" + str(Counter(r["state"] for r in out)))
