#!/usr/bin/env python3
"""Generate the 1024x500 Play feature graphic for apps that have none, from the
app's own 1024 launcher icon plus its store name and subtitle (ImageMagick).

    python3 scripts/feature_graphics.py            # missing only
    python3 scripts/feature_graphics.py --force    # regenerate all
"""
import json, pathlib, subprocess, sys, plistlib
ROOT = pathlib.Path("/Users/spatchava/agl"); M = ROOT / "agl-manifest"
FORCE = "--force" in sys.argv
apps = json.load(open(M / "apps.json"))["apps"]
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"; FONT2 = "/System/Library/Fonts/Supplemental/Arial.ttf"
for a in sorted(apps, key=lambda x: x["repo"].lower()):
    repo = a["repo"]; d = ROOT / repo / (a["dir"] if a["dir"] != "." else "")
    out = d / "fastlane/metadata/android/en-US/images/featureGraphic.png"
    if out.exists() and not FORCE: print(f"{repo:18} exists"); continue
    iconset = d / "ios/Runner/Assets.xcassets/AppIcon.appiconset"
    icons = sorted(iconset.glob("*1024*")) or sorted(iconset.glob("*.png"), key=lambda p: p.stat().st_size)[-1:]
    if not icons: print(f"{repo:18} NO ICON"); continue
    sj = M / "store/apps" / f"{repo}.json"; en = json.load(open(sj))["copy"]["en"] if sj.exists() else {}
    name = en.get("title") or en.get("name") or repo; sub = en.get("short_description") or en.get("subtitle") or ""
    if len(sub) > 60: sub = sub[:57].rsplit(" ", 1)[0] + "…"
    out.parent.mkdir(parents=True, exist_ok=True)
    # dominant icon colour for the background, darkened
    col = subprocess.run(["magick", str(icons[0]), "-resize", "1x1!", "-format", "%[pixel:p{0,0}]", "info:"], capture_output=True, text=True).stdout.strip() or "srgb(30,40,60)"
    cmd = ["magick", "-size", "1024x500", f"xc:{col}", "-fill", "rgba(0,0,0,0.45)", "-draw", "rectangle 0,0 1024,500",
           "(", str(icons[0]), "-resize", "300x300", "-alpha", "set", "(", "+clone", "-alpha", "extract", "-draw", "fill black polygon 0,0 0,60 60,0 fill white circle 60,60 60,0", "(", "+clone", "-flip", ")", "-compose", "Multiply", "-composite", "(", "+clone", "-flop", ")", "-compose", "Multiply", "-composite", ")", "-alpha", "off", "-compose", "CopyOpacity", "-composite", ")", "-gravity", "West", "-geometry", "+80+0", "-compose", "Over", "-composite",
           "-gravity", "NorthWest", "-fill", "white", "-font", FONT, "-pointsize", "58" if len(name) <= 22 else "46", "-annotate", "+430+150", name,
           "-fill", "rgba(255,255,255,0.85)", "-font", FONT2, "-pointsize", "30", "-annotate", "+430+250", sub,
           "-fill", "rgba(255,255,255,0.6)", "-pointsize", "22", "-annotate", "+430+320", "American Group LLC",
           str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0 and out.exists()
    dims = subprocess.run(["magick", "identify", "-format", "%wx%h", str(out)], capture_output=True, text=True).stdout if ok else ""
    print(f"{repo:18} {'wrote' if ok else 'FAILED'} {dims} {r.stderr.strip()[:120]}")
