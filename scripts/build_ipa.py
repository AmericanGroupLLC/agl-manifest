#!/usr/bin/env python3
"""Archive and export a signed, App Store-ready .ipa for each Flutter app.

Why this is not `flutter build ipa`: every Runner.xcodeproj in this portfolio is
set to CODE_SIGN_STYLE = Automatic, and automatic signing needs an interactive
Xcode account session that this machine does not have. An App Store Connect API
key authenticates the *API* but does not give xcodebuild an Xcode account. So the
archive is driven directly with manual signing against the profiles that were
created from the API and downloaded into
~/Library/MobileDevice/Provisioning Profiles.

Three steps per app, and each can fail independently so each is recorded:
  1. flutter build ios --release --no-codesign  — compiles Dart and runs pod install
  2. xcodebuild archive with manual signing     — the step that needs the profile
  3. xcodebuild -exportArchive                  — produces the .ipa

The .ipa is copied to the run's .dist directory (see scripts/agl_paths.py)
and the archive tree is deleted;
a .xcarchive is ~200 MB-1 GB and 43 of them will not fit.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import plistlib
import shutil
import subprocess
import time
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT, admob_defines, flutter_bin  # noqa: E402

ROOT = _ROOT
MANIFEST = _MANIFEST / "apps.json"
PROFILE_MAP = ROOT / ".dist" / "ios" / "profile_map.json"
# CFBundleVersion for every IPA this run builds. The pubspec's +N is the
# Android version code and often already exists on App Store Connect: on
# 2026-10-12 daily-pulse's IPA carried build 1, Apple already had build 1 from
# September, and the upload lane reported it "present" without uploading.
# A minute timestamp only ever increases. AGL_IOS_BUILD_NUMBER overrides.
BUILD_NUMBER = os.environ.get("AGL_IOS_BUILD_NUMBER") or time.strftime("%Y%m%d%H%M")
FLUTTER = flutter_bin()
DIST = ROOT / ".dist"
WORK = ROOT / ".dist" / "ios-work"
TEAM = "TLH7Z3G27A"


def run(cmd, cwd=None, timeout=3600):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def tail(text: str, n: int = 12) -> str:
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return " | ".join(lines[-n:])[:1500]


def build(app: dict, profile: str) -> dict:
    repo = app["repo"]
    d = ROOT / repo if app.get("dir", ".") == "." else ROOT / repo / app["dir"]
    bid = app["bundle_id"]
    rec = {"repo": repo, "bundle_id": bid, "profile": profile, "dir": str(d)}
    t0 = time.time()

    ios = d / "ios"
    if not ios.exists():
        rec["result"] = "NO_IOS_DIR"
        return rec

    # 1. Compile Dart and install pods. --no-codesign because signing happens in
    #    the archive step, and doing it here would need the same profile twice.
    r = run([str(FLUTTER), "build", "ios", "--release", "--no-codesign", f"--build-number={BUILD_NUMBER}", *admob_defines(app["repo"])], cwd=d, timeout=3600)
    # Flutter's stale .dart_tool/package_graph.json (see build_release.py):
    # AeroSwift and BuddyPlay failed here in under 4 s on it.
    if r.returncode != 0 and "package_graph.json" in (r.stdout + r.stderr):
        shutil.rmtree(d / ".dart_tool", ignore_errors=True)
        run([str(FLUTTER), "pub", "get"], cwd=d, timeout=900)
        r = run([str(FLUTTER), "build", "ios", "--release", "--no-codesign", f"--build-number={BUILD_NUMBER}", *admob_defines(app["repo"])], cwd=d, timeout=3600)
        rec["retried_after_stale_package_graph"] = True
    # "CocoaPods's specs repository is too out-of-date to satisfy
    # dependencies". The runner's ~/.cocoapods comes from an Actions cache and
    # can lag, so refresh the index once and retry. CocoaPods prints the same
    # words when ios/Podfile.lock pins a version the plugin no longer accepts,
    # which no index refresh fixes: radiotune (ship runs 38294393167 and
    # 38553467641) locks Google-Mobile-Ads-SDK 11.13.0 while its
    # google_mobile_ads 9.1.0 requires ~> 13.7 - the app's Podfile.lock has to
    # be regenerated. The refresh's own output is kept to tell the two apart.
    if r.returncode != 0 and "specs repository is too out-of-date" in (r.stdout + r.stderr):
        u = run(["pod", "install", "--repo-update"], cwd=ios, timeout=1800)
        rec["retried_after_pod_repo_update"] = u.returncode == 0
        if u.returncode != 0:
            rec["pod_repo_update_detail"] = tail(u.stdout + u.stderr, 6)
        r = run([str(FLUTTER), "build", "ios", "--release", "--no-codesign", f"--build-number={BUILD_NUMBER}", *admob_defines(app["repo"])], cwd=d, timeout=3600)
    if r.returncode != 0:
        rec.update(result="FLUTTER_BUILD_FAILED", detail=tail(r.stdout + r.stderr))
        rec["seconds"] = round(time.time() - t0, 1)
        return rec

    WORK.mkdir(parents=True, exist_ok=True)
    archive = WORK / f"{repo}.xcarchive"
    shutil.rmtree(archive, ignore_errors=True)

    workspace = ios / "Runner.xcworkspace"
    target = ["-workspace", str(workspace)] if workspace.exists() else [
        "-project", str(ios / "Runner.xcodeproj")]

    # 2. Archive UNSIGNED. A build setting given on the xcodebuild command line
    #    applies to every target in the workspace, including the CocoaPods ones,
    #    and those reject it outright: "PromisesObjC does not support
    #    provisioning profiles ... but provisioning profile ... has been manually
    #    specified". There is no way to scope a CLI setting to one target, so the
    #    signing is deferred to -exportArchive, which signs the app and every
    #    embedded framework from the ExportOptions plist.
    r = run(["xcodebuild", *target, "-scheme", "Runner", "-configuration", "Release",
             "-sdk", "iphoneos", "-archivePath", str(archive), "archive",
             "CODE_SIGNING_ALLOWED=NO", "CODE_SIGNING_REQUIRED=NO",
             "CODE_SIGN_IDENTITY=", "CODE_SIGN_ENTITLEMENTS=",
             "EXPANDED_CODE_SIGN_IDENTITY="], cwd=d, timeout=3600)
    if r.returncode != 0 or not archive.exists():
        rec.update(result="ARCHIVE_FAILED", detail=tail(r.stdout + r.stderr))
        rec["seconds"] = round(time.time() - t0, 1)
        shutil.rmtree(archive, ignore_errors=True)
        return rec

    # 3. Export. Xcode 15.4+ calls the App Store destination "app-store-connect";
    #    the older name is accepted as a fallback for safety.
    out = WORK / f"{repo}-export"
    shutil.rmtree(out, ignore_errors=True)
    plist = WORK / f"{repo}-ExportOptions.plist"
    exported = None
    for method in ("app-store-connect", "app-store"):
        plist.write_bytes(plistlib.dumps({
            "method": method,
            "teamID": TEAM,
            "signingStyle": "manual",
            "provisioningProfiles": {bid: profile},
            "stripSwiftSymbols": True,
            "uploadSymbols": True,
            "destination": "export",
        }))
        r = run(["xcodebuild", "-exportArchive", "-archivePath", str(archive),
                 "-exportOptionsPlist", str(plist), "-exportPath", str(out),
                 "-allowProvisioningUpdates"], cwd=d, timeout=1800)
        found = list(out.glob("*.ipa")) if out.exists() else []
        if r.returncode == 0 and found:
            exported = found[0]
            rec["export_method"] = method
            break
        rec["export_detail"] = tail(r.stdout + r.stderr)

    if not exported:
        rec.update(result="EXPORT_FAILED")
        rec["seconds"] = round(time.time() - t0, 1)
        shutil.rmtree(archive, ignore_errors=True)
        return rec

    DIST.mkdir(exist_ok=True)
    kept = DIST / f"{repo}.ipa"
    shutil.copy2(exported, kept)
    rec.update(result="EXPORTED", ipa=str(kept.relative_to(ROOT)),
               bytes=kept.stat().st_size)

    # An .ipa is the deliverable; the archive is regenerable and enormous.
    shutil.rmtree(archive, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    # docs/, not .dist/. store_checklist.py reads the committed copy, and
    # writing only to .dist meant the two drifted: four apps were rebuilt and
    # the checklist went on reporting "no IPA" because the committed file was
    # never updated. .dist keeps a copy so a run outside the repo still works.
    ap.add_argument("--out",
                    default=str(_MANIFEST / "docs" / "ios-ipa-evidence.json"))
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())["apps"]
    profiles = json.loads(PROFILE_MAP.read_text())
    wanted = [a for a in manifest if a.get("flutter")]
    if args.apps:
        wanted = [a for a in wanted if a["repo"] in args.apps]

    outfile = pathlib.Path(args.out)
    records = json.loads(outfile.read_text()) if outfile.exists() else []
    # "Already exported" only when the IPA is actually here. The evidence file
    # is committed, so on a CI runner it lists the laptop's exports: ship run
    # 38203990386 skipped all 43 builds as "already exported" and uploaded
    # nothing, because no IPA existed on the runner.
    done = {r["repo"] for r in records
            if r.get("result") == "EXPORTED" and r.get("ipa") and (ROOT / r["ipa"]).exists()}

    for i, app in enumerate(wanted, 1):
        repo = app["repo"]
        if repo in done:
            print(f"[{i}/{len(wanted)}] {repo} ... already exported", flush=True)
            continue
        profile = profiles.get(app["bundle_id"])
        if not profile:
            print(f"[{i}/{len(wanted)}] {repo} ... NO_PROFILE", flush=True)
            records = [r for r in records if r["repo"] != repo]
            records.append({"repo": repo, "result": "NO_PROFILE",
                            "bundle_id": app["bundle_id"]})
        else:
            print(f"[{i}/{len(wanted)}] {repo} ...", end=" ", flush=True)
            rec = build(app, profile)
            print(f"{rec['result']} ({rec.get('seconds', 0)}s)", flush=True)
            # Print the reason, not just the verdict. The evidence file holds
            # it, but a failed job skips the artifact upload, so the log was
            # the only place left and it said nothing.
            why = rec.get("detail") or rec.get("export_detail")
            if rec.get("result") != "EXPORTED" and why:
                for line in str(why).strip().splitlines()[-12:]:
                    print(f"    {line}", flush=True)
            records = [r for r in records if r["repo"] != repo]
            records.append(rec)
        outfile.write_text(json.dumps(records, indent=1))
        # Mirror into .dist so anything reading run artefacts still finds it.
        try:
            mirror = ROOT / ".dist" / "ios-ipa-evidence.json"
            mirror.parent.mkdir(parents=True, exist_ok=True)
            if mirror != outfile:
                mirror.write_text(json.dumps(records, indent=1))
        except OSError:
            pass

    # Only this run's apps. The evidence file accumulates, so counting all of
    # it reports past successes next to present failures and the step still
    # exits 0 — the same false green build_release.py had.
    by_repo = {r["repo"]: r for r in records}
    this_run = [by_repo[a["repo"]] for a in wanted if a["repo"] in by_repo]
    ok = sum(1 for r in this_run if r.get("result") == "EXPORTED")
    bad = [r for r in this_run if r.get("result") != "EXPORTED"]

    print(f"\nEXPORTED {ok}/{len(this_run)} this run")
    if bad:
        print(f"::error::{len(bad)} app(s) did not export: "
              f"{', '.join(sorted(r['repo'] for r in bad))}")
        for r in sorted(bad, key=lambda x: x["repo"]):
            print(f"  {r['repo']}: {r.get('result')}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
