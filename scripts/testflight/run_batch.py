#!/usr/bin/env python3
"""Ship every selected app to TestFlight, one after another, and record the outcome.

    python3 run_batch.py --wave records        # apps whose bundle id already has an ASC record
    python3 run_batch.py --apps AGCleaner,ChefCount

Writes ~/agl/.dist/ios-batch/results.json after every app so a crash loses nothing.
"""
import argparse, datetime, json, os, pathlib, signal, subprocess, sys, time

PER_APP_TIMEOUT = 60 * 60
def purge_derived_data(max_age_min=5):
    """Xcode leaves several GB per archive in DerivedData; 43 apps filled the disk
    on 2026-09-14. Remove Runner-*/Pods-* trees not touched in the last few minutes."""
    import shutil, time
    dd = pathlib.Path.home() / "Library/Developer/Xcode/DerivedData"
    now = time.time()
    for d in dd.glob("*"):
        if d.name.startswith(("Runner-", "Pods-")) and d.is_dir() and now - d.stat().st_mtime > max_age_min * 60:
            shutil.rmtree(d, ignore_errors=True)
  # archive + up to three upload attempts

ROOT = pathlib.Path("/Users/spatchava/agl")
HERE = pathlib.Path(__file__).resolve().parent
LOGS = ROOT / ".dist/ios-logs"
RESULTS = ROOT / ".dist/ios-batch/results.json"  # outside git, next to the logs
MANIFEST = json.load(open(ROOT / "agl-manifest/apps.json"))["apps"]
RECORDS = {r["bundleId"] for r in json.load(open(ROOT / "agl-manifest/docs/appstore-records.json"))}
SKIP = {"CalcMaster", "CodeDeal"}  # CalcMaster ran on its own lane; CodeDeal does not compile

ap = argparse.ArgumentParser()
ap.add_argument("--wave", choices=["records", "all"], default="records")
ap.add_argument("--apps", default="")
args = ap.parse_args()

apps = MANIFEST
if args.apps:
    wanted = {s.strip().lower() for s in args.apps.split(",")}
    apps = [a for a in apps if a["repo"].lower() in wanted]
elif args.wave == "records":
    apps = [a for a in apps if a["bundle_id"] in RECORDS and a["repo"] not in SKIP]

results = json.load(open(RESULTS)) if RESULTS.exists() else {}
env = os.environ.copy()
build_number = datetime.datetime.now().strftime("%Y%m%d%H")
LOGS.mkdir(parents=True, exist_ok=True)

for i, a in enumerate(apps, 1):
    purge_derived_data()
    SHOTS = pathlib.Path("/Users/spatchava/agl/.dist/screenshots_current")
    while SHOTS.exists() and SHOTS.read_text().strip() == a["repo"]:
        print(f"    screenshots.py is building {a['repo']} — waiting", flush=True); time.sleep(60)
    LOCK = pathlib.Path("/Users/spatchava/agl/.dist/ios-batch/current_app"); LOCK.write_text(a["repo"])  # screenshots.py waits while this names its app

    repo = a["repo"]
    if results.get(repo, {}).get("status") == "uploaded":
        print(f"[{i}/{len(apps)}] {repo}: already uploaded, skipping"); continue
    app_dir = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
    log = LOGS / f"{repo}.log"
    print(f"[{i}/{len(apps)}] {repo} ({a['bundle_id']}) -> {log}", flush=True)
    t0 = time.time()
    # Hard wall-clock cap per app. Ruby's Timeout cannot interrupt a blocked
    # altool child, so the cap lives here: kill the whole process group, then ask
    # App Store Connect whether the build arrived anyway (it usually did).
    with open(log, "w") as fh:
        proc = subprocess.Popen(
            ["bundle", "exec", "fastlane", "ios", "ship", f"app_dir:{app_dir}", f"bundle_id:{a['bundle_id']}", f"build_number:{build_number}", "reuse_ipa:true"],
            cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=PER_APP_TIMEOUT)
        except subprocess.TimeoutExpired:
            fh.write(f"\n[run_batch] TIMEOUT after {PER_APP_TIMEOUT}s — killing process group\n")
            os.killpg(proc.pid, signal.SIGKILL)
            subprocess.call(["pkill", "-f", "altool --upload-app"])
            rc = -9
    text = log.read_text(errors="replace")
    status = "uploaded" if rc == 0 and "UPLOADED" in text else "failed"
    if status == "failed":
        chk = subprocess.run(["bundle", "exec", "ruby", "check_build.rb", a["bundle_id"], build_number],
                             cwd=HERE, env=env, capture_output=True, text=True)
        with open(log, "a") as fh:
            fh.write(f"\n[run_batch] post-check: {chk.stdout.strip()} {chk.stderr.strip()[-200:]}\n")
        if chk.returncode == 0:
            status = "uploaded"
            text += "\nUPLOADED (confirmed by post-check)\n"
    # last fastlane error line, for the summary
    err = ""
    if status == "failed":
        lines = [l for l in text.splitlines() if "Error" in l or "error:" in l.lower() or "user_error" in l]
        err = (lines[-1] if lines else text[-400:]).strip()[:300]
    results[repo] = {"status": status, "rc": rc, "seconds": round(time.time() - t0), "build_number": build_number,
                     "bundle_id": a["bundle_id"], "log": str(log), "error": err, "at": datetime.datetime.now().isoformat(timespec="seconds")}
    json.dump(results, open(RESULTS, "w"), indent=1)
    LOCK.write_text("")
    print(f"    {status} in {results[repo]['seconds']}s {err}", flush=True)

ok = [r for r, v in results.items() if v["status"] == "uploaded"]
bad = [r for r, v in results.items() if v["status"] != "uploaded"]
print(f"\nuploaded: {len(ok)}  failed: {len(bad)}  -> {RESULTS}")
sys.exit(1 if bad else 0)
