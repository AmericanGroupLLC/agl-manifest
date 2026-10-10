#!/usr/bin/env python3
"""Generate the website's mobile-app pages from what the stores actually hold.

    python3 scripts/website_apps.py            # -> americangroup.ai/client/src/data/mobileApps.generated.ts
    python3 scripts/website_apps.py --check    # report only; exit 1 if the site would change

Every app's marketing page should promote the app — truthfully. Measured on
2026-10-08, the site did neither:

  - 17 of the 43 apps had no page of their own;
  - the detail pages that existed were mostly synthesised by
    generateFallbackProduct (the site's own test says "49 of 58"), which gives
    every slug the same invented claims: status "Live", "AI-Powered",
    "end-to-end encryption by design";
  - 16 apps were labelled "Live" while live on neither store;
  - the download buttons that existed pointed at https://apps.apple.com and
    https://play.google.com/store — the store home pages, not the app.

So the content is generated, not written, from the sources that are true:

  copy        store/apps/<repo>.json — the App Store description and subtitle,
              already reviewed for accuracy; its UPPERCASE section headings
              become the feature cards
  status      docs/play-production-blockers.json (Play) and
              docs/asc-build-state.json (Apple) — "Live" only when a store
              actually sells it, "Beta" otherwise (every app is on TestFlight
              and Firebase App Distribution)
  store links Play: only for apps live in production, and only after the
              listing page answers HTTP 200. Apple: only for READY_FOR_SALE,
              built from the numeric app id asc_build_state.rb records

Nothing is invented: no ratings, no download counts, no stats. An app with
no live listing simply has no download button.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

SITE = ROOT / "americangroup.ai"
OUT = SITE / "client/src/data/mobileApps.generated.ts"

# The site's own ProductCategory vocabulary.
CATEGORY = {
    "FINANCE": "Finance & Fintech", "BUSINESS": "Enterprise & Security",
    "HEALTH_AND_FITNESS": "Health & Wellness", "MEDICAL": "Health & Wellness",
    "TRAVEL": "Travel & Aviation", "NAVIGATION": "Travel & Aviation",
    "PRODUCTIVITY": "Productivity & Tools", "UTILITIES": "Productivity & Tools",
    "ENTERTAINMENT": "Entertainment & Gaming", "GAMES": "Entertainment & Gaming",
    "MUSIC": "Entertainment & Gaming", "PHOTO_AND_VIDEO": "Entertainment & Gaming",
    "SHOPPING": "E-Commerce & Deals", "FOOD_AND_DRINK": "E-Commerce & Deals",
    "LIFESTYLE": "Social & Communication", "SOCIAL_NETWORKING": "Social & Communication",
    "NEWS": "Social & Communication", "EDUCATION": "Education & Learning",
}
ICON = {
    "Finance & Fintech": "💳", "Enterprise & Security": "🏢", "Health & Wellness": "❤️",
    "Travel & Aviation": "✈️", "Productivity & Tools": "🛠️",
    "Entertainment & Gaming": "🎵", "E-Commerce & Deals": "🛒",
    "Social & Communication": "💬", "Education & Learning": "📘",
}
COLOR = {
    "Finance & Fintech": "#10B981", "Enterprise & Security": "#64748B",
    "Health & Wellness": "#EF4444", "Travel & Aviation": "#0EA5E9",
    "Productivity & Tools": "#6366F1", "Entertainment & Gaming": "#A855F7",
    "E-Commerce & Deals": "#F59E0B", "Social & Communication": "#EC4899",
    "Education & Learning": "#14B8A6",
}


def load(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text())
    except Exception:
        return default


def norm(x: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


def site_slugs() -> dict[str, str]:
    """normalised slug or name -> the slug the site already uses."""
    src = (SITE / "client/src/data/products.ts").read_text()
    out = {}
    for slug, name in re.findall(r'slug:\s*"([^"]+)",\s*name:\s*"([^"]+)"', src):
        out.setdefault(norm(slug), slug)
        out.setdefault(norm(name), slug)
    return out


def features_from(description: str) -> list[dict]:
    """UPPERCASE heading + the paragraph under it -> one feature card."""
    feats = []
    blocks = [b.strip() for b in description.split("\n\n") if b.strip()]
    for b in blocks:
        head, _, body = b.partition("\n")
        h = head.strip()
        # "CONVERT (10 categories)": judge case outside the parentheses only.
        bare = re.sub(r"\(.*?\)", "", h).strip()
        if body and bare and bare.isupper() and 2 < len(h) < 60 and not h.endswith("."):
            paren = h[len(bare):].strip() if h.startswith(bare) else ""
            title = (bare.title().replace("'S", "'s") + (" " + paren if paren else "")).strip()
            text = re.sub(r"\s+", " ", body).strip()
            if len(text) > 260:
                cut = text[:260].rsplit(". ", 1)[0]
                text = cut + "." if cut else text[:257] + "…"
            feats.append({"title": title, "description": text})
    return feats[:6]


def url_ok(url: str) -> bool:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-m", "25", "-L",
                        "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip() == "200"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    apps = json.loads((M / "apps.json").read_text())["apps"]
    asc = {r["repo"]: r for r in load(M / "docs/asc-build-state.json", [])}
    play = {r["repo"]: r for r in load(M / "docs/play-production-blockers.json", {}).get("apps", [])}
    known = site_slugs()

    listings = []
    for a in apps:
        repo = a["repo"]
        rec = load(M / f"store/apps/{repo}.json", {})
        en = (rec.get("copy") or {}).get("en") or {}
        if not en.get("description"):
            print(f"  {repo:16} no store description — skipped")
            continue
        slug = next((known[k] for k in (norm(repo), norm(rec.get("slug") or ""), norm(en.get("name") or ""))
                     if k and k in known), None) or (rec.get("slug") or repo).lower()
        cat = CATEGORY.get(rec.get("primary_category") or "", "Productivity & Tools")

        pkg = a.get("application_id") or (play.get(repo) or {}).get("package")
        play_live = (play.get(repo) or {}).get("state") == "LIVE_PRODUCTION"
        play_url = f"https://play.google.com/store/apps/details?id={pkg}" if (play_live and pkg) else None
        if play_url and not url_ok(play_url):
            print(f"  {repo:16} Play says live but the listing did not answer 200 — no link")
            play_url = None
        a_rec = asc.get(repo) or {}
        apple_live = a_rec.get("review_state") == "READY_FOR_SALE"
        app_url = (f"https://apps.apple.com/app/id{a_rec['apple_id']}"
                   if apple_live and a_rec.get("apple_id") else None)
        if app_url and not url_ok(app_url):
            app_url = None

        desc = en["description"]
        first = desc.split("\n\n", 1)[0].strip()
        listings.append({
            "repo": repo, "slug": slug, "name": en.get("name") or repo,
            "tagline": en.get("subtitle") or "",
            "description": first,
            "longDescription": desc.strip(),
            "category": cat, "icon": ICON[cat], "color": COLOR[cat],
            "features": features_from(desc),
            "tags": [k.strip() for k in (en.get("keywords") or "").split(",") if k.strip()][:8],
            "status": "Live" if (play_url or app_url) else "Beta",
            "appStoreUrl": app_url, "playStoreUrl": play_url,
            "hasCuratedPage": norm(slug) in {norm(s) for s in known.values()},
        })

    body = (
        "// GENERATED by agl-manifest/scripts/website_apps.py — do not edit by hand.\n"
        "// Copy comes from each app's App Store listing; status and store links come\n"
        "// from what Apple and Google actually report. Regenerate instead of editing.\n\n"
        "export interface MobileAppListing {\n"
        "  repo: string;\n  slug: string;\n  name: string;\n  tagline: string;\n"
        "  description: string;\n  longDescription: string;\n  category: string;\n"
        "  icon: string;\n  color: string;\n"
        "  features: { title: string; description: string }[];\n  tags: string[];\n"
        "  status: \"Live\" | \"Beta\";\n  appStoreUrl: string | null;\n"
        "  playStoreUrl: string | null;\n  hasCuratedPage: boolean;\n}\n\n"
        "export const mobileAppListings: MobileAppListing[] = "
        + json.dumps(listings, indent=2, ensure_ascii=False) + ";\n\n"
        "export const mobileAppBySlug: Record<string, MobileAppListing> =\n"
        "  Object.fromEntries(mobileAppListings.map(a => [a.slug, a]));\n"
    )
    # Format with the site's own Prettier, so the file written — and the
    # file --check compares against — is byte-for-byte what gets committed.
    # Without this, formatting the committed file made --check report the
    # site stale on every scheduled pass.
    fmt = subprocess.run(["npx", "--no-install", "prettier", "--stdin-filepath", str(OUT)],
                         input=body, capture_output=True, text=True, cwd=SITE)
    if fmt.returncode == 0 and fmt.stdout:
        body = fmt.stdout
    else:
        print("  prettier unavailable — writing unformatted output")
    live = sum(1 for l in listings if l["status"] == "Live")
    print(f"  {len(listings)} apps: {live} live with a verified store link, "
          f"{len(listings) - live} beta; "
          f"{sum(1 for l in listings if not l['hasCuratedPage'])} had no catalog entry")
    print(f"  feature cards from store copy: "
          f"{sum(len(l['features']) for l in listings)} across "
          f"{sum(1 for l in listings if l['features'])} apps")
    if args.check:
        same = OUT.exists() and OUT.read_text() == body
        print("  site is current" if same else "  site would change")
        return 0 if same else 1
    OUT.write_text(body)
    print(f"  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
