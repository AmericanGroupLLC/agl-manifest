#!/usr/bin/env python3
"""Publish every app's App Store privacy "nutrition label" from store/privacy.

    source scripts/testflight/env.sh
    python3 scripts/testflight/privacy_upload.py              # every app
    python3 scripts/testflight/privacy_upload.py AGrammarly   # one app

Renders store/privacy/<repo>.json with privacy_to_fastlane.py, then runs the
`ios privacy` lane (upload_app_privacy_details_to_app_store) per app.

Needs the Apple ID web session env.sh exports (FASTLANE_SESSION) as well as
the API key: Apple's public API has no data-usage publish endpoint. Apps that
track (ATT) are refused by Apple's API — see MA-011.

Results -> <DIST>/privacy-upload.json.
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from agl_paths import MANIFEST as M, DIST  # noqa: E402

only = {a.lower() for a in sys.argv[1:] if not a.startswith("--")}
subprocess.run([sys.executable, str(M / "scripts/privacy_to_fastlane.py")], check=True, capture_output=True)
apps = [a for a in json.load(open(M / "apps.json"))["apps"] if not only or a["repo"].lower() in only]
results = {}
for a in apps:
    src = M / "store/privacy/fastlane" / f"{a['repo']}.json"
    if not src.exists():
        results[a["repo"]] = {"status": "no_label"}
        continue
    r = subprocess.run(["bundle", "exec", "fastlane", "ios", "privacy", f"bundle_id:{a['bundle_id']}", f"json:{src}"],
                       cwd=HERE, capture_output=True, text=True, timeout=600)
    out = r.stdout + r.stderr
    ok = r.returncode == 0 and "finished successfully" in out
    pub = next((l.split("PRIVACY_PUBLISHED", 1)[1].strip() for l in out.splitlines() if "PRIVACY_PUBLISHED" in l), "")
    note = f"published ({pub})" if ok else ""
    err = "" if ok else ("binary tracks users: needs App Store Connect UI or a build without ATT (MA-011)"
                         if "binary indicates that your app tracks users" in out else None) or next((l.strip() for l in reversed(out.splitlines()) if "rror" in l), out[-300:].strip())[:300]
    results[a["repo"]] = {"status": "ok" if ok else "failed", "note": note, "error": err}
    print(f"  {a['repo']:18} {'ok    ' if ok else 'FAILED'} {note or err}", flush=True)
DIST.mkdir(parents=True, exist_ok=True)
(DIST / "privacy-upload.json").write_text(json.dumps(results, indent=1))
bad = [k for k, v in results.items() if v["status"] != "ok"]
print(f"\n  {len(results) - len(bad)}/{len(results)} labels published; failed: {', '.join(bad) or 'none'}")
sys.exit(1 if bad else 0)
