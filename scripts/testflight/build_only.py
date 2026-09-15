#!/usr/bin/env python3
"""Build signed App Store IPAs (no upload) for the named apps and copy them to
~/agl/.dist/ipa-for-asc/<Repo>-<build>.ipa — for dragging into App Store Connect."""
import json, os, pathlib, shutil, subprocess, sys, time, datetime
ROOT = pathlib.Path("/Users/spatchava/agl"); OUT = ROOT / ".dist/ipa-for-asc"; OUT.mkdir(parents=True, exist_ok=True)
apps = {a["repo"]: a for a in json.load(open(ROOT / "agl-manifest/apps.json"))["apps"]}
bn = datetime.datetime.now().strftime("%Y%m%d%H")
lock = ROOT / ".dist/ios-batch/current_app"
for repo in sys.argv[1:]:
    a = apps[repo]; d = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
    lock.write_text(repo); t0 = time.time()
    log = ROOT / ".dist/ios-logs" / f"{repo}-buildonly.log"
    with open(log, "w") as fh:
        rc = subprocess.call(["bundle", "exec", "fastlane", "ios", "ship", f"app_dir:{d}", f"bundle_id:{a['bundle_id']}", f"build_number:{bn}", "upload:false"],
                             cwd=pathlib.Path(__file__).parent, stdout=fh, stderr=subprocess.STDOUT)
    lock.write_text("")
    ipas = sorted((d / "build/ios/ipa").glob("*.ipa"), key=lambda p: p.stat().st_mtime)
    if rc == 0 and ipas:
        dst = OUT / f"{repo}-{bn}.ipa"; shutil.copy(ipas[-1], dst)
        print(f"{repo:18} OK  {dst.name} ({dst.stat().st_size//1_048_576} MB, {round(time.time()-t0)}s)", flush=True)
    else:
        err = next((l for l in reversed(log.read_text(errors='replace').splitlines()) if 'error:' in l or '[!]' in l), '')[:160]
        print(f"{repo:18} FAILED ({round(time.time()-t0)}s) {err}", flush=True)
