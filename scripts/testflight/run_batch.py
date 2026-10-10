#!/usr/bin/env python3
"""Ship every selected app to TestFlight, one after another, and record the outcome.

    python3 run_batch.py --wave records        # apps whose bundle id already has an ASC record
    python3 run_batch.py --apps AGCleaner,ChefCount

Writes ~/agl/.dist/ios-batch/results.json after every app so a crash loses nothing.
"""
import argparse, datetime, json, os, pathlib, signal, subprocess, sys, time
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT  # noqa: E402

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

ROOT = _ROOT
HERE = pathlib.Path(__file__).resolve().parent
LOGS = ROOT / ".dist/ios-logs"
RESULTS = ROOT / ".dist/ios-batch/results.json"  # outside git, next to the logs
MANIFEST = json.load(open(_MANIFEST / "apps.json"))["apps"]
RECORDS = {r["bundleId"] for r in json.load(open(_MANIFEST / "docs/appstore-records.json"))}
# Was {"CalcMaster", "CodeDeal"}: CalcMaster because it once ran on its own
# lane, CodeDeal because it did not compile. Both expired — CodeDeal analyzes
# clean and shipped to Play at v16 on 2026-09-25 — and between them they were
# silently removing two apps from every wave, which is why the last batch ran
# 27 and not 29. Keep it empty; a reason to skip an app belongs in the
# manifest where every script can see it, not in one script's constant.
SKIP: set[str] = set()

ap = argparse.ArgumentParser()
ap.add_argument("--no-distribute", action="store_true", help="upload only; do not add the build to the tester group")
ap.add_argument("--wave", choices=["records", "all"], default="records")
ap.add_argument("--apps", default="")
ap.add_argument("--no-resume", action="store_true",
                help="ignore a previous run's results instead of skipping apps it "
                     "recorded as uploaded. A results file from 2026-09-15 once made "
                     "a whole run report 'uploaded: 30, failed: 0' in under two "
                     "minutes having uploaded nothing. CI always passes this.")
args = ap.parse_args()

apps = MANIFEST
if args.apps:
    wanted = {s.strip().lower() for s in args.apps.split(",")}
    apps = [a for a in apps if a["repo"].lower() in wanted]
# store_eligible is honoured, but nothing sets it false any more — all 43
# apps are in scope. The filter stays so the manifest can exclude one again.
else:
    apps = [a for a in apps if a.get("store_eligible", True)]
    if args.wave == "records":
        apps = [a for a in apps if a["bundle_id"] in RECORDS and a["repo"] not in SKIP]

if args.no_resume and RESULTS.exists():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = RESULTS.with_name(f"{RESULTS.name}.{stamp}.bak")
    RESULTS.rename(backup)
    print(f"--no-resume: previous results moved aside as {backup.name}")
results = json.load(open(RESULTS)) if RESULTS.exists() else {}
env = os.environ.copy()
build_number = datetime.datetime.now().strftime("%Y%m%d%H%M")
LOGS.mkdir(parents=True, exist_ok=True)

for i, a in enumerate(apps, 1):
    purge_derived_data()
    SHOTS = _ROOT / ".dist/screenshots_current"
    while SHOTS.exists() and SHOTS.read_text().strip() == a["repo"]:
        print(f"    screenshots.py is building {a['repo']} — waiting", flush=True); time.sleep(60)
    LOCK = _ROOT / ".dist/ios-batch/current_app"
    # The directory exists on the laptop but not on a fresh CI runner, where
    # this line raised FileNotFoundError and failed every 'Upload to
    # TestFlight' step (issue #4, found by the AI office's daily pass).
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(a["repo"])  # screenshots.py waits while this names its app

    repo = a["repo"]
    if results.get(repo, {}).get("status") == "uploaded":
        LOCK.write_text("")  # never leave a skipped app's name in the lock
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

    # Uploading is not delivering: a build reaches people only through a beta
    # group. Do that straight away so every app lands in testers' TestFlight
    # without a second manual pass.
    if status == "uploaded" and not args.no_distribute:
        d = subprocess.run(["bundle", "exec", "ruby", "distribute.rb", "--app", repo],
                           cwd=HERE, env=env, capture_output=True, text=True, timeout=1800)
        print("    " + (d.stdout.strip().splitlines() or ["distribute produced no output"])[-1], flush=True)

ok = [r for r, v in results.items() if v["status"] == "uploaded"]
bad = [r for r, v in results.items() if v["status"] != "uploaded"]
print(f"\nuploaded: {len(ok)}  failed: {len(bad)}  -> {RESULTS}")
sys.exit(1 if bad else 0)
