#!/usr/bin/env python3
"""Build every app for the simulators and install it on an iPhone simulator and
an Android emulator — one command for the whole org, or for any subset.

    python3 scripts/sim_install.py CalcMaster            # one app, both platforms
    python3 scripts/sim_install.py CalcMaster BodyQuest  # several
    python3 scripts/sim_install.py --all                 # all 43 (hours)
    python3 scripts/sim_install.py --all --android       # one platform only
    python3 scripts/sim_install.py CalcMaster --skip-build   # reinstall what is built
    python3 scripts/sim_install.py --list                # app names and project dirs

Debug builds, because a release build cannot run on the iOS simulator. Each app
is built, installed, launched, and checked to still be running a few seconds
later; a screenshot of that moment goes next to the log. The run report is
<DIST>/sim-install/<timestamp>.json and every step's output is in
<DIST>/sim-install/logs/.

What this has to get right, each learnt the hard way elsewhere in this repo:

  * the Android flavour has to be named. `flutter build apk --debug` on a
    flavoured project picks the first flavour, usually `dev`, whose
    applicationIdSuffix is missing from google-services.json, so the build
    dies in process<Flavour>DebugGoogleServices. The production flavour is
    chosen the same way build_release.py chooses it;
  * Gradle on this Mac needs JAVA_TOOL_OPTIONS (IPv4 + proxy) — taken from
    build_release.java_tool_options() rather than restated;
  * ANDROID_HOME in the login shell can point at an SDK without adb or the
    emulator, so the SDK is resolved to one that actually has them;
  * the package and bundle id are read from the built artefact, not assumed
    from apps.json, so a flavour's applicationIdSuffix cannot launch the wrong
    (or no) app.

Another session may already be driving an emulator. Pass --android-serial to
pin one, otherwise the first running emulator is used, and one is booted from
an AVD (--avd, else the first phone-sized Pixel) only if none is running.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import pathlib
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import DIST, MANIFEST, app_dir, flutter_bin  # noqa: E402
from build_release import flavours, java_tool_options, pick_flavour  # noqa: E402

FLUTTER = str(flutter_bin())
OUT = DIST / "sim-install"
LOGS = OUT / "logs"            # main() narrows this to logs/<run stamp>/
LOCKS = OUT / "locks"          # one flock per app, held while it is processed


# ---------------------------------------------------------------- utilities

def run(cmd, log: pathlib.Path | None = None, cwd=None, env=None, timeout=1800):
    """Run a command, append its output to `log`, never raise.

    On timeout the whole process group is killed, not just the direct child:
    `xcrun simctl install` timing out left the real `simctl` running against a
    frozen simulator long after the run had moved on."""
    try:
        p = subprocess.Popen([str(c) for c in cmd], cwd=cwd, env=env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    except OSError as e:
        rc, out = 127, str(e)
    else:
        try:
            so, se = p.communicate(timeout=timeout)
            rc, out = p.returncode, (so or "") + (se or "")
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            so, se = p.communicate()
            rc, out = 124, f"TIMEOUT after {timeout}s\n{so or ''}{se or ''}"
    if log:
        with log.open("a") as f:
            f.write(f"$ {' '.join(map(str, cmd))}\n{out}\n[exit {rc}]\n\n")
    return rc, out


def tail(text: str, n: int = 6) -> str:
    """The line(s) that say what broke. Gradle ends every failure with the same
    "Run with --stacktrace ... BUILD FAILED" footer, so the last lines of its
    output never contain the cause; the cause is the "What went wrong" block."""
    lines = [l for l in text.strip().splitlines() if l.strip()]
    for i, l in enumerate(lines):
        if "What went wrong" in l:
            cause = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("* "):
                    break
                cause.append(nxt.strip())
            return " | ".join(cause[:n])[-600:]
    # adb reports install failures as a Java stack; the "at ..." frames are
    # noise, the Failure/Exception line is the reason.
    errors = [l.strip() for l in lines if not l.lstrip().startswith("at ")
              and re.search(r"Error \(Xcode\)|^Error:|error:|No space left|"
                            r"Failure \[|Exception:", l)]
    if errors:
        return " | ".join(list(dict.fromkeys(errors))[:n])[-600:]
    return " | ".join(lines[-n:])[-600:]


def free_gb() -> float:
    try:
        return shutil.disk_usage(str(DIST.parent)).free / 2**30
    except OSError:
        return float("inf")


def busy_by_other(d: pathlib.Path) -> list[str]:
    """Other processes working inside this app's directory right now.

    screenshots.py and build_release.py walk the same apps, from other
    sessions, in the same build/ trees. Two Flutter builds in one directory
    corrupt each other, and --clean-after deleting a tree mid-build fails the
    other one. Our own builds are synchronous, so at the moment this is called
    nothing of ours is running there."""
    _, out = run(["lsof", "-d", "cwd", "-F", "pcn"], timeout=60)
    found, pid, cmd, me = [], "", "", str(os.getpid())
    prefix = str(d.resolve())
    for line in out.splitlines():
        tag, val = line[:1], line[1:]
        if tag == "p":
            pid = val
        elif tag == "c":
            cmd = val
        elif (tag == "n" and pid != me and cmd in BUILD_TOOLS
              and (val == prefix or val.startswith(prefix + "/"))):
            found.append(f"{cmd}[{pid}]")
    return found


# Only processes that build count. An emulator started from an app directory
# keeps it as its cwd for days — qemu-system-aarch64, netsimd and the shell that
# launched it held CalcMaster "busy" for a whole --busy-wait on 2026-10-03.
BUILD_TOOLS = {"dart", "dartvm", "flutter", "xcodebuild", "java", "pod", "ruby",
               "gradle", "swift-frontend", "clang", "ld"}


def wait_until_free(d: pathlib.Path, wait_min: int, lock) -> list[str]:
    """Take this app's lock and wait out any other build in its directory.

    Two checks, because each misses what the other sees. The lock is exact
    between sim_install runs, but other tools do not take it. The process scan
    sees every tool, but only while one is running: between a run's iOS and
    Android steps nothing builds, the directory looks free, and on 2026-10-03
    two sweeps built FashionFactory at once ("Could not delete ...caches-jvm")."""
    deadline = time.time() + wait_min * 60
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            others = busy_by_other(d)
            if not others:
                return []
            fcntl.flock(lock, fcntl.LOCK_UN)
        except BlockingIOError:
            others = ["another sim_install run"]
        if time.time() >= deadline:
            return others
        print(f"    waiting: {', '.join(others[:3])} working in {d.name}", flush=True)
        time.sleep(30)


DERIVED = pathlib.Path.home() / "Library/Developer/Xcode/DerivedData"


def clean_build(d: pathlib.Path) -> str:
    """Delete one app's own build output: its build/ tree, and the DerivedData
    folders whose WorkspacePath is inside it. Nothing shared — `*.noindex`
    under DerivedData are Xcode's caches for every project, and deleting them
    mid-sweep has failed builds before (see ios_build_janitor.sh)."""
    before = free_gb()
    shutil.rmtree(d / "build", ignore_errors=True)
    if DERIVED.is_dir():
        for p in DERIVED.iterdir():
            if p.name.endswith(".noindex") or not p.is_dir():
                continue
            try:
                ws = plistlib.loads((p / "info.plist").read_bytes()).get("WorkspacePath", "")
            except (OSError, plistlib.InvalidFileException):
                continue
            if ws.startswith(str(d) + "/"):
                shutil.rmtree(p, ignore_errors=True)
    return f"{max(free_gb() - before, 0):.1f} GB"


def load_apps() -> list[dict]:
    apps = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    return [a for a in apps if a.get("flutter")]


# ---------------------------------------------------------------- Android

def android_sdk() -> pathlib.Path:
    """An SDK that really has adb and the emulator in it."""
    candidates = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
                  str(pathlib.Path.home() / "Library/Android/sdk")]
    for c in candidates:
        if c and (pathlib.Path(c) / "platform-tools/adb").exists():
            return pathlib.Path(c)
    return pathlib.Path.home() / "Library/Android/sdk"


SDK = android_sdk()
ADB = SDK / "platform-tools/adb"
EMULATOR = SDK / "emulator/emulator"


# serial -> packages sim_install has installed there, oldest first — the only
# ones it may uninstall to make room. Kept on disk across runs: a per-run list
# could never evict the apps an earlier run left behind, so a fresh run on a
# full emulator failed every install (2026-10-04, daily-pulse et al.).
LEDGER = OUT / "installed.json"


def ledger_load() -> dict[str, list[str]]:
    try:
        return json.loads(LEDGER.read_text())
    except (OSError, ValueError):
        return {}


def ledger_update(serial: str, add: str | None = None, remove: str | None = None) -> list[str]:
    """Re-read, change, write: other runs may have updated it meanwhile."""
    data = ledger_load()
    pkgs = data.setdefault(serial, [])
    for p in (remove, add):
        if p and p in pkgs:
            pkgs.remove(p)
    if add:
        pkgs.append(add)
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(json.dumps(data, indent=1))
    except OSError:
        pass
    return pkgs


def adb(*args, serial=None, timeout=120):
    return run([ADB] + (["-s", serial] if serial else []) + list(args), timeout=timeout)


def running_emulators() -> list[str]:
    _, out = adb("devices")
    return [l.split()[0] for l in out.splitlines()[1:]
            if l.strip().endswith("device") and l.startswith("emulator-")]


def android_device(serial: str | None, avd: str | None, boot_timeout=300) -> str | None:
    live = running_emulators()
    if serial:
        return serial if serial in live else None
    if live and not avd:
        return live[0]
    _, out = run([EMULATOR, "-list-avds"])
    avds = out.split()
    pick = avd or next((a for a in avds if "Pixel" in a and "Tablet" not in a),
                       avds[0] if avds else None)
    if not pick or pick not in avds:
        return None
    print(f"  booting Android AVD {pick} ...", flush=True)
    subprocess.Popen([str(EMULATOR), "-avd", pick, "-no-snapshot-save", "-no-boot-anim"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + boot_timeout
    while time.time() < deadline:
        for s in set(running_emulators()) - set(live):
            if adb("shell", "getprop", "sys.boot_completed", serial=s)[1].strip() == "1":
                return s
        time.sleep(5)
    return None


def aapt() -> pathlib.Path | None:
    tools = sorted((SDK / "build-tools").glob("*/aapt"), key=lambda p: p.parent.name)
    return tools[-1] if tools else None


def apk_package(apk: pathlib.Path, fallback: str) -> str:
    tool = aapt()
    if tool:
        rc, out = run([tool, "dump", "badging", apk], timeout=120)
        m = re.search(r"package: name='([^']+)'", out)
        if rc == 0 and m:
            return m.group(1)
    return fallback


def android(app: dict, d: pathlib.Path, serial: str, args, log: pathlib.Path) -> dict:
    rec: dict = {"platform": "android", "device": serial}
    flavour = pick_flavour(flavours(d))
    rec["flavour"] = flavour
    if not args.skip_build:
        env = dict(os.environ, JAVA_TOOL_OPTIONS=java_tool_options(),
                   ANDROID_HOME=str(SDK), ANDROID_SDK_ROOT=str(SDK))
        mode = "debug"
        cmd = [FLUTTER, "build", "apk", "--debug"] + (["--flavor", flavour] if flavour else [])
        rc, out = run(cmd, log, cwd=d, env=env, timeout=args.timeout)
        # Naming the flavour is not enough. The *debug build type* also
        # appends applicationIdSuffix ".debug", and google-services.json
        # lists only the unsuffixed package, so the build dies in
        # process<Flavour>DebugGoogleServices with "No matching client found
        # for package name '...dailypulse.debug'". Profile has no suffix and
        # is closer to what ships. Same fallback as screenshots.py.
        if rc != 0 and "No matching client found" in out:
            mode = "profile"
            cmd = [FLUTTER, "build", "apk", "--profile"] + (["--flavor", flavour] if flavour else [])
            rc, out = run(cmd, log, cwd=d, env=env, timeout=args.timeout)
        if rc != 0:
            return {**rec, "status": "build_failed", "detail": tail(out)}
        rec["build_mode"] = mode
    mode = rec.get("build_mode", "debug")
    name = f"app-{flavour}-{mode}.apk" if flavour else f"app-{mode}.apk"
    apk = d / "build/app/outputs/flutter-apk" / name
    if not apk.exists():
        return {**rec, "status": "no_artifact", "detail": f"missing {apk.relative_to(d)}"}
    pkg = apk_package(apk, app.get("application_id", ""))
    rec.update(artifact=str(apk), package=pkg)
    install = [ADB, "-s", serial, "install", "-r", "-t", apk]
    rc, out = run(install, log, timeout=600)
    if "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in out:
        # A copy signed with another key (a release build, or another machine's
        # debug key) is already there, and Android will not update across keys.
        # This is a test emulator: drop the old copy and its data, then retry.
        run([ADB, "-s", serial, "uninstall", pkg], log, timeout=120)
        rc, out = run(install, log, timeout=600)
        rec["replaced_differently_signed_install"] = True
    # A debug APK is 150-200 MB and the default /data partition is ~6 GB, so a
    # sweep fills the emulator after about fifteen apps (INSUFFICIENT_STORAGE,
    # or "Requested internal only, but not enough space"). Make room by
    # removing what sim_install installed, oldest first — never anything it
    # did not put there.
    while "INSUFFICIENT_STORAGE" in out or "not enough space" in out:
        old = next((p for p in ledger_load().get(serial, []) if p != pkg), None)
        if not old:
            break
        run([ADB, "-s", serial, "uninstall", old], log, timeout=120)
        ledger_update(serial, remove=old)
        rec.setdefault("evicted_to_make_room", []).append(old)
        rc, out = run(install, log, timeout=600)
    if rc != 0 or "Success" not in out:
        return {**rec, "status": "install_failed", "detail": tail(out)}
    ledger_update(serial, add=pkg)
    if args.no_launch:
        return {**rec, "status": "installed"}
    # Not `monkey -p <pkg> 1`: on these emulator images it aborts with
    # "SYS_KEYS has no physical keys" (exit 251) before starting anything.
    _, act = run([ADB, "-s", serial, "shell", "cmd", "package", "resolve-activity",
                  "--brief", "-c", "android.intent.category.LAUNCHER", pkg], log, timeout=60)
    component = next((l.strip() for l in reversed(act.splitlines())
                      if l.strip().startswith(pkg + "/")), f"{pkg}/.MainActivity")
    rc, out = run([ADB, "-s", serial, "shell", "am", "start", "-W", "-n", component],
                  log, timeout=120)
    if rc != 0 or "Error" in out:
        return {**rec, "status": "launch_failed", "detail": tail(out)}
    time.sleep(args.settle)
    _, pid = adb("shell", "pidof", pkg, serial=serial)
    shot = LOGS / f"{app['repo']}-android.png"
    try:
        png = subprocess.run([str(ADB), "-s", serial, "exec-out", "screencap", "-p"],
                             capture_output=True, timeout=60).stdout
        if png:
            shot.write_bytes(png)
    except (subprocess.TimeoutExpired, OSError):
        pass
    if not pid.strip():
        return {**rec, "status": "launch_failed",
                "detail": "process not running after launch — see logcat"}
    return {**rec, "status": "running", "pid": pid.strip(),
            "screenshot": str(shot) if shot.exists() else None}


# ---------------------------------------------------------------- iOS

def ios_devices() -> list[dict]:
    _, out = run(["xcrun", "simctl", "list", "devices", "available", "-j"], timeout=60)
    try:
        data = json.loads(out)["devices"]
    except (ValueError, KeyError):
        return []
    return [{**d, "runtime": rt} for rt, ds in data.items() if "iOS" in rt for d in ds]


def ios_device(want: str | None, family: str = "iPhone") -> str | None:
    """A simulator of the given family, preferring the iOS release App Review
    uses. Nine apps were rejected for crashing on launch on "iPhone 17 Pro
    Max, iOS 27.0", and Apple adds that apps "downloaded onto iPad devices
    should function as expected for iPad users" — so both are tested."""
    devs = ios_devices()
    if want:
        match = [d for d in devs if want in (d["udid"], d["name"])]
    else:
        fam = [d for d in devs if d["name"].startswith(family)]
        # Newest runtime *that has a device of this family* — the first
        # version took the newest runtime overall, found no iPad on it, and
        # fell back to an iPad on iOS 26.5.
        newest = sorted({d["runtime"] for d in fam},
                        key=lambda r: [int(x) for x in re.findall(r"\d+", r)])
        top = [d for d in fam if newest and d["runtime"] == newest[-1]] or fam
        booted = [d for d in top if d["state"] == "Booted"]
        match = booted or top[-1:]
    if not match:
        return None
    dev = match[0]
    if dev["state"] != "Booted":
        print(f"  booting iOS simulator {dev['name']} ...", flush=True)
        run(["xcrun", "simctl", "boot", dev["udid"]], timeout=180)
    run(["xcrun", "simctl", "bootstatus", dev["udid"], "-b"], timeout=300)
    return dev["udid"]


def ios_flavour(d: pathlib.Path, android_flavour: str | None) -> str | None:
    """Only pass --flavor to iOS when Runner has a scheme of that name; most of
    these apps flavour Android alone, and a missing scheme fails the build."""
    if not android_flavour:
        return None
    schemes = d / "ios/Runner.xcodeproj/xcshareddata/xcschemes"
    return android_flavour if (schemes / f"{android_flavour}.xcscheme").exists() else None


SIM_DEAD: set[str] = set()


def ios_responsive(udid: str) -> bool:
    """A frozen simulator still shows as Booted, but every simctl call against
    it hangs — install for its full 300 s timeout, app after app. On
    2026-10-03 swap ran out and every simulator on the machine froze at once.
    A cheap probe first; once a device fails it, skip it for the rest of the
    run instead of paying a timeout per app."""
    if udid in SIM_DEAD:
        return False
    rc, _ = run(["xcrun", "simctl", "spawn", udid, "launchctl", "list"], timeout=30)
    if rc != 0:
        SIM_DEAD.add(udid)
    return rc == 0


def ios(app: dict, d: pathlib.Path, udid: str, args, log: pathlib.Path,
        tag: str = "ios") -> dict:
    rec: dict = {"platform": tag, "device": udid}
    if not ios_responsive(udid):
        return {**rec, "status": "simulator_unresponsive",
                "detail": f"{udid} does not answer simctl (frozen?) — iOS skipped for this run"}
    flavour = ios_flavour(d, pick_flavour(flavours(d)))
    rec["flavour"] = flavour
    if not args.skip_build:
        cmd = [FLUTTER, "build", "ios", "--simulator", "--debug"] + \
              (["--flavor", flavour] if flavour else [])
        rc, out = run(cmd, log, cwd=d, timeout=args.timeout)
        if rc != 0:
            return {**rec, "status": "build_failed", "detail": tail(out)}
    built = sorted((d / "build/ios/iphonesimulator").glob("*.app"),
                   key=lambda p: p.stat().st_mtime)
    if not built:
        return {**rec, "status": "no_artifact", "detail": "no .app in build/ios/iphonesimulator"}
    bundle_app = built[-1]
    try:
        bundle = plistlib.loads((bundle_app / "Info.plist").read_bytes())["CFBundleIdentifier"]
    except (OSError, KeyError, plistlib.InvalidFileException):
        bundle = app.get("bundle_id", "")
    rec.update(artifact=str(bundle_app), bundle_id=bundle)
    rc, out = run(["xcrun", "simctl", "install", udid, bundle_app], log, timeout=300)
    if rc != 0:
        return {**rec, "status": "install_failed", "detail": tail(out)}
    if args.no_launch:
        return {**rec, "status": "installed"}
    run(["xcrun", "simctl", "terminate", udid, bundle], log, timeout=30)
    # Pre-grant every privacy permission so no system prompt is left open.
    # One unanswered "Allow Radio Tune to use your location?" sat over the
    # home screen and made the next three apps' launches time out: each one
    # started, but could not come to the foreground. It would also have put a
    # permission dialog into any screenshot taken afterwards.
    run(["xcrun", "simctl", "privacy", udid, "grant", "all", bundle], log, timeout=30)
    rc, out = run(["xcrun", "simctl", "launch", udid, bundle], log, timeout=90)
    if rc != 0:
        return {**rec, "status": "launch_failed", "detail": tail(out)}
    time.sleep(args.settle)
    _, procs = run(["xcrun", "simctl", "spawn", udid, "launchctl", "list"], timeout=60)
    shot = LOGS / f"{app['repo']}-{tag}.png"
    run(["xcrun", "simctl", "io", udid, "screenshot", shot], timeout=60)
    if f"UIKitApplication:{bundle}" not in procs:
        return {**rec, "status": "launch_failed",
                "detail": "launched, but not running a few seconds later (crashed?)"}
    return {**rec, "status": "running", "screenshot": str(shot) if shot.exists() else None}


# ---------------------------------------------------------------- main

def purge_derived_data(max_age_min=5):
    """Remove Runner-*/Pods-* trees Xcode left for apps already finished.
    Same rule as screenshots.py, which learnt it when 43 apps filled the disk."""
    dd = pathlib.Path.home() / "Library/Developer/Xcode/DerivedData"
    if not dd.is_dir():
        return 0
    now, gone = time.time(), 0
    for d in dd.glob("*"):
        try:
            if (d.name.startswith(("Runner-", "Pods-")) and d.is_dir()
                    and now - d.stat().st_mtime > max_age_min * 60):
                shutil.rmtree(d, ignore_errors=True)
                gone += 1
        except OSError:
            pass
    return gone


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("apps", nargs="*", help="repo names from apps.json (case-insensitive)")
    ap.add_argument("--all", action="store_true", help="every Flutter app in apps.json")
    ap.add_argument("--list", action="store_true", help="list the apps and exit")
    ap.add_argument("--ios", action="store_true", help="iOS only")
    ap.add_argument("--android", action="store_true", help="Android only")
    ap.add_argument("--ios-device", help="simulator UDID or name (default: a booted iPhone)")
    ap.add_argument("--ipad", action="store_true",
                    help="also install and launch the iOS build on an iPad simulator")
    ap.add_argument("--ipad-device", help="iPad simulator UDID or name (default: newest iOS)")
    ap.add_argument("--android-serial", help="emulator serial, e.g. emulator-5560")
    ap.add_argument("--avd", help="AVD to boot when no emulator is running")
    ap.add_argument("--skip-build", action="store_true",
                    help="install what is already built instead of building")
    ap.add_argument("--no-launch", action="store_true", help="install only")
    ap.add_argument("--settle", type=int, default=8,
                    help="seconds to wait after launch before checking it is alive")
    ap.add_argument("--timeout", type=int, default=2400, help="per-build timeout, seconds")
    ap.add_argument("--min-free-gb", type=int, default=10,
                    help="stop before an app when the disk has less free than this")
    ap.add_argument("--clean-after", action="store_true",
                    help="delete each app's build/ and its DerivedData once installed "
                         "(keeps an --all sweep from filling the disk)")
    ap.add_argument("--busy-wait", type=int, default=20,
                    help="minutes to wait for another process building in an app's "
                         "directory before skipping it")
    args = ap.parse_args()

    apps = load_apps()
    if args.list:
        for a in apps:
            print(f"{a['repo']:<22} {app_dir(a)}")
        return 0
    if args.all:
        chosen = apps
    elif args.apps:
        by_name = {a["repo"].lower(): a for a in apps}
        unknown = [n for n in args.apps if n.lower() not in by_name]
        if unknown:
            print(f"unknown app(s): {', '.join(unknown)} — see --list", file=sys.stderr)
            return 2
        chosen = [by_name[n.lower()] for n in args.apps]
    else:
        ap.error("name one or more apps, or pass --all")
    do_ios = args.ios or not args.android
    do_android = args.android or not args.ios

    udid = serial = None
    if do_ios:
        udid = ios_device(args.ios_device)
        if not udid:
            print("no iOS simulator available — check `xcrun simctl list devices`", file=sys.stderr)
            return 1
        print(f"iOS simulator: {udid}")
    ipad = None
    if do_ios and args.ipad:
        ipad = ios_device(args.ipad_device, family="iPad")
        print(f"iPad simulator: {ipad}")
    if do_android:
        serial = android_device(args.android_serial, args.avd)
        if not serial:
            print("no Android emulator running and none could be booted "
                  f"(sdk: {SDK})", file=sys.stderr)
            return 1
        print(f"Android emulator: {serial}")

    # One log directory per run: two runs at once used to overwrite each
    # other's <repo>-<platform>.log, so a failure was reported against
    # another run's output.
    global LOGS
    stamp = time.strftime("%Y%m%d-%H%M%S")
    LOGS = OUT / "logs" / stamp
    LOGS.mkdir(parents=True, exist_ok=True)
    LOCKS.mkdir(parents=True, exist_ok=True)
    results = []
    if args.all and not args.clean_after:
        print("note: --all without --clean-after keeps every app's build output "
              "(~0.5-1.5 GB each)", flush=True)
    for i, app in enumerate(chosen, 1):
        d = app_dir(app)
        print(f"[{i}/{len(chosen)}] {app['repo']}  ({d})", flush=True)
        free = free_gb()
        if free < args.min_free_gb:
            # Building into a full disk does not just fail this app: it fails
            # every later one, and anything else on the machine writing at the
            # time. A run on 2026-10-03 went on building at 3.5 GB free and
            # left 131 MB.
            for rest in chosen[i - 1:]:
                results.append({"repo": rest["repo"], "platform": "-", "status": "disk_full",
                                "detail": f"{free:.1f} GB free < --min-free-gb {args.min_free_gb}"})
            print(f"    stopping: {free:.1f} GB free, below --min-free-gb "
                  f"{args.min_free_gb}. Free some space, or lower it.", flush=True)
            break
        if not (d / "pubspec.yaml").exists():
            results.append({"repo": app["repo"], "platform": "-", "status": "missing_project",
                            "detail": f"no pubspec.yaml at {d}"})
            print("    - missing project", flush=True)
            continue
        lock = (LOCKS / f"{app['repo']}.lock").open("w")
        others = [] if args.skip_build else wait_until_free(d, args.busy_wait, lock)
        if others:
            lock.close()
            results.append({"repo": app["repo"], "platform": "-", "status": "busy",
                            "detail": f"still in use by {', '.join(others[:3])}"})
            print(f"    - busy: {', '.join(others[:3])}", flush=True)
            continue
        plats = app.get("platforms", {})
        for name, wanted, fn, dev in (("ios", do_ios, ios, udid),
                                      ("android", do_android, android, serial)):
            if not wanted:
                continue
            if plats and not plats.get(name, True):
                results.append({"repo": app["repo"], "platform": name, "status": "skipped",
                                "detail": "platform disabled in apps.json"})
                continue
            log = LOGS / f"{app['repo']}-{name}.log"
            log.write_text(f"# {app['repo']} {name} {stamp}\n\n")
            t0 = time.time()
            rec = fn(app, d, dev, args, log)
            rec.update(repo=app["repo"], seconds=round(time.time() - t0), log=str(log))
            results.append(rec)
            mark = "ok " if rec["status"] in ("running", "installed") else "ERR"
            print(f"    {mark} {name:<7} {rec['status']}"
                  + (f" — {rec['detail']}" if rec.get("detail") else ""), flush=True)
            # The same simulator build, on an iPad: no second compile.
            if name == "ios" and ipad and rec["status"] in ("running", "installed"):
                t0 = time.time()
                prev_skip = args.skip_build
                args.skip_build = True
                prec = ios(app, d, ipad, args, log, tag="ipad")
                args.skip_build = prev_skip
                prec.update(repo=app["repo"], seconds=round(time.time() - t0), log=str(log))
                results.append(prec)
                mark = "ok " if prec["status"] in ("running", "installed") else "ERR"
                print(f"    {mark} ipad    {prec['status']}"
                      + (f" — {prec['detail']}" if prec.get("detail") else ""), flush=True)
        if args.clean_after:
            others = busy_by_other(d)
            print(f"    not cleaned: in use by {', '.join(others[:3])}" if others
                  else f"    cleaned {clean_build(d)}", flush=True)
            # clean_build only removes the Flutter build directory. Xcode keeps
            # several GB per app in DerivedData, which this did not touch: over
            # three apps it grew 5 GB -> 12 GB, so a --all run would have
            # exhausted the disk around app 27 — exactly what happened on
            # 2026-09-14. Trees untouched for minutes belong to finished apps.
            freed = purge_derived_data()
            if freed:
                print(f"    purged {freed} DerivedData tree(s)", flush=True)
        lock.close()   # releases the flock

    report = OUT / f"{stamp}.json"
    try:
        report.write_text(json.dumps({"ios_device": udid, "android_device": serial,
                                      "results": results}, indent=1))
    except OSError as e:
        # Losing the summary as well as the builds hid what had happened.
        report = f"(not written: {e})"
    good = [r for r in results if r["status"] in ("running", "installed")]
    bad = [r for r in results if r["status"] not in ("running", "installed", "skipped")]
    print(f"\n{len(good)} ok, {len(bad)} failed, "
          f"{len(results) - len(good) - len(bad)} skipped — report: {report}")
    for r in bad:
        print(f"  {r['repo']:<22} {r['platform']:<7} {r['status']}: {r.get('detail', '')}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
