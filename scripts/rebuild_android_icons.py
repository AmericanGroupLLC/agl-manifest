#!/usr/bin/env python3
"""Rebuild the Android launcher icon for apps whose iOS artwork is fine.

These apps already have real iOS artwork, so nothing new needs designing — the
Android side is simply wrong, in one of four ways the audit measured:

  Verba            ships the stock blue Flutter logo at all five densities
  BodyQuest        no adaptive icon, so Android 8+ shrinks a square PNG into a badge
  GroceryMatch     same
  MyHealth         same
  yourtube         same, plus ic_launcher_round is a byte-identical square copy
  NexusTransferPay adaptive foreground is full-bleed, so the mask crops the mark
  PilotEnRoute     full-bleed and undersized (192px where 432 is required)
  Uscis-Case       full-bleed, undersized, and foreground/round assets cross-wired
  iMaps            adaptive foreground is an "iM" monogram while iOS is a pin logo

The master is each app's own 1024 iOS icon (or, for Verba, the real source art
already in the repo but never wired up), so Android ends up matching iOS rather
than diverging again.

    python3 fix_android_icons.py --dry-run
    python3 fix_android_icons.py
"""

from __future__ import annotations

import argparse
import json
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path("/Users/spatchava/agl")

# app -> master image, relative to the app directory. None means "use the iOS
# 1024 icon", which is the right source in every case except Verba, whose iOS
# icon is fine but whose repo also carries the original high-res art.
APPS: dict[str, str | None] = {
    "Verba": "assets/icon/app_icon.png",
    "BodyQuest": None,
    "GroceryMatch": None,
    "MyHealth": None,
    "yourtube": None,
    "NexusTransferPay": None,
    "PilotEnRoute": None,
    "Uscis-Case": None,
    "iMaps": None,
}

DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
ADAPTIVE = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
# Only the middle 72dp of the 108dp adaptive canvas is guaranteed visible.
SAFE = 72 / 108

ADAPTIVE_XML = ('<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@mipmap/ic_launcher_background"/>\n'
                '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
                '</adaptive-icon>\n')


def app_dir(repo: str, apps: list[dict]) -> pathlib.Path:
    a = next(x for x in apps if x["repo"] == repo)
    d = a.get("dir", ".") or "."
    return ROOT / repo if d == "." else ROOT / repo / d


def ios_master(d: pathlib.Path) -> pathlib.Path | None:
    p = d / "ios/Runner/Assets.xcassets/AppIcon.appiconset"
    if not p.exists():
        return None
    best, best_px = None, 0
    for f in p.glob("*.png"):
        try:
            w, _ = Image.open(f).size
        except Exception:
            continue
        if w > best_px:
            best, best_px = f, w
    return best


def edge_colour(img: Image.Image) -> tuple[int, int, int]:
    """Background colour for the adaptive layer, sampled from the art's corners."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    pts = [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]
    cols = [rgb.getpixel(p) for p in pts]
    return tuple(sum(c[i] for c in cols) // len(cols) for i in range(3))


def circular(src: Image.Image, size: int) -> Image.Image:
    out = src.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    out.putalpha(mask.resize((size, size), Image.LANCZOS))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    apps = json.loads((ROOT / "agl-manifest/apps.json").read_text())["apps"]
    for repo, rel in APPS.items():
        d = app_dir(repo, apps)
        src = (d / rel) if rel else ios_master(d)
        if src is None or not src.exists():
            print(f"{repo:<18} SKIP no master image")
            continue
        master = Image.open(src).convert("RGBA")
        res = d / "android/app/src/main/res"
        if not res.exists():
            print(f"{repo:<18} SKIP no android res/")
            continue
        if args.dry_run:
            print(f"{repo:<18} would use {src.relative_to(ROOT)} {master.size}")
            continue

        bg = edge_colour(master)
        n = 0
        for dens, px in DENSITIES.items():
            out = res / f"mipmap-{dens}"
            out.mkdir(parents=True, exist_ok=True)
            master.convert("RGB").resize((px, px), Image.LANCZOS).save(
                out / "ic_launcher.png", "PNG")
            circular(master, px).save(out / "ic_launcher_round.png", "PNG")
            n += 2
        for dens, px in ADAPTIVE.items():
            out = res / f"mipmap-{dens}"
            out.mkdir(parents=True, exist_ok=True)
            # Inset the whole artwork into the safe zone instead of letting it
            # bleed to the canvas edge, which is what the mask was cropping.
            fg = Image.new("RGBA", (px, px), (0, 0, 0, 0))
            inner = max(1, int(px * SAFE))
            fg.paste(master.resize((inner, inner), Image.LANCZOS),
                     ((px - inner) // 2, (px - inner) // 2))
            fg.save(out / "ic_launcher_foreground.png", "PNG")
            Image.new("RGB", (px, px), bg).save(out / "ic_launcher_background.png", "PNG")
            n += 2
        anydpi = res / "mipmap-anydpi-v26"
        anydpi.mkdir(parents=True, exist_ok=True)
        (anydpi / "ic_launcher.xml").write_text(ADAPTIVE_XML)
        (anydpi / "ic_launcher_round.xml").write_text(ADAPTIVE_XML)
        print(f"{repo:<18} {n} files from {src.name} bg=#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
