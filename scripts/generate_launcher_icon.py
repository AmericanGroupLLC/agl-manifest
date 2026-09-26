#!/usr/bin/env python3
"""Give a ported app its own launcher icon instead of the Flutter logo.

`flutter create` ships Flutter's own logo, and it is easy to miss: analyze is
clean, tests pass, the release bundle signs. It only shows up on a home screen —
which is where five freshly ported apps were found sitting side by side, all
four identical blue Flutter marks, indistinguishable from each other.

That is not cosmetic. Both stores reject the framework's placeholder icon, and a
user cannot tell two of these apps apart on their own device.

This draws a monogram on the app's brand colour: a rounded square for Android
(and the adaptive-icon foreground/background pair) and the full opaque square
iOS requires — an iOS icon with an alpha channel is rejected at upload, which is
why the alpha is flattened rather than left to chance.

A monogram is a placeholder with self-respect, not a substitute for a designed
icon. It is legible at 48px, distinct per app, and honest about being typographic
rather than pretending to be artwork.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT  # noqa: E402

# Brand colour and monogram per app. Colours are taken from each app's own
# theme where it has one, so the icon matches the first screen the app shows.
BRANDS = {
    "AGStudio":        ("#6D28D9", "AG"),
    "AeroSwift":       ("#0B63CE", "AS"),
    "ApexMarketWatch": ("#0B7A55", "AM"),
    "BuddyPlay":       ("#6D3BE4", "BP"),
    "MyCard":          ("#4F46E5", "MC"),
    "PlantPulse":      ("#1E40AF", "OC"),   # product is OmniControl
}

# Android density buckets. The adaptive foreground is larger because the OS
# masks it down to a circle/squircle and clips ~25% off each edge.
ANDROID = {
    "mipmap-mdpi": 48, "mipmap-hdpi": 72, "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144, "mipmap-xxxhdpi": 192,
}

IOS_SIZES = [
    ("Icon-App-20x20@1x.png", 20), ("Icon-App-20x20@2x.png", 40), ("Icon-App-20x20@3x.png", 60),
    ("Icon-App-29x29@1x.png", 29), ("Icon-App-29x29@2x.png", 58), ("Icon-App-29x29@3x.png", 87),
    ("Icon-App-40x40@1x.png", 40), ("Icon-App-40x40@2x.png", 80), ("Icon-App-40x40@3x.png", 120),
    ("Icon-App-60x60@2x.png", 120), ("Icon-App-60x60@3x.png", 180),
    ("Icon-App-76x76@1x.png", 76), ("Icon-App-76x76@2x.png", 152),
    ("Icon-App-83.5x83.5@2x.png", 167),
    ("Icon-App-1024x1024@1x.png", 1024),
]

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]


def font_for(px: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if pathlib.Path(path).exists():
            try:
                return ImageFont.truetype(path, px)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_icon(size: int, colour: str, text: str, *, rounded: bool, scale: float = 0.42) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=colour)
    else:
        d.rectangle([0, 0, size, size], fill=colour)

    f = font_for(max(8, int(size * scale)))
    # anchor="mm" centres on the glyph's own box; centring on the bounding box of
    # the string instead leaves capitals visibly high, because the box includes
    # descender space these letters never use.
    d.text((size / 2, size / 2), text, font=f, fill="white", anchor="mm")
    return img


def write(app: str) -> str:
    if app not in BRANDS:
        return "no brand defined"
    colour, mono = BRANDS[app]
    res = ROOT / app / "mobile/android/app/src/main/res"
    if not res.exists():
        return f"missing {res}"

    for bucket, px in ANDROID.items():
        (res / bucket).mkdir(parents=True, exist_ok=True)
        draw_icon(px, colour, mono, rounded=True).save(res / bucket / "ic_launcher.png")
        # Foreground drawn at 60% so the launcher's mask cannot clip the letters.
        draw_icon(px * 2, colour, mono, rounded=False, scale=0.26).save(
            res / bucket / "ic_launcher_foreground.png")

    (res / "values").mkdir(parents=True, exist_ok=True)
    (res / "values/ic_launcher_background.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'    <color name="ic_launcher_background">{colour}</color>\n</resources>\n')
    (res / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
    (res / "mipmap-anydpi-v26/ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background"/>\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
        '</adaptive-icon>\n')

    ios = ROOT / app / "mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset"
    if ios.exists():
        for name, px in IOS_SIZES:
            # Flattened onto opaque white: the App Store rejects an icon with an
            # alpha channel, and a rounded corner would be double-masked by iOS.
            icon = draw_icon(px, colour, mono, rounded=False)
            Image.alpha_composite(Image.new("RGBA", icon.size, "white"), icon) \
                 .convert("RGB").save(ios / name)
    return "written"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*", default=sorted(BRANDS))
    args = ap.parse_args()
    for app in (args.apps or sorted(BRANDS)):
        print(f"{app:18} {write(app)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
