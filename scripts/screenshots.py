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
    """A scroll that moved nothing must not become a second screenshot."""
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

def unpatch(app_dir): sh("git", "checkout", "--", "lib", cwd=app_dir)

def clear_alerts(udid, rounds=4):
    """Tap through system permission alerts / first-run sheets, most permissive first."""
    for _ in range(rounds):
        els = describe(udid)
        btns = [e for e in els if e.get("type") == "Button" and (e.get("AXLabel") or "").strip() in DISMISS]
        if not btns: return
        btns.sort(key=lambda e: DISMISS.index((e.get("AXLabel") or "").strip()))
        tap(udid, *center(btns[0])); time.sleep(2.5)

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
        b = sh(FLUTTER, "build", "ios", "--simulator", "--debug", cwd=app_dir, timeout=1800)
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
                btns = [e for e in els if e.get("type") in ("Button", "Tab")
                        and (e["frame"]["y"] > 0.80 * H or 0.05 * H < e["frame"]["y"] < 0.33 * H)
                        and 40 <= e["frame"]["width"] < 0.5 * W and (e.get("AXLabel") or "").strip()]
                rows = {}
                for e in btns: rows.setdefault((round(e["frame"]["y"] / 8), round(e["frame"]["height"] / 8)), []).append(e)
                # a tab bar: >=3 similarly sized labelled buttons on one line; take the lowest such row
                cands = []
                for row in rows.values():
                    ws = sorted(e["frame"]["width"] for e in row)
                    if len(row) >= 3 and ws[-1] <= ws[0] * 1.6: cands.append(row)
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
                cand = next((e for e in describe(udid)
                             if e.get("type") in ("Button", "Cell", "Link")
                             and any(w in (e.get("AXLabel") or "").strip().lower() for w in SAFE)), None)
                if cand:
                    tap(udid, *center(cand)); time.sleep(3)
                    p = out_ios / f"{dev}-02.png"
                    if shot(udid, p) and not same_image(shots[0], p):
                        shots.append(p)
                    else:
                        p.unlink(missing_ok=True)
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
        if patched: unpatch(app_dir)
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
        try: r = capture(a, out_ios, out_android)
        except Exception as e: r = {"repo": a["repo"], "screens": {}, "error": f"{type(e).__name__}: {e}"[:300]}
        mine.write_text("")
        r["seconds"] = round(time.time() - t0); results[a["repo"]] = r
        json.dump(results, open(RESULTS, "w"), indent=1)
        print(f"{a['repo']}: {r['screens']} banner_patched={r.get('banner_patched')} {r['error']} ({r['seconds']}s)", flush=True)

if __name__ == "__main__": main()
