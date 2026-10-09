#!/usr/bin/env python3
"""Capture store screenshots on the iOS simulator for every app.

Per app: temporarily hide Flutter's debug banner (the simulator cannot run a
release build), build for the simulator, install on an iPhone 17 Pro Max
(1320x2868, App Store "6.9-inch") and an iPad Pro 13-inch (2064x2752), launch,
dismiss a first-run/permission sheet if one is showing, screenshot the home
screen, then tap each bottom-navigation tab found in the accessibility tree
(Flutter labels them "Tab n of m") and screenshot again. Writes:

  <app>/fastlane/screenshots/en-US/{iphone69,ipadpro13}-NN.png          (deliver)
  <app>/fastlane/metadata/android/en-US/images/phoneScreenshots/NN.png  (supply, padded to 1440x2880 = 2:1)
  <app>/fastlane/metadata/android/en-US/images/tenInchScreenshots/NN.png

    python3 scripts/screenshots.py CalcMaster
    python3 scripts/screenshots.py --all
    python3 scripts/screenshots.py --all --skip-done

Requires idb (~/.idb-venv) with the Homebrew idb_companion first on PATH.
"""
import hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST, flutter_bin, flutter_sdk  # noqa: E402
FLUTTER = str(flutter_bin())
DEVICES = {"iphone69": "3A41E921-1471-466E-BCDA-30E428297CCF", "ipadpro13": "3C6104B3-00B8-4468-A26B-06E7AF142E97"}
ENV = dict(os.environ, PATH=f"/opt/homebrew/bin:{pathlib.Path.home()}/.idb-venv/bin:{flutter_sdk()}/bin:" + os.environ["PATH"])
DISMISS = ["Allow Full Access", "Allow While Using App", "Allow Once", "Allow", "OK", "Continue", "Get Started", "Get started", "Skip", "Not now", "Not Now", "Maybe later", "Accept", "Agree", "I agree", "Done", "Next", "Don\u2019t Allow", "Don't Allow"]
MAX_SCREENS = 5
RESULTS = ROOT / ".dist/screenshots-results.json"

def sh(*cmd, cwd=None, timeout=1800, check=False):
    return subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, timeout=timeout)

def describe(udid):
    r = sh("idb", "ui", "describe-all", "--udid", udid, timeout=60)
    try: return json.loads(r.stdout)
    except Exception: return []

def boot(udid):
    """simctl io times out against a shut-down device, so make sure it is up.
    Booting an already-booted device is a no-op error we can ignore."""
    state = sh("xcrun", "simctl", "list", "devices", "-j", timeout=60).stdout
    if f'"udid" : "{udid}"' in state and '"state" : "Booted"' in state:
        import json as _j
        for runtime in _j.loads(state)["devices"].values():
            for d in runtime:
                if d["udid"] == udid and d["state"] == "Booted":
                    return
    sh("xcrun", "simctl", "boot", udid, timeout=180)
    sh("xcrun", "simctl", "bootstatus", udid, "-b", timeout=300)

def tap(udid, x, y): sh("idb", "ui", "tap", str(int(x)), str(int(y)), "--udid", udid, timeout=30)

def center(e): f = e["frame"]; return f["x"] + f["width"] / 2, f["y"] + f["height"] / 2

def shot(udid, path): sh("xcrun", "simctl", "io", udid, "screenshot", str(path), timeout=60); return path.exists()

def swipe(udid, x1, y1, x2, y2, duration=0.4):
    sh("idb", "ui", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)),
       "--duration", str(duration), "--udid", udid, timeout=30)

def same_image(a, b):
    """A scroll that moved nothing must not become a second screenshot.

    Compares the image *below the status bar*. Hashing whole files let two
    captures of the identical screen count as different because the clock had
    ticked from 11:55 to 12:10 — which is exactly how Kinnav shipped two
    copies of its login screen to Play as "two screenshots".
    """
    try:
        import subprocess as _sp
        digests = []
        for f in (a, b):
            # Crop the top 6%: status bar out, everything that identifies the
            # screen still in. sips is always present on macOS.
            h = int(_sp.run(["sips", "-g", "pixelHeight", str(f)], capture_output=True,
                            text=True).stdout.split()[-1])
            w = int(_sp.run(["sips", "-g", "pixelWidth", str(f)], capture_output=True,
                            text=True).stdout.split()[-1])
            tmp = tempfile.mktemp(suffix=".png")
            _sp.run(["sips", "-c", str(int(h * 0.94)), str(w), str(f), "--out", tmp],
                    capture_output=True)
            digests.append(hashlib.sha256(pathlib.Path(tmp).read_bytes()).digest())
            pathlib.Path(tmp).unlink(missing_ok=True)
        return digests[0] == digests[1]
    except Exception:
        try:
            return hashlib.sha256(pathlib.Path(a).read_bytes()).digest() == \
                   hashlib.sha256(pathlib.Path(b).read_bytes()).digest()
        except OSError:
            return True

def patch_banner(app_dir):
    """Add debugShowCheckedModeBanner:false to every MaterialApp/CupertinoApp constructor. Returns files changed."""
    if sh("git", "status", "--porcelain", "--", "lib", cwd=app_dir).stdout.strip():
        return None  # lib has local changes; do not touch
    changed = []
    for f in (app_dir / "lib").rglob("*.dart"):
        t = f.read_text(errors="replace")
        if "debugShowCheckedModeBanner" in t: continue
        n = re.sub(r"\b((?:MaterialApp|CupertinoApp|WidgetsApp)(?:\.router)?\s*\()", r"\1debugShowCheckedModeBanner: false, ", t)
        if n != t: f.write_text(n); changed.append(f)
    return changed

def unpatch(app_dir, files=None):
    """Restore only the files patch_banner changed. Resetting all of lib/
    would also discard anything another process edited during the capture."""
    if not files:
        return
    sh("git", "checkout", "--", *[str(f) for f in files], cwd=app_dir)

def clear_alerts(udid, rounds=4):
    """Tap through system permission alerts / first-run sheets, most permissive first."""
    for _ in range(rounds):
        els = describe(udid)
        btns = [e for e in els if e.get("type") == "Button" and (e.get("AXLabel") or "").strip() in DISMISS]
        if not btns: return
        btns.sort(key=lambda e: DISMISS.index((e.get("AXLabel") or "").strip()))
        tap(udid, *center(btns[0])); time.sleep(2.5)

# Getting past a sign-in wall. Measured on Kinnav 2026-10-02: the app opens on
# an onboarding carousel, then a login screen, and the capture was shooting the
# login form as the store screenshot. clear_alerts could not help — it matches
# labels exactly, and these read "Demo mode (dev) — skip to app" and
# "Use test account".
#
# Substring matched, and deliberately a short list of ways *into* an app. None
# of these creates, sends, buys or deletes anything.
BYPASS = ["demo mode", "use test account", "continue as guest", "browse as guest",
          "skip sign in", "skip for now", "continue without", "try the demo",
          "explore first", "guest mode", "try it free"]


def enter_app(udid, rounds=4):
    """Walk onboarding and a login gate until the app itself is on screen."""
    for _ in range(rounds):
        clear_alerts(udid)
        els = describe(udid)
        cand = next((e for e in els
                     if e.get("type") in ("Button", "Cell", "Link", "StaticText")
                     and any(w in (e.get("AXLabel") or "").strip().lower() for w in BYPASS)), None)
        if not cand:
            break
        tap(udid, *center(cand))
        time.sleep(6)
    clear_alerts(udid)   # whatever the app asks for once it is actually running


def _qa_account():
    """(email, password) of the QA account, read from the integration guide at
    run time by the same code supabase_accounts.py uses. Never stored here,
    never written to a log."""
    try:
        from supabase_accounts import accounts
        return next(((e, pw) for role, e, pw in accounts() if e.lower().startswith("qa@")), None)
    except BaseException:
        return None


def sign_in(udid) -> bool:
    """Sign in with the QA account when the app is on a sign-in form.

    2.3.3: "screenshots ... must show the actual app in use, and not merely
    the ... login page". Six apps were rejected for exactly that, and the
    bypass buttons the capture used to tap ("Use test account", "Demo mode
    (dev)") were removed from every app — so the honest way in is a real
    account. Only an email field, a password field and a sign-in button are
    touched; nothing is created or changed."""
    els = describe(udid)
    lab = lambda e: ((e.get("AXLabel") or "") + " " + (e.get("AXValue") or "") + " " +
                     (e.get("AXPlaceholderValue") or "")).lower()
    email = next((e for e in els if e.get("type") in ("TextField", "Other") and "email" in lab(e)), None)
    pw = next((e for e in els if e.get("type") in ("SecureTextField", "TextField", "Other")
               and "password" in lab(e) and e is not email), None)
    if not (email and pw):
        return False
    acct = _qa_account()
    if not acct:
        return False
    tap(udid, *center(email)); time.sleep(1)
    sh("idb", "ui", "text", acct[0], "--udid", udid, timeout=30)
    tap(udid, *center(pw)); time.sleep(1)
    sh("idb", "ui", "text", acct[1], "--udid", udid, timeout=30)
    time.sleep(1)
    go = next((e for e in describe(udid) if e.get("type") == "Button"
               and (e.get("AXLabel") or "").strip().lower() in
               ("sign in", "log in", "login", "sign in with email", "continue", "log in with email")), None)
    if not go:
        return False
    tap(udid, *center(go)); time.sleep(10)
    clear_alerts(udid)
    return True


def vet(shots: list, dev: str, repo: str, res: dict) -> list:
    """Keep only frames App Review would accept, judged by screenshot_audit.

    The capture used to publish whatever was on screen; App Store Connect was
    found holding a passcode prompt (MyCard), the iOS home screen
    (AGrammarly), another app's permission sheet (five apps) and "SAMPLE
    DATA" banners. Every frame is now read and a rejected one never leaves
    the staging directory."""
    if not shots:
        return shots
    try:
        import screenshot_audit as sa
        if not sa.APP_NAMES:
            for a in json.load(open(M / "apps.json"))["apps"]:
                sa.APP_NAMES[a["repo"].lower()] = a["repo"]
        text = sa.ocr(shots)
    except BaseException as e:
        res.setdefault("vet", {})[dev] = f"not vetted: {type(e).__name__}"
        return []          # unvetted frames are not published
    kept, dropped = [], []
    for f in shots:
        kind, why = sa.classify(text.get(str(f)), sa.stddev(f), repo)
        (dropped if kind in sa.BAD else kept).append((f, kind, why))
    for f, kind, why in dropped:
        pathlib.Path(f).unlink(missing_ok=True)
    out = []
    for i, (f, _, _) in enumerate(kept, start=1):
        dst = pathlib.Path(f).with_name(f"{dev}-{i:02d}.png")
        if pathlib.Path(f) != dst:
            pathlib.Path(f).replace(dst)
        out.append(dst)
    res.setdefault("vet", {})[dev] = {"kept": len(out),
                                      "dropped": [f"{pathlib.Path(f).name}: {k} ({w})" for f, k, w in dropped]}
    return out


# ---------------------------------------------------------------------------
# Android. Until now this file produced Android "screenshots" by letterboxing
# the iOS ones to 1440x2880 — so every Play listing showed an iPhone render of
# the app, padded. These capture the app actually running on the emulator.

ADB = str(pathlib.Path.home() / "Library/Android/sdk/platform-tools/adb")
EMULATOR = str(pathlib.Path.home() / "Library/Android/sdk/emulator/emulator")
LOGS = DIST / "device-logs"

# Gradle on this Mac needs both of these; see build_release.py for why. They
# are set here rather than inherited because `flutter build apk` spawns two
# JVMs and only JAVA_TOOL_OPTIONS reaches both.
def _android_env():
    import socket
    opts = ["-Djava.net.preferIPv4Stack=true"]
    try:
        with socket.create_connection(("127.0.0.1", 10054), timeout=1):
            opts += ["-Dhttp.proxyHost=127.0.0.1", "-Dhttp.proxyPort=10054",
                     "-Dhttps.proxyHost=127.0.0.1", "-Dhttps.proxyPort=10054",
                     "-Dhttp.nonProxyHosts=localhost|127.0.0.1"]
    except OSError:
        pass
    return dict(ENV, JAVA_TOOL_OPTIONS=" ".join(opts))


class _AdbResult:
    def __init__(self, rc=1, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


def adb(*args, serial=None, timeout=120, binary=False):
    """Never raises. A sluggish emulator timing out on `uninstall` once
    aborted an entire capture that had already succeeded; a failed adb call
    is a bad result, not an exception."""
    cmd = [ADB] + (["-s", serial] if serial else []) + list(args)
    try:
        return subprocess.run(cmd, capture_output=True, text=not binary, timeout=timeout)
    except subprocess.TimeoutExpired:
        return _AdbResult(out=b"" if binary else "")
    except OSError as e:
        return _AdbResult(err=str(e))


def android_device(boot_timeout=300):
    """The running emulator, started from an AVD if none is up."""
    out = adb("devices").stdout or ""
    live = [l.split()[0] for l in out.splitlines()[1:] if l.strip().endswith("device")]
    if live:
        return live[0]
    avds = subprocess.run([EMULATOR, "-list-avds"], capture_output=True, text=True).stdout.split()
    if not avds:
        return None
    pick = next((a for a in avds if "Pixel" in a and "Tablet" not in a), avds[0])
    subprocess.Popen([EMULATOR, "-avd", pick, "-no-snapshot-save", "-no-boot-anim"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + boot_timeout
    while time.time() < deadline:
        out = adb("devices").stdout or ""
        live = [l.split()[0] for l in out.splitlines()[1:] if l.strip().endswith("device")]
        if live and (adb("shell", "getprop", "sys.boot_completed", serial=live[0]).stdout or "").strip() == "1":
            return live[0]
        time.sleep(5)
    return None


def _android_flavour(app_dir):
    """`flutter build apk --debug` picks the first flavour, which is `dev` —
    and its applicationIdSuffix makes the package absent from
    google-services.json, so the build dies in processDevDebugGoogleServices:
    "No matching client found for package name ...calcmaster.dev"."""
    for g in ("android/app/build.gradle.kts", "android/app/build.gradle"):
        f = app_dir / g
        if not f.exists():
            continue
        txt = f.read_text(errors="ignore")
        if "productFlavors" not in txt:
            return None
        for name in ("prod", "production", "release", "live", "store"):
            if f'create("{name}")' in txt or f"{name} {{" in txt:
                return name
    return None


def android_capture(app, app_dir, out_android, serial):
    """Build, install, launch and photograph the app on the emulator."""
    repo, pkg = app["repo"], app.get("application_id") or app["bundle_id"]
    res = {"shots": 0, "error": "", "crashlytics": False}
    flavour = _android_flavour(app_dir)
    def _build(mode):
        cmd = [FLUTTER, "build", "apk", mode, "--dart-define=SCREENSHOT=true"]
        if flavour:
            cmd += ["--flavor", flavour]
        return subprocess.run(cmd, cwd=app_dir, env=_android_env(),
                              capture_output=True, text=True, timeout=2400)

    b = _build("--debug")
    out = (b.stdout or "") + (b.stderr or "")
    # Nine apps failed here with
    #   No matching client found for package name '...dailypulse.debug'
    # because the debug build type appends applicationIdSuffix ".debug" and
    # google-services.json only lists the unsuffixed package. Profile has no
    # suffix, and is closer to what ships anyway: kDebugMode is false, so the
    # debug banner and the dev shortcuts are gone.
    if b.returncode != 0 and "No matching client found" in out:
        b = _build("--profile")
        out = (b.stdout or "") + (b.stderr or "")
    apks = sorted((app_dir / "build/app/outputs/flutter-apk").glob("*.apk"))
    if b.returncode != 0 or not apks:
        # Keep "What went wrong", not the generic Gradle footer that a plain
        # tail gives you — that footer told us nothing for fourteen apps.
        why = re.search(r"\* What went wrong:\s*(.+?)(?:\n\s*\* Try:|\Z)", out, re.S)
        res["error"] = "build failed: " + (why.group(1).strip() if why
                                           else out.strip()[-300:])[:300]
        return res

    adb("uninstall", pkg, serial=serial, timeout=90)
    # -t: a debug APK is flagged test-only and is otherwise refused.
    ins = adb("install", "-r", "-t", str(apks[-1]), serial=serial, timeout=600)
    if "Success" not in (ins.stdout or ""):
        res["error"] = "install failed: " + (ins.stderr or ins.stdout).strip()[-200:]
        return res

    adb("logcat", "-c", serial=serial, timeout=60)
    # `monkey` reports success and leaves the launcher focused; an explicit
    # component actually starts the activity.
    adb("shell", "am", "start", "-n", f"{pkg}/.MainActivity", serial=serial, timeout=90)
    time.sleep(10)
    for _ in range(3):      # runtime permission dialogs
        ui = adb("shell", "uiautomator", "dump", "/sdcard/ui.xml", serial=serial, timeout=60)
        xml = adb("shell", "cat", "/sdcard/ui.xml", serial=serial, timeout=60).stdout or ""
        m = re.search(r'text="(Allow|While using the app|Only this time|OK|Continue|Accept)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml)
        if not m:
            break
        x = (int(m.group(2)) + int(m.group(4))) // 2
        y = (int(m.group(3)) + int(m.group(5))) // 2
        adb("shell", "input", "tap", str(x), str(y), serial=serial, timeout=60)
        time.sleep(3)

    staging = pathlib.Path(tempfile.mkdtemp(prefix=f"aglandshots-{repo}-"))
    shots = []

    def grab(n):
        raw = adb("exec-out", "screencap", "-p", serial=serial, timeout=120, binary=True).stdout
        if not raw or len(raw) < 5000:
            return None
        f = staging / f"{n:02d}.png"
        f.write_bytes(raw)
        return f

    first = grab(1)
    if first:
        shots.append(first)
        # Bottom navigation: tap along the lowest row of clickable nodes.
        xml = ""
        if adb("shell", "uiautomator", "dump", "/sdcard/ui.xml", serial=serial, timeout=60).returncode == 0:
            xml = adb("shell", "cat", "/sdcard/ui.xml", serial=serial, timeout=60).stdout or ""
        # Not filtered on clickable="true". Flutter's semantics nodes are not
        # marked clickable, so that filter found zero nodes on CalcMaster —
        # whose bottom bar is plainly five labelled nodes at y 2174..2316.
        # Labelled nodes sharing the lowest y-band are the tab bar.
        nodes = []
        for m in re.finditer(r"<node[^>]*>", xml):
            s = m.group(0)
            b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
            # Whichever is non-empty, not whichever matches first. Every node
            # carries text="" as well as content-desc, so `text or
            # content-desc` short-circuits on the empty text match and the
            # real label is never read — which found 0 labelled nodes on a
            # screen with fourteen of them.
            txt = re.search(r'text="([^"]*)"', s)
            desc = re.search(r'content-desc="([^"]*)"', s)
            label = next((v.group(1).strip() for v in (txt, desc)
                          if v and v.group(1).strip()), "")
            if b and label:
                nodes.append(tuple(int(g) for g in b.groups()))
        h = max((d for _, _, _, d in nodes), default=2400)
        bar = [n for n in nodes if n[1] > 0.85 * h]
        if len(bar) < 2:
            bar = []
        for i, n in enumerate(sorted(bar, key=lambda z: z[0])[1:MAX_SCREENS], start=2):
            adb("shell", "input", "tap", str((n[0] + n[2]) // 2), str((n[1] + n[3]) // 2),
                serial=serial, timeout=60)
            time.sleep(3)
            f = grab(i)
            if f and not same_image(shots[-1], f):
                shots.append(f)
            elif f:
                f.unlink(missing_ok=True)

    LOGS.mkdir(parents=True, exist_ok=True)
    log = adb("logcat", "-d", serial=serial, timeout=120).stdout or ""
    (LOGS / f"{repo}-android.log").write_text(log)
    res["crashlytics"] = "FirebaseCrashlytics" in log
    res["fatal"] = bool(re.search(r"FATAL EXCEPTION|AndroidRuntime.*FATAL", log))

    # Never trade a good set for a worse one. The first run of this function
    # replaced CalcMaster's five Play screenshots with the single one it had
    # managed to capture — the same way the iOS half once emptied iMaps, which
    # is why that half builds in a scratch directory. A capture that found
    # fewer screens than are already published is a capture that went wrong,
    # not a new set.
    tgt = out_android / "phoneScreenshots"
    have = len(list(tgt.glob("*.png"))) if tgt.exists() else 0
    if shots and len(shots) >= max(have, 1):
        tgt.mkdir(parents=True, exist_ok=True)
        for gone in tgt.glob("*.png"):
            gone.unlink()
        for i, s in enumerate(sorted(shots), start=1):
            shutil.copy(s, tgt / f"{i:02d}.png")
    elif shots:
        res["kept_existing"] = have
        res["error"] = (res["error"] + f" captured {len(shots)} but {have} already "
                        f"published; kept the existing set").strip()
    shutil.rmtree(staging, ignore_errors=True)
    adb("uninstall", pkg, serial=serial, timeout=90)
    res["shots"] = len(shots)
    return res


def drive_capture(app, app_dir, out_ios, out_android, udid):
    """Capture by driving the app under integration_test, not by poking at it.

    The idb path below photographs whatever is on screen, and for an app with
    a sign-in wall that is the login form — the Guideline 2.3.3 rejection.
    Neither live way past it is available: the documented test accounts do
    not authenticate (MA-036) and anonymous sign-in is disabled on the
    Supabase project (MA-040).

    Every app already carries integration_test/store_screenshots_test.dart
    and test_driver/integration_test.dart, written and then never run. That
    test drives the real app and can set up its own state first, so an app
    whose AuthService restores an offline session starts signed in with no
    network at all. yourtube goes from one login screen to five real ones.
    """
    res = {"repo": app["repo"], "screens": {}, "banner_patched": None, "error": ""}
    target = app_dir / "integration_test/store_screenshots_test.dart"
    driver = app_dir / "test_driver/integration_test.dart"
    if not target.exists() or not driver.exists():
        res["error"] = "no integration_test/test_driver pair"
        return res

    raw = app_dir / "store_screenshots"
    shutil.rmtree(raw, ignore_errors=True)
    r = sh(FLUTTER, "drive", "--driver=test_driver/integration_test.dart",
           f"--target=integration_test/store_screenshots_test.dart",
           "--dart-define=SCREENSHOT=true", "-d", udid,
           cwd=app_dir, timeout=2400)
    shots = sorted(raw.glob("*.png")) if raw.is_dir() else []
    if not shots:
        res["error"] = "drive produced no screenshots: " + \
                       (r.stderr or r.stdout).strip()[-220:]
        return res

    # Drop blank frames. A degraded simulator answers takeScreenshot with a
    # uniform white image, and the capture counts them as successes: a 43-app
    # run published ten apps' worth of empty screenshots, every frame
    # byte-identical, and the count alone looked fine. Standard deviation of
    # the greyscale is ~0 for a blank frame and >0.04 for a real screen.
    def blank(f):
        out = sh("magick", str(f), "-colorspace", "Gray", "-format",
                 "%[fx:standard_deviation]", "info:").stdout.strip()
        try:
            return float(out) < 0.02
        except ValueError:
            return False

    real = [s for s in shots if not blank(s)]
    if not real:
        res["error"] = (f"all {len(shots)} frames were blank — the simulator "
                        "was not rendering; reboot it and retry")
        return res
    if len(real) < len(shots):
        res["blank_dropped"] = len(shots) - len(real)
    shots = real
    shots = vet(shots, "iphone69", app["repo"], res)
    if not shots:
        res["error"] = "every frame failed the 2.3.3 audit: " + str(res.get("vet"))[:200]
        return res

    # Same rule as the idb path: never replace a published set with a
    # smaller one, and stage before touching what is already there.
    have = len(list(out_ios.glob("iphone69-*.png"))) if out_ios.is_dir() else 0
    if len(shots) < max(have, 1):
        res["error"] = f"captured {len(shots)} but {have} already published"
        res["screens"]["iphone69"] = have
        return res

    out_ios.mkdir(parents=True, exist_ok=True)
    for old in out_ios.glob("iphone69-*.png"):
        old.unlink()
    for i, s in enumerate(shots, start=1):
        shutil.copy(s, out_ios / f"iphone69-{i:02d}.png")

    tgt = out_android / "phoneScreenshots"
    tgt.mkdir(parents=True, exist_ok=True)
    for old in tgt.glob("*.png"):
        old.unlink()
    for i, s in enumerate(shots, start=1):
        # Play wants at most 2:1; the simulator frame is taller than that.
        col = sh("magick", str(s), "-gravity", "North", "-crop", "1x1+0+0",
                 "+repage", "-format", "%[pixel:p{0,0}]", "info:").stdout.strip() or "black"
        sh("magick", str(s), "-background", col, "-gravity", "center",
           "-extent", "1440x2880", str(tgt / f"{i:02d}.png"))

    res["screens"]["iphone69"] = len(shots)
    res["passed_sign_in"] = True   # the drive starts the app already signed in
    res["sign_in_gate"] = None
    return res


def capture(app, out_ios, out_android):
    repo = app["repo"]; app_dir = ROOT / repo / (app["dir"] if app["dir"] != "." else "")
    bundle = app["bundle_id"]
    res = {"repo": repo, "screens": {}, "banner_patched": None, "error": ""}
    patched = patch_banner(app_dir); res["banner_patched"] = None if patched is None else len(patched)
    # Bound before the try: the finally below cleans it up, and a build that
    # fails returns before the assignment — which raised UnboundLocalError and
    # hid the real error behind it.
    staging = None
    try:
        # SCREENSHOT=true hides debug-only affordances. An iOS release build
        # cannot run on a simulator, so these are debug builds, and without
        # this define they draw dev shortcuts the shipped app does not have —
        # Kinnav's "Demo mode (dev) — skip to app" went out onto its live Play
        # listing this way. Its own app_config.dart calls that grounds for
        # rejection. Apps that do not read the define are unaffected.
        b = sh(FLUTTER, "build", "ios", "--simulator", "--debug",
               "--dart-define=SCREENSHOT=true", cwd=app_dir, timeout=1800)
        if b.returncode != 0:
            res["error"] = "build failed: " + (b.stderr or b.stdout).strip()[-400:]; return res
        apps = list((app_dir / "build/ios/iphonesimulator").glob("*.app"))
        if not apps: res["error"] = "no .app produced"; return res
        # Capture into a scratch directory and only replace the real one once
        # a capture has actually succeeded. This used to delete the existing
        # screenshots here, before the first launch — so when BodyQuest and
        # daily-pulse timed out on a cold simulator, both lost the screenshots
        # they already had and had to be restored from git. A failed capture
        # must leave the app no worse than it found it.
        staging = pathlib.Path(tempfile.mkdtemp(prefix=f"aglshots-{repo}-"))
        real_out_ios, out_ios = out_ios, staging
        for dev, udid in DEVICES.items():
            boot(udid)
            clear_alerts(udid)   # a permission sheet left by the previous app blocks every later shot
            sh("xcrun", "simctl", "install", udid, str(apps[0]), timeout=120)
            sh("xcrun", "simctl", "launch", udid, bundle, timeout=60)
            time.sleep(8)
            clear_alerts(udid)   # first-run sheets and permission prompts
            time.sleep(4); clear_alerts(udid)   # consent forms (UMP) arrive a few seconds after launch
            # Record whether a sign-in gate was seen and whether we got past
            # it. Apple rejected apps under 2.3.3 for screenshots that showed
            # nothing but the login screen, and the only way the checklist
            # can tell is if the capture says so.
            before = describe(udid)
            gated = any(w in ((e.get("AXLabel") or "") + (e.get("AXValue") or "")).lower()
                        for e in before
                        for w in ("sign in", "log in", "password", "create account"))
            enter_app(udid)      # onboarding carousel, then a sign-in wall
            if gated:
                res["signed_in_with_qa"] = sign_in(udid)
                enter_app(udid)  # post-sign-in onboarding, if any
            after = describe(udid)
            still = any(w in ((e.get("AXLabel") or "") + (e.get("AXValue") or "")).lower()
                        for e in after
                        for w in ("sign in", "log in", "password", "create account"))
            res["sign_in_gate"] = gated
            res["passed_sign_in"] = (not still) if gated else True
            time.sleep(3)
            shots = []
            p = out_ios / f"{dev}-01.png"
            if shot(udid, p): shots.append(p)
            els = describe(udid)
            tabs = [e for e in els if re.search(r"\bTab \d+ of \d+", (e.get("AXLabel") or "") + " " + (e.get("AXValue") or "") + " " + (e.get("AXHint") or ""))]
            if len(tabs) < 2:
                # Bottom navigation renders as a row of Buttons sharing one y and
                # height in the lowest ~15% of the screen (CalcMaster, 2026-09-14).
                app_el = next((e for e in els if e.get("type") == "Application"), None)
                H = app_el["frame"]["height"] if app_el else 956
                W = app_el["frame"]["width"] if app_el else 440
                # A tab row is not always at the bottom: AGCleaner draws its three
                # tabs under the title bar, so accept a row in the top third too.
                # width < 0.6*W, not 0.5*W, and >=2 per row below: a Material 3
                # NavigationBar with two destinations gives each ~half the
                # screen, so both tests rejected it and Verba yielded a single
                # screenshot despite having a nav bar in main_shell.dart.
                btns = [e for e in els if e.get("type") in ("Button", "Tab")
                        and (e["frame"]["y"] > 0.80 * H or 0.05 * H < e["frame"]["y"] < 0.33 * H)
                        and 40 <= e["frame"]["width"] < 0.6 * W and (e.get("AXLabel") or "").strip()]
                rows = {}
                for e in btns: rows.setdefault((round(e["frame"]["y"] / 8), round(e["frame"]["height"] / 8)), []).append(e)
                # a tab bar: >=3 similarly sized labelled buttons on one line; take the lowest such row
                cands = []
                for row in rows.values():
                    ws = sorted(e["frame"]["width"] for e in row)
                    if len(row) >= 2 and ws[-1] <= ws[0] * 1.6: cands.append(row)
                # Prefer a bottom bar when both exist; otherwise take the top row.
                bottom = [r for r in cands if r[0]["frame"]["y"] > 0.80 * H]
                best = max(bottom or cands, key=lambda r: r[0]["frame"]["y"], default=[])
                tabs = best
            # de-duplicate by x position, keep order
            seen = set(); ordered = []
            for e in sorted(tabs, key=lambda e: e["frame"]["x"]):
                k = round(e["frame"]["x"])
                if k in seen: continue
                seen.add(k); ordered.append(e)
            for i, e in enumerate(ordered[1:MAX_SCREENS], start=2):
                tap(udid, *center(e)); time.sleep(3)
                p = out_ios / f"{dev}-{i:02d}.png"
                if shot(udid, p): shots.append(p)

            # Play refuses a listing with fewer than two phone screenshots, and an
            # app with no tab bar yields exactly one. Scroll the first screen and
            # shoot again: a real second view of the app, not a duplicate.
            if len(shots) < 2:
                app_el = next((e for e in els if e.get("type") == "Application"), None)
                H = app_el["frame"]["height"] if app_el else 956
                W = app_el["frame"]["width"] if app_el else 440
                swipe(udid, W / 2, H * 0.75, W / 2, H * 0.25)
                time.sleep(2)
                p = out_ios / f"{dev}-02.png"
                if shot(udid, p) and not same_image(shots[0], p):
                    shots.append(p)
                else:
                    p.unlink(missing_ok=True)

            # Still one shot: the first screen neither scrolls nor has tabs. Open a
            # clearly non-destructive screen instead. Only these labels are tapped,
            # so nothing is created, sent or deleted to get a screenshot.
            if len(shots) < 2:
                SAFE = ("settings", "about", "info", "help", "menu", "more", "history",
                        "details", "profile", "account", "search", "preferences")
                # Type is not filtered. Flutter exposes a tappable card as
                # "Other" or "StaticText" as often as "Button", and Kinnav's
                # home screen — which is nothing but cards reading Guardians,
                # Call History, Chat — produced no candidate at all under the
                # old Button/Cell/Link filter. A minimum size keeps this off
                # labels and decorations.
                cand = next((e for e in describe(udid)
                             if e["frame"]["width"] >= 60 and e["frame"]["height"] >= 28
                             and any(w in (e.get("AXLabel") or "").strip().lower() for w in SAFE)), None)
                if cand:
                    tap(udid, *center(cand)); time.sleep(3)
                    p = out_ios / f"{dev}-02.png"
                    if shot(udid, p) and not same_image(shots[0], p):
                        shots.append(p)
                    else:
                        p.unlink(missing_ok=True)
            shots = vet(shots, dev, repo, res)
            # The iOS half of the device logs. Crashlytics on iOS reports
            # through the same simulator log stream, so this is where an
            # "Initializing Firebase Crashlytics" line or a crash shows up.
            # --last bounds it; without it `log show` walks the whole store.
            LOGS.mkdir(parents=True, exist_ok=True)
            lg = sh("xcrun", "simctl", "spawn", udid, "log", "show",
                    "--style", "compact", "--last", "5m",
                    "--predicate", f'processImagePath CONTAINS "{repo}" '
                                   f'OR senderImagePath CONTAINS "Runner"',
                    timeout=180)
            if lg.stdout:
                (LOGS / f"{repo}-ios-{dev}.log").write_text(lg.stdout)
                res.setdefault("ios_crashlytics", False)
                res["ios_crashlytics"] |= "Crashlytics" in lg.stdout
            sh("xcrun", "simctl", "terminate", udid, bundle, timeout=30)
            sh("xcrun", "simctl", "uninstall", udid, bundle, timeout=60)
            res["screens"][dev] = len(shots)
            # Android copies
            # Same rule as the iOS side: build the new set somewhere else and
            # only replace the real directory once there is something to
            # replace it with. Protecting only fastlane/screenshots was not
            # enough — a forced-failure test still emptied iMaps'
            # phoneScreenshots, because this loop deleted first and then had
            # nothing to write.
            if not shots:
                continue
            tgt = out_android / ("phoneScreenshots" if dev == "iphone69" else "tenInchScreenshots")
            tgt_staging = pathlib.Path(tempfile.mkdtemp(prefix=f"aglandroid-{repo}-"))
            for i, s in enumerate(shots, start=1):
                dst = tgt_staging / f"{i:02d}.png"
                if dev == "iphone69":   # 1320x2868 -> pad to 1440x2880 (exactly 2:1, Play's limit)
                    col = sh("magick", s, "-gravity", "North", "-crop", "1x1+0+0", "+repage", "-format", "%[pixel:p{0,0}]", "info:").stdout.strip() or "black"
                    sh("magick", str(s), "-background", col, "-gravity", "center", "-extent", "1440x2880", str(dst))
                else:
                    shutil.copy(s, dst)

            made = sorted(tgt_staging.glob("*.png"))
            if made:
                tgt.mkdir(parents=True, exist_ok=True)
                for gone in tgt.glob("*.png"):
                    gone.unlink()
                for f in made:
                    shutil.copy(f, tgt / f.name)
            shutil.rmtree(tgt_staging, ignore_errors=True)

        # Promote staging over the real directory, now that something was
        # actually captured. Up to here the app's existing screenshots are
        # untouched, which is the whole point of the scratch directory.
        if any(res["screens"].values()):
            real_out_ios.mkdir(parents=True, exist_ok=True)
            for old in real_out_ios.glob("*.png"):
                old.unlink()
            for f in sorted(staging.glob("*.png")):
                shutil.copy(f, real_out_ios / f.name)
        else:
            # setdefault is no use here: res["error"] already exists as "".
            res["error"] = (res["error"] or
                            "nothing captured; existing screenshots left alone")
    finally:
        if patched: unpatch(app_dir, patched)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
    return res


def purge_derived_data(max_age_min=5):
    """Xcode leaves several GB per archive in DerivedData; 43 apps filled the disk
    on 2026-09-14. Remove Runner-*/Pods-* trees not touched in the last few minutes."""
    import shutil, time
    dd = pathlib.Path.home() / "Library/Developer/Xcode/DerivedData"
    now = time.time()
    for d in dd.glob("*"):
        if d.name.startswith(("Runner-", "Pods-")) and d.is_dir() and now - d.stat().st_mtime > max_age_min * 60:
            shutil.rmtree(d, ignore_errors=True)

def main():
    apps = json.load(open(M / "apps.json"))["apps"]
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if names: apps = [a for a in apps if a["repo"] in names]
    results = json.load(open(RESULTS)) if RESULTS.exists() else {}

    # --android captures on the emulator as well. Without it the Android
    # screenshots stay what they have always been: the iOS capture padded to
    # 1440x2880, i.e. an iPhone render on a Play listing.
    want_android = "--android" in sys.argv
    skip_ios = "--android-only" in sys.argv
    want_android = want_android or skip_ios
    serial = android_device() if want_android else None
    if want_android and not serial:
        print("no Android emulator and none could be started; "
              "continuing with iOS only", flush=True)
    elif serial:
        print(f"android device: {serial}", flush=True)

    for a in sorted(apps, key=lambda x: x["repo"].lower()):
        purge_derived_data()
        lock = DIST / "ios-batch/current_app"
        while lock.exists() and lock.read_text().strip() == a["repo"]:
            print(f"{a['repo']}: TestFlight is building it — waiting", flush=True); time.sleep(60)
        mine = DIST / "screenshots_current"; mine.write_text(a["repo"])  # run_batch waits on this

        if "--skip-done" in sys.argv and results.get(a["repo"], {}).get("screens", {}).get("iphone69", 0) >= 1:
            print(f"{a['repo']}: done, skipping"); continue
        app_dir = ROOT / a["repo"] / (a["dir"] if a["dir"] != "." else "")
        out_ios = app_dir / "fastlane/screenshots/en-US"; out_ios.mkdir(parents=True, exist_ok=True)
        # Old screenshots are removed only once a new build exists (see capture): a
        # failed build must not leave an app with no screenshots at all.
        out_android = app_dir / "fastlane/metadata/android/en-US/images"
        t0 = time.time(); print(f"{a['repo']}: building…", flush=True)
        if "--drive" in sys.argv:
            # Drive the app under integration_test instead of poking at it
            # with idb. See drive_capture for why.
            ios_udid = next(iter(DEVICES.values()))
            boot(ios_udid)
            try:
                r = drive_capture(a, app_dir, out_ios, out_android, ios_udid)
            except Exception as e:
                r = {"repo": a["repo"], "screens": {},
                     "error": f"{type(e).__name__}: {e}"[:300]}
        elif skip_ios:
            r = {"repo": a["repo"], "screens": {}, "error": ""}
        else:
            try: r = capture(a, out_ios, out_android)
            except Exception as e: r = {"repo": a["repo"], "screens": {}, "error": f"{type(e).__name__}: {e}"[:300]}
        if serial:
            try:
                r["android"] = android_capture(a, app_dir, out_android, serial)
            except Exception as e:
                r["android"] = {"shots": 0, "error": f"{type(e).__name__}: {e}"[:200]}
        mine.write_text("")
        r["seconds"] = round(time.time() - t0); results[a["repo"]] = r
        json.dump(results, open(RESULTS, "w"), indent=1)
        and_ = r.get("android") or {}
        print(f"{a['repo']}: ios={r['screens']} "
              f"android={and_.get('shots', '-')} "
              f"crashlytics={and_.get('crashlytics', '-')} "
              f"{r['error']}{(' | android: ' + and_['error']) if and_.get('error') else ''} "
              f"({r['seconds']}s)", flush=True)

if __name__ == "__main__": main()
