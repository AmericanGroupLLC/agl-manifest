#!/usr/bin/env python3
"""Replace placeholder app icons with real, app-appropriate artwork.

Twenty apps shipped an auto-generated two-letter monogram on a flat gradient —
a placeholder that the previous generator produced, not a logo. One of them,
PlantPulse, shipped the wrong initials entirely ("OC"). This writes a proper
pictogram icon instead: a Material Icons glyph chosen per app, over a
per-app two-colour gradient.

Material Icons ships with the Flutter SDK, so the glyphs are real, professionally
drawn pictograms rather than shapes hand-plotted with PIL primitives.

What it writes per app:
  iOS      every size declared in the app's own AppIcon Contents.json, RGB with
           no alpha channel (Apple rejects icons that have one)
  Android  legacy ic_launcher at five densities, a genuinely circular
           ic_launcher_round, an adaptive foreground inset into the safe zone,
           and the mipmap-anydpi-v26 XML that ties them together

Apps with real artwork are never touched; the app list here is explicit.

    python3 make_icons.py --list
    python3 make_icons.py --only PlantPulse
    python3 make_icons.py
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST, flutter_sdk  # noqa: E402
FONT = flutter_sdk() / "bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf"
def _codepoints() -> dict[str, int]:
    """Parse name -> codepoint straight out of the Flutter SDK.

    An earlier version read a hand-made cache file that nothing generated, so
    the script only worked on the machine where that file happened to exist.
    icons.dart is the source of truth and ships with the SDK.
    """
    src = (flutter_sdk() / "packages/flutter/lib/src/material/icons.dart").read_text()
    pairs = re.findall(r"static const IconData ([a-z_0-9]+) = IconData\(0x([0-9a-f]+)", src)
    return {k: int(v, 16) for k, v in pairs
            if not k.endswith(("_outlined", "_rounded", "_sharp"))}


CODEPOINTS = _codepoints()

# app -> (Material Icons glyph, gradient start, gradient end)
# Colours are chosen per app rather than generated from a hash, so that related
# apps do not collide and each reads as a deliberate brand.
DESIGN: dict[str, tuple[str, str, str]] = {
    "AeroSwift":       ("flight",             "#0B3D91", "#1E88E5"),
    # AGCleaner is not listed: its card-merge icon is drawn by
    # AGCleaner/scripts/generate_card_mark_icons.py, and a run of this script must not replace it.
    # AGRecorder is not listed: its icon is drawn by AGRecorder/tool/draw_icon.py
    # (waveform and flag on paper), and a run of this script must not replace it.
    "AGStudio":        ("auto_awesome",       "#4A148C", "#AB47BC"),
    "ApexMarketWatch": ("candlestick_chart",  "#0D2818", "#2E7D32"),
    # BuddyPlay is not listed: its two-pawns-on-felt-in-a-brass-ring icon is drawn by
    # BuddyPlay/mobile/tool/draw_icon.py, and a run of this script must not replace it.
    "CarDeal":         ("directions_car",     "#263238", "#546E7A"),
    # ChefCount is not listed: its skillet-and-countdown icon is drawn by
    # ChefCount/tool/draw_icon.py, and a run of this script must not replace it.
    # EventSpark is not listed: its ticket-stub-and-check-stamp icon is drawn by
    # EventSpark/mobile/tool/draw_icon.py, and a run of this script must not replace it.
    # GadgetNest is not listed: its phone-and-countdown icon is drawn by
    # GadgetNest/tool/draw_icon.py, and a run of this script must not replace it.
    # HomeWise is not listed: its house-on-a-dimension-line icon is drawn by
    # HomeWise/mobile/tool/draw_icon.py, and a run of this script must not replace it.
    # MileMaster is not listed: its road-and-mile-marker-on-a-logbook-page icon is
    # drawn by MileMaster/tool/draw_icon.py, and a run of this script must not replace it.
    "MyCard":          ("credit_card",        "#212121", "#616161"),
    # MyFinance is not listed: its ledger-sheet-and-runway icon is drawn by
    # MyFinance/tool/draw_icon.py, and a run of this script must not replace it.
    "NearServe":       ("handyman",           "#E65100", "#FFA726"),
    "PlantPulse":      ("local_florist",      "#1B5E20", "#7CB342"),
    "portfolio-board": ("dashboard",          "#37474F", "#78909C"),
    "RideZap":         ("electric_bolt",      "#F57F17", "#FFCA28"),
    "RoomCraft":       ("weekend",            "#4E342E", "#A1887F"),
    # WiFiTrail is not listed: its dashed-trail-and-signal-dot icon is drawn by
    # WiFiTrail/tool/draw_icon.py, and a run of this script must not replace it.
}

DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
# Adaptive icons are a 108dp canvas of which only the middle 72dp is guaranteed
# visible; anything outside is cropped by the launcher's mask. The nine apps
# with full-bleed foregrounds were being clipped for exactly this reason.
ADAPTIVE = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
SAFE_FRACTION = 0.62


def rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(size: int, c0: str, c1: str) -> Image.Image:
    """Diagonal two-colour gradient, drawn once at full size."""
    a, b = rgb(c0), rgb(c1)
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px[x, y] = (round(a[0] + (b[0] - a[0]) * t),
                        round(a[1] + (b[1] - a[1]) * t),
                        round(a[2] + (b[2] - a[2]) * t))
    return img


def glyph_layer(size: int, glyph: str, frac: float) -> Image.Image:
    """White glyph on transparency, centred, occupying `frac` of the canvas."""
    if glyph not in CODEPOINTS:
        raise KeyError(f"unknown Material Icons glyph: {glyph}")
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    font = ImageFont.truetype(str(FONT), max(8, int(size * frac)))
    ImageDraw.Draw(layer).text((size / 2, size / 2), chr(CODEPOINTS[glyph]),
                               font=font, fill=(255, 255, 255, 255), anchor="mm")
    return layer


def master(glyph: str, c0: str, c1: str, size: int = 1024) -> Image.Image:
    base = gradient(size, c0, c1)
    base.paste(glyph_layer(size, glyph, 0.52), (0, 0), glyph_layer(size, glyph, 0.52))
    return base


def circular(src: Image.Image, size: int) -> Image.Image:
    """A round icon that is actually round — several apps shipped a square copy."""
    out = src.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    out.putalpha(mask.resize((size, size), Image.LANCZOS))
    return out


def app_dir(repo: str, apps: list[dict]) -> pathlib.Path:
    a = next(x for x in apps if x["repo"] == repo)
    d = a.get("dir", ".") or "."
    return ROOT / repo if d == "." else ROOT / repo / d


def write_ios(d: pathlib.Path, m: Image.Image, report: dict) -> None:
    iconset = d / "ios/Runner/Assets.xcassets/AppIcon.appiconset"
    cj = iconset / "Contents.json"
    if not cj.exists():
        report["ios"] = "no Contents.json"
        return
    meta = json.loads(cj.read_text())
    n = 0
    for entry in meta.get("images", []):
        fn = entry.get("filename")
        if not fn:
            continue
        w = float(entry["size"].split("x")[0]) * float(entry["scale"].rstrip("x"))
        px = max(1, int(round(w)))
        # Convert to RGB: an App Store icon with an alpha channel is rejected.
        m.resize((px, px), Image.LANCZOS).convert("RGB").save(iconset / fn, "PNG")
        n += 1
    report["ios"] = f"{n} sizes"


def write_android(d: pathlib.Path, m: Image.Image, c0: str, c1: str,
                  glyph: str, report: dict) -> None:
    res = d / "android/app/src/main/res"
    if not res.exists():
        report["android"] = "no res/"
        return
    made = 0
    for dens, px in DENSITIES.items():
        out = res / f"mipmap-{dens}"
        out.mkdir(parents=True, exist_ok=True)
        m.resize((px, px), Image.LANCZOS).convert("RGB").save(out / "ic_launcher.png", "PNG")
        circular(m, px).save(out / "ic_launcher_round.png", "PNG")
        made += 2
    for dens, px in ADAPTIVE.items():
        out = res / f"mipmap-{dens}"
        out.mkdir(parents=True, exist_ok=True)
        # Foreground: glyph only, inside the safe zone, transparent elsewhere.
        glyph_layer(px, glyph, 0.52 * SAFE_FRACTION).save(
            out / "ic_launcher_foreground.png", "PNG")
        gradient(px, c0, c1).convert("RGB").save(out / "ic_launcher_background.png", "PNG")
        made += 2

    anydpi = res / "mipmap-anydpi-v26"
    anydpi.mkdir(parents=True, exist_ok=True)
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
           '    <background android:drawable="@mipmap/ic_launcher_background"/>\n'
           '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
           '    <monochrome android:drawable="@mipmap/ic_launcher_foreground"/>\n'
           '</adaptive-icon>\n')
    (anydpi / "ic_launcher.xml").write_text(xml)
    (anydpi / "ic_launcher_round.xml").write_text(xml)
    report["android"] = f"{made} files + adaptive xml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for k, (g, a, b) in sorted(DESIGN.items()):
            print(f"{k:<18} {g:<20} {a} -> {b}")
        return 0

    apps = json.loads((MANIFEST / "apps.json").read_text())["apps"]
    todo = [args.only] if args.only else sorted(DESIGN)
    for repo in todo:
        glyph, c0, c1 = DESIGN[repo]
        d = app_dir(repo, apps)
        report: dict[str, str] = {}
        m = master(glyph, c0, c1)
        (ROOT / ".dist/app-icons").mkdir(exist_ok=True)
        m.save(ROOT / f".dist/app-icons/{repo}.png", "PNG")
        write_ios(d, m, report)
        write_android(d, m, c0, c1, glyph, report)
        print(f"{repo:<18} {glyph:<20} ios={report.get('ios')} android={report.get('android')}",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
