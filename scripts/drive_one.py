#!/usr/bin/env python3
"""Run one app's store-screenshot script on one simulator, for iterating on it.

    python3 scripts/drive_one.py <repo> --udid <simulator udid>

Uninstalls the app (first-launch state), runs
`flutter drive --target=integration_test/store_screenshots_test.dart` with
SCREENSHOT=true and the QA account as QA_EMAIL/QA_PASSWORD dart-defines, and
prints where the frames and the log went. The QA credentials are read here at
run time (supabase_accounts.accounts()) and masked in the log, so whoever runs
this — a person or an agent — never sees them.

Frames: <app dir>/store_screenshots/*.png   Log: <DIST>/drive-logs/<repo>-<udid>.log
Exit code is flutter drive's.

screenshots.py --drive is the production capture; this is the same run for one
app and one device, used while fixing a script.
"""
import json, os, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from agl_paths import MANIFEST, ROOT, DIST, flutter_bin  # noqa: E402

import argparse
ap = argparse.ArgumentParser(usage=__doc__)
ap.add_argument("repo")
ap.add_argument("--udid", required=True)
opts = ap.parse_args()
repo, udid = opts.repo, opts.udid
app = next(a for a in json.load(open(MANIFEST / "apps.json"))["apps"] if a["repo"] == repo)
app_dir = ROOT / repo / (app["dir"] if app["dir"] != "." else "")

try:
    from supabase_accounts import accounts
    acct = next(((e, p) for role, e, p in accounts() if e.lower().startswith("qa@")), None)
except BaseException:
    acct = None

defines = ["--dart-define=SCREENSHOT=true"]
if acct:
    defines += [f"--dart-define=QA_EMAIL={acct[0]}", f"--dart-define=QA_PASSWORD={acct[1]}"]

env = dict(os.environ, PATH=f"{pathlib.Path.home()}/.rbenv/shims:/opt/homebrew/bin:" + os.environ["PATH"])
subprocess.run(["xcrun", "simctl", "boot", udid], capture_output=True)
subprocess.run(["xcrun", "simctl", "bootstatus", udid, "-b"], capture_output=True, timeout=600)
subprocess.run(["xcrun", "simctl", "uninstall", udid, app["bundle_id"]], capture_output=True)
from sim_permissions import services_for, prepare  # noqa: E402
note = prepare(udid, app["bundle_id"], app_dir, services_for(app_dir), str(flutter_bin()), defines, env)
print("permissions:", note.replace(acct[1], "***") if acct else note)
raw = app_dir / "store_screenshots"
for f in raw.glob("*.png") if raw.is_dir() else []:
    f.unlink()
try:
    r = subprocess.run([str(flutter_bin()), "drive", "--driver=test_driver/integration_test.dart",
                        "--target=integration_test/store_screenshots_test.dart", *defines, "-d", udid],
                       cwd=app_dir, env=env, capture_output=True, text=True, timeout=2400)
    log, rc = r.stdout + r.stderr, r.returncode
except subprocess.TimeoutExpired as ex:
    out = ex.stdout.decode(errors="replace") if isinstance(ex.stdout, bytes) else (ex.stdout or "")
    log, rc = f"timed out after {ex.timeout}s\n{out}", 124
if acct:
    log = log.replace(acct[1], "***").replace(acct[0], "<qa>")
log = re.sub(r"QA_PASSWORD=\S+", "QA_PASSWORD=***", log)
out = DIST / "drive-logs"; out.mkdir(parents=True, exist_ok=True)
lp = out / f"{repo}-{udid}.log"; lp.write_text(log)
frames = sorted(raw.glob("*.png")) if raw.is_dir() else []
print(f"exit={rc} frames={len(frames)} -> {raw}\nlog -> {lp}")
for f in frames:
    print("  ", f.name)
sys.exit(rc)
