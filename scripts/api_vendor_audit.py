#!/usr/bin/env python3
"""Every build-time credential the apps read, per app, and whether a release build gets it.

    python3 scripts/api_vendor_audit.py          # -> docs/api-vendor-keys.json

Scans each app's lib/ for `String.fromEnvironment('<KEY>')` whose name looks
like a credential or partner id (API keys, client ids/secrets, affiliate
markers and tags). AdMob unit ids and Supabase are excluded — those are
handled by admob_defines() and committed config.

`passed_by_release_build` is measured against what the delivery path really
passes: build_release.py and build_ipa.py add only admob_defines(), and
ship.yml holds no third-party secret. So a key with no default is empty in
every shipped build, and the feature behind it is off.

Read-only and local: no network, no secrets read. The signup list that
explains each vendor is docs/API_VENDORS_AND_AFFILIATES.md.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

OUT = M / "docs/api-vendor-keys.json"
USAGE_OUT = M / "docs/api-vendor-usage.json"

# Candidate vendors (the founder's directory, 2026-10-12, plus what the apps
# already call). Each maps to lowercase fragments searched in non-comment Dart
# lines and pubspec.yaml. A hit means the app names the vendor in code; it
# does not prove a live integration — the key table says whether it can work.
VENDORS = {
    # travel
    "Amadeus": ["amadeus"], "Duffel": ["duffel"], "Travelport": ["travelport"], "Sabre": ["sabre.com", "sabre "],
    "Kiwi.com Tequila": ["tequila.kiwi", "kiwi.com"], "Skyscanner": ["skyscanner"],
    "Travelpayouts": ["travelpayouts", ".tp.st", "tp.media"], "Expedia Group": ["expedia"],
    "Booking.com": ["booking.com"], "Hotelbeds": ["hotelbeds"], "Agoda": ["re:agoda\\.com"], "CarTrawler": ["cartrawler"],
    "Rentalcars.com": ["rentalcars"], "DiscoverCars": ["discovercars"], "VIPCars": ["vipcars"], "Busbud": ["busbud"],
    "Distribusion": ["distribusion"], "Omio": ["omio"], "Wanderu": ["wanderu"], "Rome2Rio": ["rome2rio"],
    "Trainline": ["trainline"], "Viator": ["viator"], "GetYourGuide": ["getyourguide"],
    "Welcome Pickups": ["welcomepickups"], "Jayride": ["jayride"], "HomeToGo": ["hometogo"],
    "Cover Genius": ["covergenius"], "Allianz Partners": ["allianz"], "Airalo": ["airalo"], "Holafly": ["holafly"],
    "Dragonpass": ["dragonpass"], "LoungeKey": ["loungekey"], "Bounce": ["usebounce", "bounce.com"],
    "Radical Storage": ["radicalstorage"],
    # aviation
    "FlightAware AeroAPI": ["flightaware", "aeroapi"], "ADS-B Exchange": ["adsbexchange"],
    "OpenSky Network": ["opensky-network"], "Airplanes.Live": ["airplanes.live"], "Cirium": ["cirium"],
    "Aviationstack": ["aviationstack"], "AviationWeather.gov": ["aviationweather.gov"],
    "NOAA / weather.gov": ["noaa.gov", "api.weather.gov"], "CheckWX": ["checkwx"],
    "OpenWeather": ["openweathermap"], "Tomorrow.io": ["tomorrow.io"], "FAA": ["faa.gov"], "eCFR": ["ecfr.gov"],
    "FAASTeam": ["faasafety.gov"], "FAA DroneZone": ["faadronezone"], "NTSB": ["ntsb.gov"],
    "NASA ASRS": ["asrs.arc.nasa.gov"], "OurAirports": ["ourairports"], "OpenAIP": ["openaip"],
    "ForeFlight": ["foreflight"], "Garmin": ["garmin.com"], "Rotate Pilot": ["rotatepilot.com"],
    "Open-Meteo": ["open-meteo.com"],
    # shared infrastructure
    "Supabase": ["supabase"], "Firebase": ["firebase"], "Auth0": ["auth0"], "Stripe": ["re:flutter_stripe|stripe\\.com|stripe\\.instance"],
    "RevenueCat": ["revenuecat", "purchases_flutter"], "OpenAI": ["openai.com", "openai_"],
    "Google AI (Gemini)": ["generativelanguage.googleapis", "google_generative_ai", "gemini"],
    "Anthropic": ["anthropic.com"], "Google Maps Platform": ["maps.googleapis.com", "google_maps_flutter", "places.googleapis"],
    "Mapbox": ["mapbox"], "Resend": ["resend.com"], "SendGrid": ["sendgrid"],
    "Firebase Cloud Messaging": ["re:package:firebase_messaging|^\\s*firebase_messaging:"], "Sentry": ["re:sentry_flutter|sentry\\.io|sentry_dsn"], "PostHog": ["posthog"],
    "Cloudflare": ["cloudflare"],
    # commerce / affiliate
    "Rakuten Advertising": ["rakuten"], "Awin": ["awin.com", "'awin'", "awin1.com"], "CJ Affiliate": ["cj.com", "anrdoezrs", "dpbolvw", "jdoqocy", "tkqlhce"],
    "Impact": ["impact.com", "pxf.io", "sjv.io"], "Amazon Associates": ["re:amazon\\.[a-z.]+/|[?&]tag=|tag=\\$|tag=[a-z0-9-]+-2[0-9]|amazon associates"],
    "eBay Partner Network": ["ebay.com", "campid"], "Best Buy": ["bestbuy"], "Walmart": ["walmart"],
    "ShareASale": ["shareasale"], "FlexOffers": ["flexoffers"],
    # other categories
    "Ticketmaster": ["ticketmaster"], "Eventbrite": ["eventbrite"], "NewsAPI": ["newsapi.org"], "GNews": ["gnews.io"],
    "Finnhub": ["finnhub"], "Polygon.io": ["polygon.io"], "Alpha Vantage": ["alphavantage"], "SEC EDGAR": ["sec.gov"],
    "Spoonacular": ["spoonacular"], "Edamam": ["edamam"], "Kroger": ["kroger"], "Instacart": ["instacart"],
    "Nutritionix": ["nutritionix"], "FatSecret": ["fatsecret"], "Veryfi": ["veryfi"], "Yelp Fusion": ["yelp"],
    "Foursquare": ["foursquare"], "RapidAPI": ["rapidapi"], "USDA FoodData Central": ["api.nal.usda.gov"],
    "NREL / NLR alt-fuel": ["developer.nlr.gov", "developer.nrel.gov"], "Open Charge Map": ["openchargemap"],
    "NASA FIRMS": ["firms.modaps"], "Agora": ["re:agora_rtc|agora\\.io|agora_app_id"], "YouTube Data API": ["youtube.googleapis", "youtube/v3"],
    "Pexels": ["pexels"], "Pixabay": ["pixabay"], "DoorDash": ["doordash"], "Uber Eats": ["ubereats"],
    "Grubhub": ["grubhub"], "Uber": ["uber.com"], "Lyft": ["lyft.com"],
}
DEFINE = re.compile(r"(?:String|bool|int)\.fromEnvironment\(\s*'([A-Z0-9_]+)'\s*"
                    r"(?:,\s*defaultValue:\s*(?:'([^']*)'|([^\)]+)))?", re.S)
CREDENTIAL = re.compile(r"KEY|TOKEN|SECRET|CLIENT_ID|APP_ID|AFFILIATE|_TAG|PARTNER|PUBLISHER|"
                        r"TRACKING|CAMPAIGN|_SID|DSN|USERNAME|PASSWORD|_ID$|ACCOUNT|MERCHANT|"
                        r"REFERRAL|AFF_|MARKER")
NOT_VENDOR = re.compile(r"^(ADMOB_|SUPABASE_|FLAVOR$|APP_ENV$|BACKEND|SCREENSHOT$|ENV$|"
                        r"API_BASE_URL$|API_URL$|USE_|ENABLE_|DEBUG|IAP_)")


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())["apps"]
    passed = set()  # nothing beyond ADMOB_* reaches a release build today
    report = {}
    for a in apps:
        lib = ROOT / a["repo"] / (a.get("dir") or ".") / "lib"
        keys: dict[str, dict] = {}
        for f in sorted(lib.rglob("*.dart")):
            text = f.read_text(errors="ignore")
            for m in DEFINE.finditer(text):
                k = m.group(1)
                if NOT_VENDOR.search(k) or not CREDENTIAL.search(k):
                    continue
                default = m.group(2) if m.group(2) is not None else (m.group(3) or "").strip()
                rec = keys.setdefault(k, {"default": None, "sites": []})
                if default and default not in ("''", '""'):
                    rec["default"] = default
                line = text[:m.start()].count("\n") + 1
                rec["sites"].append(f"{f.relative_to(ROOT / a['repo'])}:{line}")
        for k, rec in keys.items():
            rec["passed_by_release_build"] = k in passed
            rec["effective_in_release"] = ("default" if rec["default"] else "EMPTY")
        report[a["repo"]] = keys
    OUT.write_text(json.dumps({"apps": report}, indent=1) + "\n")

    usage: dict[str, dict[str, str]] = {v: {} for v in VENDORS}
    for a in apps:
        base = ROOT / a["repo"] / (a.get("dir") or ".")
        files = sorted((base / "lib").rglob("*.dart")) + [base / "pubspec.yaml"]
        for f in files:
            if not f.exists():
                continue
            for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                s = line.strip()
                if s.startswith("//") or s.startswith("#"):
                    continue
                low = re.sub(r"(?<![:/])//.*$", "", s).lower()
                for vendor, frags in VENDORS.items():
                    if a["repo"] not in usage[vendor] and any(
                            re.search(fr[3:], low) if fr.startswith("re:") else fr in low for fr in frags):
                        usage[vendor][a["repo"]] = f"{f.relative_to(ROOT / a['repo'])}:{i}"
    USAGE_OUT.write_text(json.dumps({"vendors": usage}, indent=1) + "\n")
    print(f"  {sum(1 for v in usage.values() if v)} of {len(usage)} candidate vendors are named "
          f"in app code; -> {USAGE_OUT}")
    distinct = {k for v in report.values() for k in v}
    empty = {k for v in report.values() for k, r in v.items() if not r["default"]}
    print(f"  {len(distinct)} credential keys across {sum(1 for v in report.values() if v)} apps; "
          f"{len(empty)} are empty in every release build")
    print(f"  -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
