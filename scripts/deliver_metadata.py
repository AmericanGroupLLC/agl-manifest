#!/usr/bin/env python3
"""Push each app's listing to App Store Connect without submitting for review:
metadata text + URLs + review notes + category (deliver), the age-rating answers,
the privacy "nutrition label", and — when present — the screenshots.

    source scripts/testflight/env.sh
    python3 scripts/deliver_metadata.py AGRecorder            # one app
    python3 scripts/deliver_metadata.py --eligible            # every app with an ASC record and unblocked copy
    python3 scripts/deliver_metadata.py --eligible --screenshots

Skips apps whose store JSON is `_blocked` (no honest copy exists). CodeDeal was
skipped here too, for analyzer errors it no longer has. Never passes submit_for_review. Results in
~/agl/.dist/deliver-results.json, logs in ~/agl/.dist/deliver-logs/.
"""
import datetime, json, os, pathlib, re, subprocess, sys
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402
LOGS = ROOT / ".dist/deliver-logs"; LOGS.mkdir(parents=True, exist_ok=True)
RESULTS = ROOT / ".dist/deliver-results.json"
KEYJSON = ROOT / ".dist/ios-batch/asc-key.json"
apps = json.load(open(M / "apps.json"))["apps"]
recs = {r["bundleId"] for r in json.load(open(M / "docs/appstore-records.json"))}
names = [x for x in sys.argv[1:] if not x.startswith("--")]
with_shots = "--screenshots" in sys.argv
def blocked(repo):
    p = M / "store/apps" / f"{repo}.json"
    return p.exists() and "_blocked" in json.load(open(p))
if names: sel = [a for a in apps if a["repo"] in names]
else: sel = [a for a in apps if a["bundle_id"] in recs and not blocked(a["repo"])]
results = json.load(open(RESULTS)) if RESULTS.exists() else {}
# Render the listing text from store/apps/<repo>.json into every repo first.
# deliver uploads the repo's fastlane/metadata, and those copies had drifted:
# on 2026-10-09 GadgetNest's still advertised a price-history chart and
# AGRecorder's a cloud sync, both removed from the app and from the manifest.
_gen = subprocess.run(["python3", str(M / "scripts/store_metadata.py"), "generate"],
                      capture_output=True, text=True)
if _gen.returncode != 0:
    sys.exit("store_metadata.py generate failed — not uploading stale listing text:\n" + _gen.stderr[-400:])
env = dict(os.environ, LC_ALL="en_US.UTF-8")
for a in sel:
    repo = a["repo"]; d = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
    ver = a["version"].split("+")[0]
    rating = M / "store/ratings" / (f"{repo}.json" if (M / "store/ratings" / f"{repo}.json").exists() else "default.json")
    shots = d / "fastlane/screenshots"
    use_shots = with_shots and any(shots.glob("en-US/*.png"))
    # Never upload a set App Review would reject under 2.3.3. The same audit
    # that reads what App Store Connect holds reads what is about to replace it.
    shot_block = ""
    if use_shots:
        aud = subprocess.run(["python3", str(M / "scripts/screenshot_audit.py"), "--local", repo],
                             capture_output=True, text=True)
        if " FAIL " in aud.stdout or aud.returncode != 0:
            use_shots = False
            shot_block = "screenshots not uploaded — local set fails 2.3.3: " + \
                " ".join(l.strip() for l in aud.stdout.splitlines()[1:3])[:200]
    log = LOGS / f"{repo}.log"; out = {"repo": repo, "version": ver, "at": datetime.datetime.now().isoformat(timespec="seconds")}
    cmd = ["bundle", "exec", "fastlane", "run", "deliver", f"api_key_path:{KEYJSON}", f"app_identifier:{a['bundle_id']}", f"app_version:{ver}",
           f"metadata_path:{d/'fastlane/metadata'}", "skip_binary_upload:true", "force:true", "run_precheck_before_submit:false",
           "precheck_include_in_app_purchases:false", "ignore_language_directory_validation:true", "submit_for_review:false",
           f"app_rating_config_path:{rating}"]
    cmd += [f"screenshots_path:{shots}", "overwrite_screenshots:true", "skip_screenshots:false"] if use_shots else ["skip_screenshots:true"]
    with open(log, "w") as fh:
        rc = subprocess.call(cmd, cwd=M / "scripts/testflight", env=env, stdout=fh, stderr=subprocess.STDOUT)
    text = log.read_text(errors="replace"); out["deliver"] = "ok" if rc == 0 else "failed"
    if rc: out["deliver_error"] = next((l.strip()[:300] for l in reversed(text.splitlines()) if "[!]" in l or "Error" in l), text[-300:])
    # The privacy "nutrition label" is not in the App Store Connect API; fastlane's
    # upload_app_privacy_details_to_app_store needs an Apple ID web session, which
    # this machine does not have (MA-011). The answers are in store/privacy/<repo>.json.
    out["privacy"] = "human (MA-011)"; out["screenshots"] = use_shots
    if shot_block: out["screenshots_blocked"] = shot_block
    results[repo] = out; json.dump(results, open(RESULTS, "w"), indent=1)
    print(f"{repo:18} deliver={out['deliver']} screenshots={use_shots} {out.get('deliver_error','')[:160]} {shot_block}", flush=True)
