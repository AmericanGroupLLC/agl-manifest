#!/usr/bin/env python3
"""Ship every selected app to TestFlight, one after another, and record the outcome.

    python3 run_batch.py --wave records        # apps whose bundle id already has an ASC record
    python3 run_batch.py --apps AGCleaner,ChefCount

Writes ~/agl/.dist/ios-batch/results.json after every app so a crash loses nothing.
"""
import argparse, datetime, json, os, pathlib, shlex, signal, subprocess, sys, time
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
ap.add_argument("--no-beta-review", action="store_true",
                help="distribute without submitting the build to Beta App Review for the external group "
                     "(distribute.rb --no-submit). Internal testers get it either way. ship.yml's internal "
                     "stage passes this: its job is TestFlight internal, and every submission in run "
                     "38812509219 was refused anyway ('Beta contract is missing', an Account Holder step).")
ap.add_argument("--wave", choices=["records", "all"], default="records")
ap.add_argument("--apps", default="")
ap.add_argument("--prebuilt", default="",
                help="directory of <repo>.ipa files already built and signed (ship.yml's iOS "
                     "shard); upload those instead of building from source. An app with no "
                     "IPA there is reported as no_ipa — its build failure is the build job's.")
ap.add_argument("--defer-listing", action="store_true",
                help="upload every app first, then wait for App Store Connect to list all of "
                     "the uploaded builds together, for at most --listing-cap-min in total. "
                     "Without it each app waits for its own build before the next upload "
                     "starts, and one build Apple never lists costs the full per-app timeout "
                     "(PilotEnRoute and yourtube, 3,600 s each in ship run 38294393167, #27). "
                     "An app still counts as uploaded only once App Store Connect lists it.")
ap.add_argument("--listing-cap-min", type=int, default=30,
                help="with --defer-listing: minutes to wait, after the last upload, for "
                     "App Store Connect to list every uploaded build (default 30)")
ap.add_argument("--per-app-timeout", type=int, default=PER_APP_TIMEOUT,
                help=f"hard wall-clock cap per app's upload, in seconds (default {PER_APP_TIMEOUT})")
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
    lane_args = []
    app_build = build_number
    if args.prebuilt:
        ipa = pathlib.Path(args.prebuilt).resolve() / f"{repo}.ipa"
        if not ipa.exists():
            results[repo] = {"status": "no_ipa", "bundle_id": a["bundle_id"], "error": f"no {ipa.name} in {args.prebuilt}",
                             "at": datetime.datetime.now().isoformat(timespec="seconds")}
            json.dump(results, open(RESULTS, "w"), indent=1)
            LOCK.write_text("")
            print(f"[{i}/{len(apps)}] {repo}: no prebuilt IPA, skipping", flush=True); continue
        # The same gate transporter_upload.py applies. CI ships through this
        # path, which used to upload without it: MileMaster build 2 reached
        # Apple without NSLocationAlwaysAndWhenInUseUsageDescription and came
        # back as ITMS-90683, a warning privacy_scan.py would have raised here.
        _sys.path.insert(0, str(HERE))
        from transporter_upload import ipa_blocker
        why = ipa_blocker(ipa)
        if why:
            results[repo] = {"status": "blocked", "bundle_id": a["bundle_id"], "error": why,
                             "at": datetime.datetime.now().isoformat(timespec="seconds")}
            json.dump(results, open(RESULTS, "w"), indent=1)
            LOCK.write_text("")
            print(f"[{i}/{len(apps)}] {repo}: NOT uploaded — {why}", flush=True); continue
        lane_args = [f"ipa:{ipa}"]
        if args.defer_listing:
            # The lane returns once the upload command completes; the listing
            # wait happens below, for every app at once. Between failed
            # attempts it still checks App Store Connect, for 5 minutes, so a
            # retry is not refused as a duplicate of a build that did land.
            lane_args += ["defer_listing:true", "listing_wait_minutes:5"]
        # The post-check must ask for the build number inside the IPA, not this run's clock.
        r = subprocess.run(f"unzip -p {shlex.quote(str(ipa))} 'Payload/*.app/Info.plist' | plutil -extract CFBundleVersion raw -o - -",
                           shell=True, capture_output=True, text=True)
        app_build = r.stdout.strip() or build_number
    log = LOGS / f"{repo}.log"
    print(f"[{i}/{len(apps)}] {repo} ({a['bundle_id']}) -> {log}", flush=True)
    t0 = time.time()
    # Hard wall-clock cap per app. Ruby's Timeout cannot interrupt a blocked
    # altool child, so the cap lives here: kill the whole process group, then ask
    # App Store Connect whether the build arrived anyway (it usually did).
    with open(log, "w") as fh:
        proc = subprocess.Popen(
            ["bundle", "exec", "fastlane", "ios", "ship", f"app_dir:{app_dir}", f"bundle_id:{a['bundle_id']}", f"build_number:{app_build}", "reuse_ipa:true", *lane_args],
            cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=args.per_app_timeout)
        except subprocess.TimeoutExpired:
            fh.write(f"\n[run_batch] TIMEOUT after {args.per_app_timeout}s — killing process group\n")
            os.killpg(proc.pid, signal.SIGKILL)
            subprocess.call(["pkill", "-f", "altool --upload-app"])
            rc = -9
    text = log.read_text(errors="replace")
    status = "uploaded" if rc == 0 and "UPLOADED" in text else "failed"
    # Sent, not yet proven: confirmed (or not) by the listing poll after the loop.
    if status == "failed" and args.defer_listing and rc == 0 and "UPLOAD_SENT" in text:
        status = "sent"
    if status == "failed":
        chk = subprocess.run(["bundle", "exec", "ruby", "check_build.rb", a["bundle_id"], app_build],
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
    results[repo] = {"status": status, "rc": rc, "seconds": round(time.time() - t0), "build_number": app_build,
                     "bundle_id": a["bundle_id"], "log": str(log), "error": err, "at": datetime.datetime.now().isoformat(timespec="seconds")}
    json.dump(results, open(RESULTS, "w"), indent=1)
    LOCK.write_text("")
    print(f"    {status} in {results[repo]['seconds']}s {err}", flush=True)

    # Uploading is not delivering: a build reaches people only through a beta
    # group. Do that straight away so every app lands in testers' TestFlight
    # without a second manual pass.
    if status == "uploaded" and not args.no_distribute:
        d = subprocess.run(["bundle", "exec", "ruby", "distribute.rb", "--app", repo, *(["--no-submit"] if args.no_beta_review else [])],
                           cwd=HERE, env=env, capture_output=True, text=True, timeout=1800)
        print("    " + (d.stdout.strip().splitlines() or ["distribute produced no output"])[-1], flush=True)

# --defer-listing: every upload has been sent; now prove each one arrived.
# One App Store Connect query per pending app per minute, all apps together,
# with one deadline for the lot instead of an hour per app.
pending = {r: v for r, v in results.items() if v["status"] == "sent"}
if pending:
    cap = args.listing_cap_min * 60
    print(f"\nwaiting up to {args.listing_cap_min} min for App Store Connect to list "
          f"{len(pending)} uploaded build(s)", flush=True)
    t_wait = time.time()
    while pending and time.time() - t_wait < cap:
        pairs = [x for v in pending.values() for x in (v["bundle_id"], v["build_number"])]
        chk = subprocess.run(["bundle", "exec", "ruby", "check_build.rb", *pairs],
                             cwd=HERE, env=env, capture_output=True, text=True)
        listed = {}
        for line in chk.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[0] == "PRESENT":
                listed[parts[1]] = line.strip()
        for repo, v in list(pending.items()):
            if v["bundle_id"] not in listed:
                continue
            v.update(status="uploaded", listed=listed[v["bundle_id"]],
                     listed_after_s=round(time.time() - t_wait),
                     at=datetime.datetime.now().isoformat(timespec="seconds"))
            with open(v["log"], "a") as fh:
                fh.write(f"\n[run_batch] UPLOADED (listed by App Store Connect): {listed[v['bundle_id']]}\n")
            del pending[repo]
            json.dump(results, open(RESULTS, "w"), indent=1)
            print(f"    {repo}: listed — {listed[v['bundle_id']]}", flush=True)
            if not args.no_distribute:
                d = subprocess.run(["bundle", "exec", "ruby", "distribute.rb", "--app", repo, *(["--no-submit"] if args.no_beta_review else [])],
                                   cwd=HERE, env=env, capture_output=True, text=True, timeout=1800)
                print("    " + (d.stdout.strip().splitlines() or ["distribute produced no output"])[-1], flush=True)
        if pending:
            time.sleep(60)
    for repo, v in pending.items():
        v.update(status="failed",
                 error=(f"upload sent, but App Store Connect did not list build {v['build_number']} "
                        f"within {args.listing_cap_min} min — Apple may have rejected it in "
                        "processing (check the account email), or it is still processing"),
                 at=datetime.datetime.now().isoformat(timespec="seconds"))
        print(f"    {repo}: NOT listed after {args.listing_cap_min} min (build {v['build_number']})", flush=True)
    json.dump(results, open(RESULTS, "w"), indent=1)

ok = [r for r, v in results.items() if v["status"] == "uploaded"]
bad = [r for r, v in results.items() if v["status"] not in ("uploaded", "no_ipa")]
none = [r for r, v in results.items() if v["status"] == "no_ipa"]
print(f"\nuploaded: {len(ok)}  failed: {len(bad)}  no prebuilt IPA: {len(none)}  -> {RESULTS}")
sys.exit(1 if bad else 0)
