#!/usr/bin/env python3
"""Replace the 1x1 placeholder launch images and remove junk icon files.

Three separate pieces of leftover scaffolding, all measured by the icon audit:

1. 38 apps ship the Flutter template LaunchImage — a 68-byte, 1x1 transparent
   PNG, md5 978c1bee49d7ad5fc1a4d81099b13e18 — in all three scale slots. The
   launch screen therefore shows a blank window while the app boots. Each app
   gets a real launch image built from its own app icon, so the splash matches
   the icon the user just tapped.

2. AGCleaner and WiFiTrail each carry four files named *.png whose entire
   contents are the ASCII text "DUMMY ASSET" (11 bytes). They are Expo-scaffold
   leftovers, referenced by nothing, and are deleted rather than replaced.

3. AGrammarly, HerJourney and NewsBoard still carry the five Flutter template
   ic_launcher.png files. Their manifests point at @mipmap/launcher_icon, so
   users never see them, but they ship inside the APK as dead weight and make
   the repo look like it still uses the default icon. Deleted only after
   confirming the manifest does not reference @mipmap/ic_launcher.

    python3 fix_launch_and_junk.py --dry-run
    python3 fix_launch_and_junk.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

from PIL import Image

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402
TEMPLATE_LAUNCH_MD5 = "978c1bee49d7ad5fc1a4d81099b13e18"
TEMPLATE_IC_LAUNCHER_MD5 = {
    "6270344430679711b81476e29878caa7", "13e9c72ec37fac220397aa819fa1ef2d",
    "a0a8db5985280b3679d99a820ae2db79", "afe1b655b9f32da22f9a4301bb8e6ba8",
    "57838d52c318faff743130c3fcfae0c6",
}
DUMMY = b"DUMMY ASSET"
# 1x / 2x / 3x logo edge, matching what the apps that already had a real launch
# image use (CalcMaster 180/360/540).
LAUNCH_SIZES = [("LaunchImage.png", 180), ("LaunchImage@2x.png", 360),
                ("LaunchImage@3x.png", 540)]


def md5(p: pathlib.Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def app_dir(a: dict) -> pathlib.Path:
    d = a.get("dir", ".") or "."
    return ROOT / a["repo"] if d == "." else ROOT / a["repo"] / d


def ios_master(d: pathlib.Path) -> pathlib.Path | None:
    p = d / "ios/Runner/Assets.xcassets/AppIcon.appiconset"
    if not p.exists():
        return None
    best, px = None, 0
    for f in p.glob("*.png"):
        try:
            w, _ = Image.open(f).size
        except Exception:
            continue
        if w > px:
            best, px = f, w
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    apps = [a for a in json.loads((MANIFEST / "apps.json").read_text())["apps"]
            if a.get("flutter")]

    launch_fixed, launch_skipped, dummies, stale = 0, 0, 0, 0

    for a in apps:
        d = app_dir(a)
        ls = d / "ios/Runner/Assets.xcassets/LaunchImage.imageset"
        if not ls.exists():
            continue
        existing = [p for p in ls.glob("LaunchImage*.png")]
        if not existing:
            continue
        # Only replace the template. An app that already has a real launch
        # image keeps it.
        if not all(md5(p) == TEMPLATE_LAUNCH_MD5 for p in existing):
            launch_skipped += 1
            continue
        src = ios_master(d)
        if src is None:
            continue
        icon = Image.open(src).convert("RGBA")
        if dry:
            print(f"{a['repo']:<18} would write 3 launch images from {src.name}")
            launch_fixed += 1
            continue
        for name, px in LAUNCH_SIZES:
            # Transparent canvas: LaunchScreen.storyboard supplies the
            # background colour, so a baked-in one would clash in dark mode.
            img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
            img.paste(icon.resize((px, px), Image.LANCZOS), (0, 0))
            img.save(ls / name, "PNG")
        launch_fixed += 1
        print(f"{a['repo']:<18} launch images written")

    for repo in ("AGCleaner", "WiFiTrail"):
        for p in sorted((ROOT / repo / "assets").glob("*.png")):
            try:
                if p.read_bytes().strip() != DUMMY:
                    continue
            except Exception:
                continue
            print(f"{repo:<18} {'would delete' if dry else 'deleted'} {p.relative_to(ROOT)}")
            if not dry:
                p.unlink()
            dummies += 1

    for a in apps:
        if a["repo"] not in ("AGrammarly", "HerJourney", "NewsBoard"):
            continue
        d = app_dir(a)
        man = d / "android/app/src/main/AndroidManifest.xml"
        if not man.exists():
            continue
        icon_attr = re.search(r'android:icon="@mipmap/([A-Za-z0-9_]+)"', man.read_text())
        if not icon_attr or icon_attr.group(1) == "ic_launcher":
            print(f"{a['repo']:<18} KEPT ic_launcher.png - manifest still points at it")
            continue
        for p in sorted((d / "android/app/src/main/res").glob("mipmap-*/ic_launcher.png")):
            if md5(p) not in TEMPLATE_IC_LAUNCHER_MD5:
                continue
            print(f"{a['repo']:<18} {'would delete' if dry else 'deleted'} stale {p.relative_to(ROOT)}")
            if not dry:
                p.unlink()
            stale += 1

    print(f"\nlaunch images written: {launch_fixed}   left alone (already real): {launch_skipped}")
    print(f"DUMMY ASSET files removed: {dummies}   stale template icons removed: {stale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
