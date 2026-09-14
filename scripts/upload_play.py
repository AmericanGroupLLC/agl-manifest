#!/usr/bin/env python3
"""Upload every signed .aab in ~/agl/.dist to Google Play's internal testing track.

NOT YET RUN — it needs a Play Console service-account JSON, which does not exist
on this machine (docs/MANUAL_ACTIONS.md MA-003). Once it does:

    export PLAY_JSON_KEY_FILE=~/agl-secrets/play-service-account.json
    python3 ~/agl/.dist/upload_play.py            # all apps
    python3 ~/agl/.dist/upload_play.py BodyQuest  # one app

Draft apps get a draft release (Play refuses anything else on a Draft app);
apps already in Production get a normal internal-testing release. Google may
still reject the very first bundle of a brand-new app over the API — if so the
log says so and that app's first upload has to be done in the Play Console UI.
"""
import datetime, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path("/Users/spatchava/agl")
DIST = ROOT / ".dist"
LOGS = DIST / "play-logs"; LOGS.mkdir(exist_ok=True)
RESULTS = DIST / "play-results.json"
KEY = os.environ.get("PLAY_JSON_KEY_FILE", "")
if not KEY or not pathlib.Path(KEY).expanduser().exists():
    sys.exit("PLAY_JSON_KEY_FILE is not set or the file does not exist — see docs/MANUAL_ACTIONS.md MA-003")
KEY = str(pathlib.Path(KEY).expanduser())

apps = json.load(open(ROOT / "agl-manifest/apps.json"))["apps"]
if len(sys.argv) > 1:
    wanted = {s.lower() for s in sys.argv[1:]}
    apps = [a for a in apps if a["repo"].lower() in wanted]
results = json.load(open(RESULTS)) if RESULTS.exists() else {}
env = dict(os.environ, LC_ALL="en_US.UTF-8", BUNDLE_GEMFILE=str(ROOT / "agl-manifest/Gemfile"),
           PATH=f"{pathlib.Path.home()}/.rbenv/shims:" + os.environ["PATH"])

for a in apps:
    repo, pkg = a["repo"], a["application_id"]
    aab = next(iter(sorted(DIST.glob(f"{repo}-*.aab"))), None)
    if not aab:
        results[repo] = {"status": "no-aab"}; print(f"{repo}: no .aab in {DIST}"); continue
    if results.get(repo, {}).get("status") == "uploaded":
        print(f"{repo}: already uploaded"); continue
    log = LOGS / f"{repo}.log"
    cmd = ["bundle", "exec", "fastlane", "run", "upload_to_play_store", f"package_name:{pkg}", f"aab:{aab}",
           "track:internal", "release_status:draft", f"json_key:{KEY}", "skip_upload_metadata:true",
           "skip_upload_images:true", "skip_upload_screenshots:true", "skip_upload_changelogs:true"]
    print(f"{repo}: {pkg} <- {aab.name}", flush=True)
    with open(log, "w") as fh:
        rc = subprocess.call(cmd, cwd=ROOT / "agl-manifest", env=env, stdout=fh, stderr=subprocess.STDOUT)
    text = log.read_text(errors="replace")
    ok = rc == 0 and "Successfully finished the upload" in text
    err = "" if ok else next((l.strip()[:300] for l in reversed(text.splitlines()) if "[!]" in l or "Error" in l), text[-300:])
    results[repo] = {"status": "uploaded" if ok else "failed", "package": pkg, "aab": aab.name, "error": err,
                     "at": datetime.datetime.now().isoformat(timespec="seconds"), "log": str(log)}
    json.dump(results, open(RESULTS, "w"), indent=1)
    print(f"    {'uploaded' if ok else 'FAILED ' + err}", flush=True)

n_ok = sum(1 for v in results.values() if v["status"] == "uploaded")
print(f"\nuploaded {n_ok}/{len(results)} -> {RESULTS}")
