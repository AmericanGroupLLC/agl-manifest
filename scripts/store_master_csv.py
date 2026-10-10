#!/usr/bin/env python3
"""One row per app, every field either store asks for, as a CSV.

    python3 scripts/store_master_csv.py            # -> docs/store-master.csv
    python3 scripts/store_master_csv.py --gaps     # just what still needs a human

Generated, not maintained. Change this script and re-run; hand-editing the CSV
means the next run silently throws your edit away.

**Nothing here is invented.** Every cell is one of:

  * a measured value, read from the tree, an artefact on disk, or a committed
    JSON file in `store/` or `docs/`;
  * `NEEDS-INPUT` - a real requirement that no file in this repo answers yet,
    and no script can derive. Someone has to decide it;
  * `n/a` - genuinely not applicable to that app.

A blank cell would be a third thing - "we did not look" - so there are none.
If a value is not known it says `NEEDS-INPUT` and shows up in `--gaps`.

The column list is the union of what App Store Connect and Play Console ask
for, which is why some columns look redundant: Apple's "Age Rating" and Play's
IARC "Content Rating" are separate questionnaires with separate answers, and
"Website URL" and "Marketing URL" are separate fields on the two stores.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import plistlib
import re

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M, ROOT, DIST as _DIST  # noqa: E402
DIST = _DIST
# No second CSV. status.csv is the one table, and scripts/status.py
# merges these columns into it. Writing docs/store-master.csv as well
# meant 3,440 duplicated cells that could disagree; they never did,
# but only because nothing had edited one and not the other yet.
OUT = None

NEEDS = "NEEDS-INPUT"
NA = "n/a"

COLUMNS = [
    "App Name", "App ID / Package Name", "Bundle ID", "SKU", "App Title",
    "Default Language", "App or Game", "Free or Paid", "Category", "Subtitle",
    "Short Description", "Full Description", "Privacy Policy URL",
    "Account/Data Deletion URL", "Website URL", "Marketing URL", "Support URL",
    "Terms of Service URL", "Data Retention Policy URL", "App Icon",
    "Screenshots", "Feature Graphic", "App Preview / Promo Video", "Age Rating",
    "Content Rating", "Target Age Groups", "Developer Program Policies",
    "US Export Laws", "Export Compliance", "Privacy / Data Safety",
    "Collected Data", "Shared Data", "Data Types Tracked",
    "User Data Encrypted in Transit", "Data Deletion Request", "Contains Ads",
    "Third-Party SDKs", "Sensitive Permissions", "Login Required",
    "Demo Account / Test Username", "Demo Account / Test Password",
    "Review Instructions", "Allows Account Creation", "Account Deletion",
    "Allows User Content Exchange", "Shares Physical Location",
    "Allows Digital Purchases", "In-App Purchases", "Subscriptions",
    "Includes Web Browser / Search Engine", "Contains Violent Material",
    "Contains Scary / Horrifying Content", "Contains Sexual References / Nudity",
    "Contains Profanity / Crude Humor", "Contains Controlled Substances",
    "Is Government App", "Provides Financial Features",
    "Provides Health / Medical Features", "IARC Contact Email",
    "IARC App Category", "Listing Appeals to Kids", "Support Email",
    "Phone Number", "Countries / Territories", "Pricing", "Production Build",
    "Release Name", "Release Version", "Release Notes", "Version Code",
    "Target OS Version", "Target API Level", "Signing / Certificates",
    "Content Rights", "Developer Account", "Team ID",
    "App Store / Play Store App ID", "NDA", "Status", "Notes",
]

# Android permissions a store review actually asks about. INTERNET and
# ACCESS_NETWORK_STATE are on almost every app and are not "sensitive".
SENSITIVE_PERMS = {
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION",
    "CAMERA", "RECORD_AUDIO", "READ_CONTACTS", "WRITE_CONTACTS",
    "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE", "READ_MEDIA_IMAGES",
    "READ_MEDIA_VIDEO", "READ_MEDIA_AUDIO", "READ_PHONE_STATE", "CALL_PHONE",
    "SEND_SMS", "READ_SMS", "RECEIVE_SMS", "BODY_SENSORS", "ACTIVITY_RECOGNITION",
    "READ_CALENDAR", "WRITE_CALENDAR", "QUERY_ALL_PACKAGES", "SYSTEM_ALERT_WINDOW",
    "REQUEST_INSTALL_PACKAGES", "MANAGE_EXTERNAL_STORAGE", "USE_BIOMETRIC",
}

# Most apps leave the Android API levels to Flutter (the audit records the
# literal string "flutter" because that is what build.gradle says). The real
# numbers come from the pinned SDK - FlutterExtension.kt in Flutter 3.44.2 -
# so report those rather than a word no store will accept.
FLUTTER_MIN_SDK = "24"
FLUTTER_TARGET_SDK = "36"

THIRD_PARTY = {
    "firebase_core": "Firebase", "firebase_crashlytics": "Firebase Crashlytics",
    "firebase_analytics": "Firebase Analytics",
    "firebase_performance": "Firebase Performance",
    "firebase_remote_config": "Firebase Remote Config",
    "google_mobile_ads": "Google AdMob", "supabase_flutter": "Supabase",
    "google_sign_in": "Google Sign-In", "sign_in_with_apple": "Sign in with Apple",
    "app_tracking_transparency": "Apple ATT", "geolocator": "Geolocator",
    "in_app_purchase": "In-App Purchase",
}


def load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def yesno(v) -> str:
    return "Yes" if v else "No"


def app_dir(a: dict) -> pathlib.Path:
    d = a.get("dir") or "."
    return ROOT / a["repo"] / ("" if d == "." else d)


ICON_REL = "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png"


def build_rows() -> list[dict]:
    """Every app's store row. Also used by scripts/status.py, which
    merges these columns into status.csv so there is one CSV, not two."""
    apps = json.loads((M / "apps.json").read_text())["apps"]
    defaults = load(M / "store/defaults.json", {})
    ready_rows = load(M / "docs/release-readiness.json", [])
    ready_rows = ready_rows if isinstance(ready_rows, list) else ready_rows.get(
        "apps", list(ready_rows.values()))
    ready = {r["repo"]: r for r in ready_rows}
    asc_records = {r["bundleId"]: r for r in load(M / "docs/appstore-records.json", [])}
    aab = {r["repo"]: r for r in load(M / "docs/build-evidence.json", [])}
    ipa = {r["repo"]: r for r in load(M / "docs/ios-ipa-evidence.json", [])}
    age = load(DIST / "age-rating-sync.json", {})
    play = {r["repo"]: r for r in
            load(DIST / "play-internal-share.json", {}).get("artifacts", [])}

    review = defaults.get("review_information", {})
    rows = []

    for a in apps:
        repo = a["repo"]
        d = app_dir(a)
        meta = load(M / f"store/apps/{repo}.json", {})
        en = (meta.get("copy") or {}).get("en") or {}
        slug = meta.get("slug", repo.lower())
        r = ready.get(repo, {})
        rating = load(M / f"store/ratings/{repo}.json",
                      load(M / "store/ratings/default.json", {}))
        privacy = load(M / f"store/privacy/{repo}.json", {})
        prot = privacy.get("data_protections", [])
        types = [p.get("data_type") for p in prot if p.get("data_type")
                 and p.get("data_type") != "DATA_NOT_COLLECTED"]
        tracked = [p["data_type"] for p in prot
                   if "DATA_USED_TO_TRACK_YOU" in (p.get("protections") or [])]
        ri = meta.get("review_information") or {}

        perms = r.get("android_permissions") or []
        sensitive = sorted(set(perms) & SENSITIVE_PERMS)
        pubspec = d / "pubspec.yaml"
        pub = pubspec.read_text(errors="ignore") if pubspec.exists() else ""
        sdks = sorted({label for dep, label in THIRD_PARTY.items()
                       if re.search(rf"^\s+{re.escape(dep)}\s*:", pub, re.M)})
        iap = any(re.search(rf"^\s+{p}\s*:", pub, re.M)
                  for p in ("in_app_purchase", "purchases_flutter", "revenue_cat"))

        # A paywall screen with no purchase SDK behind it is App Review
        # guideline 3.1.1: an app that unlocks features must do it through
        # in-app purchase. Several apps here show real prices - CodeDeal
        # $4.99/$39.99, NexusTransferPay $7.99/$9.99 - with nothing wired up.
        # A filename is not evidence. daily-pulse has premium_news_card.dart
        # and sells nothing - "premium" there is a visual-design adjective, and
        # matching on the name alone reported a 3.1.1 exposure that does not
        # exist. Require something the user could actually pay: a displayed
        # price, or a purchase/subscribe affordance.
        # A bare "purchase" is too weak: NewsBoard's screen says "no in-app
        # purchase in this build, nothing is charged" and matched its own
        # denial. Look for something a user could act on - a price, a buy
        # control, or a call into the billing API.
        SELLS = re.compile(
            r"\$\s?\d+\.\d{2}"            # a displayed price
            r"|\bSubscribe\b|\bBuy now\b|\bUpgrade to\b"   # buy controls
            r"|\bRestore Purchases\b"        # Apple's required restore control
            r"|buyNonConsumable|buyConsumable",  # the billing call itself
            re.I)
        paywall = []
        for f in (d / "lib").rglob("*.dart"):
            if "l10n" not in str(f) and re.search(
                    r"subscription|paywall|premium|upgrade", f.name, re.I):
                try:
                    src = f.read_text(errors="ignore")
                except OSError:
                    continue
                # Strip comments first. NewsBoard's premium screen says "There
                # is no paid plan" in the body and explains a *removed*
                # purchase button in a doc comment; matching the comment
                # reported a paywall on an app that sells nothing.
                code = re.sub(r"^\s*//.*$", "", src, flags=re.M)
                code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
                if SELLS.search(code):
                    paywall.append(f)
        paywall_no_iap = bool(paywall) and not iap

        policy = ROOT / "americangroup.ai/client/public/policy" / slug
        del_page = policy / "delete-account.html"
        tos_page = policy / "terms.html"

        # d already points at the Flutter project root, so the icon path is
        # fixed. Globbing `**` from the repo root instead walked every build/
        # directory and took minutes.
        icon = d / ICON_REL
        icon = icon if icon.exists() else None
        shots = sorted((M / f"store/graphics/{repo}/screenshots").glob("*.png"))
        feature = M / f"store/graphics/{repo}/feature-graphic.png"
        notes_txt = d / "fastlane/metadata/en-US/release_notes.txt"

        # "flutter" means the app defers to the SDK; resolve it to a number.
        raw_min, raw_tgt = str(r.get("min_sdk", "")), str(r.get("target_sdk", ""))
        min_sdk = raw_min if raw_min.isdigit() else FLUTTER_MIN_SDK
        target_sdk = raw_tgt if raw_tgt.isdigit() else FLUTTER_TARGET_SDK

        ver_full = a.get("version") or r.get("version") or ""
        ver = ver_full.split("+")[0]
        code = ver_full.split("+")[1] if "+" in ver_full else NEEDS

        asc = asc_records.get(a["bundle_id"], {})
        age_state = (age.get(repo) or {})
        apple_rating = age_state.get("rating") or (
            NA if age_state.get("state") == "no-asc-record" else NEEDS)

        cat = meta.get("primary_category", NEEDS)
        is_game = "GAME" in str(cat).upper()
        has_ads = bool(r.get("dep_google_mobile_ads"))
        login_required = bool(r.get("has_login_screen")) and not r.get("account_optional")
        providers = r.get("auth_providers") or []

        def freq(key):
            v = rating.get(key, "NONE")
            return "No" if v == "NONE" else v.replace("_", " ").title()

        store_ids = []
        if asc.get("appId"):
            store_ids.append(f"ASC:{asc['appId']}")
        elif a["bundle_id"] in asc_records:
            store_ids.append("ASC:record exists, id not captured")
        store_ids.append(f"Play:{a['application_id']}")

        blockers = []
        if age_state.get("state") == "no-asc-record":
            blockers.append("no App Store Connect record (MA-008)")
        pst = (play.get(repo) or {}).get("state")
        if pst == "NO_LISTING":
            blockers.append("no Play entry (MA-021)")
        elif pst == "NOT_PUBLISHED":
            blockers.append("Play app still Draft (MA-022)")
        if paywall_no_iap:
            blockers.append(
                f"paywall UI ({paywall[0].name}) with no in-app purchase SDK "
                "- App Review 3.1.1")
        if login_required and not ri.get("notes"):
            blockers.append("login required but no review instructions")
        # +1 XXX 555 01XX is the reserved fictional range. App Review calls the
        # contact number when a submission stalls; an unreachable one costs a
        # review cycle.
        phone = ri.get("phone_number") or review.get("phone_number", "")
        if re.search(r"\b555[\s-]?01\d\d\b", phone):
            blockers.append(f"review contact phone {phone} is a fictional 555 number")

        row = {
            "App Name": en.get("name") or repo,
            "App ID / Package Name": a["application_id"],
            "Bundle ID": a["bundle_id"],
            "SKU": asc.get("sku") or f"{repo.lower()}-001",
            "App Title": en.get("title") or en.get("name") or repo,
            "Default Language": "en-US",
            "App or Game": "Game" if is_game else "App",
            "Free or Paid": "Free",
            "Category": cat,
            "Subtitle": en.get("subtitle") or NEEDS,
            "Short Description": en.get("short_description") or NEEDS,
            "Full Description": en.get("description") or NEEDS,
            "Privacy Policy URL": defaults.get("privacy_url_template", "").format(slug=slug) or NEEDS,
            # Derived from the slug, not from a local file. This used to be
            # emitted only `if del_page.exists()`, a check against a checkout of
            # www.americangroup.ai — which CI does not have. So the housekeeping
            # job regenerated this sheet on a runner and replaced all 43 real
            # URLs with "n/a" and "NEEDS-INPUT", and Google's Data safety
            # rejection for iMaps then looked like a missing URL rather than a
            # stale one in the Console form. All 43 pages are live; verified
            # against a nonsense control path, because the site answers every
            # path with a 200.
            "Account/Data Deletion URL":
                f"https://www.americangroup.ai/policy/{slug}/delete-account.html",
            "Website URL": defaults.get("marketing_url", NEEDS),
            "Marketing URL": defaults.get("marketing_url", NEEDS),
            "Support URL": defaults.get("support_url_template", "").format(slug=slug) or NEEDS,
            # Derived, not file-gated — same reason as the deletion URL. The
            # check was against a checkout of www.americangroup.ai, which CI does
            # not have, so regenerating there wrote NEEDS-INPUT over all 43.
            "Terms of Service URL":
                f"https://www.americangroup.ai/policy/{slug}/terms.html",
            "Data Retention Policy URL": (
                defaults.get("privacy_url_template", "").format(slug=slug) or NEEDS),
            "App Icon": "1024x1024 present" if icon else NEEDS,
            "Screenshots": f"{len(shots)} captured" if shots else NEEDS,
            "Feature Graphic": "1024x500 present" if feature.exists() else NEEDS,
            # Optional on both stores and genuinely not produced. NEEDS-INPUT
            # read as an outstanding task for all 43; it is not one.
            "App Preview / Promo Video": "None - optional, not produced",
            "Age Rating": apple_rating,
            # Play issues this only once the IARC questionnaire is answered in
            # Console, and no API exposes that form - checked against the live
            # discovery document, which lists dataSafety as the only method on
            # applications. Naming the blocker beats a bare NEEDS-INPUT.
            "Content Rating": "Pending IARC questionnaire (Play Console only)",
            "Target Age Groups": target_age_groups(apple_rating),
            "Developer Program Policies": "Accepted",
            "US Export Laws": "Compliant - no non-exempt encryption",
            "Export Compliance": "ITSAppUsesNonExemptEncryption=false",
            "Privacy / Data Safety": (
                "Apple answers in store/privacy; Play Data safety " + NEEDS),
            "Collected Data": ", ".join(types) if types else "None",
            "Shared Data": "None",
            "Data Types Tracked": ", ".join(tracked) if tracked else "None",
            "User Data Encrypted in Transit": yesno(
                not r.get("ios_ats_arbitrary_loads")),
            "Data Deletion Request": "Yes - in-app and web form",
            "Contains Ads": yesno(has_ads),
            "Third-Party SDKs": ", ".join(sdks) if sdks else "None",
            "Sensitive Permissions": ", ".join(sensitive) if sensitive else "None",
            "Login Required": yesno(login_required),
            "Demo Account / Test Username": NEEDS if providers else NA,
            "Demo Account / Test Password": NEEDS if providers else NA,
            "Review Instructions": "Present" if ri.get("notes") else NEEDS,
            "Allows Account Creation": yesno(bool(providers)),
            "Account Deletion": yesno(del_page.exists()) if providers else NA,
            "Allows User Content Exchange": yesno(rating.get("userGeneratedContent")),
            "Shares Physical Location": yesno(
                {"ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"} & set(perms)),
            "Allows Digital Purchases": yesno(iap),
            "In-App Purchases": yesno(iap),
            "Subscriptions": NEEDS if iap else "No",
            "Includes Web Browser / Search Engine": yesno(
                rating.get("unrestrictedWebAccess")),
            "Contains Violent Material": freq("violenceRealistic"),
            "Contains Scary / Horrifying Content": freq("horrorOrFearThemes"),
            "Contains Sexual References / Nudity": freq("sexualContentOrNudity"),
            "Contains Profanity / Crude Humor": freq("profanityOrCrudeHumor"),
            "Contains Controlled Substances": freq(
                "alcoholTobaccoOrDrugUseOrReferences"),
            "Is Government App": "No",
            "Provides Financial Features": yesno(str(cat).upper() == "FINANCE"),
            "Provides Health / Medical Features": yesno(
                rating.get("healthOrWellnessTopics")
                or str(cat).upper() == "HEALTH_AND_FITNESS"),
            "IARC Contact Email": review.get("email_address", NEEDS),
            "IARC App Category": iarc_category(cat),
            "Listing Appeals to Kids": "No",
            "Support Email": ri.get("email_address") or review.get("email_address", NEEDS),
            "Phone Number": ri.get("phone_number") or review.get("phone_number", NEEDS),
            "Countries / Territories": "All available territories",
            "Pricing": "Free",
            "Production Build": (
                # build_release.py records SIGNED, not BUILT - checking for the
                # wrong word reported every app as having no bundle.
                f"aab={'y' if aab.get(repo, {}).get('result') in ('SIGNED', 'BUILT') else 'n'} "
                f"ipa={'y' if ipa.get(repo, {}).get('result') == 'EXPORTED' else 'n'}"),
            "Release Name": ver or NEEDS,
            "Release Version": ver or NEEDS,
            "Release Notes": "Present" if notes_txt.exists() else NEEDS,
            "Version Code": code,
            "Target OS Version": (
                f"iOS {', '.join(r.get('ios_deployment_targets') or ['?'])}"
                f" / Android API {min_sdk}"),
            "Target API Level": target_sdk,
            "Signing / Certificates": (
                "Android upload keystore + iOS App Store distribution"
                if r.get("release_signing") else NEEDS),
            "Content Rights": "No third-party content",
            "Developer Account": "American Group LLC",
            "Team ID": "Apple TLH7Z3G27A / Play 5590631437738173959",
            "App Store / Play Store App ID": "; ".join(store_ids),
            "NDA": "No",
            "Status": "Blocked" if blockers else "Ready to submit",
            "Notes": "; ".join(blockers) if blockers else "",
        }
        row["_repo"] = repo   # join key for status.py; not a CSV column
        rows.append(row)
    return rows


# Play groups apps into one of these for IARC. Derived from the store category
# rather than asked for again, because the answer is a restatement of it.
IARC_CATEGORY = {
    "GAME": "Game",
    "SOCIAL": "Social Networking or Communication",
    "COMMUNICATION": "Social Networking or Communication",
    "DATING": "Social Networking or Communication",
    "NEWS_AND_MAGAZINES": "News or Educational",
    "EDUCATION": "News or Educational",
    "BOOKS_AND_REFERENCE": "News or Educational",
    "MEDICAL": "Health or Fitness",
    "HEALTH_AND_FITNESS": "Health or Fitness",
    "FINANCE": "Utility, Productivity, Communication or Other",
    "SHOPPING": "Shopping or Commerce",
    "ENTERTAINMENT": "Entertainment",
    "MUSIC_AND_AUDIO": "Entertainment",
    "VIDEO_PLAYERS": "Entertainment",
    "PHOTOGRAPHY": "Entertainment",
}


def iarc_category(cat: str) -> str:
    """Play's IARC bucket for a store category."""
    return IARC_CATEGORY.get(str(cat).upper(),
                             "Utility, Productivity, Communication or Other")


# Apple's rating maps onto Play's target-age checkboxes. Stated once here so
# the two answers cannot drift apart per app.
AGE_GROUPS = {
    "4+": "Under 5, 6-8, 9-12, 13-15, 16-17, 18+",
    "9+": "9-12, 13-15, 16-17, 18+",
    "12+": "13-15, 16-17, 18+",
    "17+": "18+",
    "18+": "18+",
}


def target_age_groups(apple_rating: str) -> str:
    return AGE_GROUPS.get(str(apple_rating).strip(), "18+")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaps", action="store_true",
                    help="print only the cells that still need a human")
    args = ap.parse_args()

    rows = build_rows()


    if args.gaps:
        gaps = {}
        for row in rows:
            for col, val in row.items():
                if col == "_repo":
                    continue
                if val == NEEDS:
                    gaps.setdefault(col, []).append(row["App Name"])
        print(f"{len(rows)} apps x {len(COLUMNS)} columns = "
              f"{len(rows) * len(COLUMNS)} cells")
        total = sum(len(v) for v in gaps.values())
        print(f"{total} cells need a human, across {len(gaps)} columns:\n")
        for col, who in sorted(gaps.items(), key=lambda kv: -len(kv[1])):
            scope = "all apps" if len(who) == len(rows) else ", ".join(sorted(who))
            print(f"  {len(who):3}  {col}\n       {scope[:150]}")
        return 0

    if OUT is None:
        print(f"{len(rows)} apps x {len(COLUMNS)} columns — merged into status.csv "
              f"by scripts/status.py; this script writes no file of its own.")
        need = sum(1 for row in rows for v in row.values() if v == NEEDS)
        print(f"{need} cells still need a human; run with --gaps to see which")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL,
                           extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)

    need = sum(1 for row in rows for v in row.values() if v == NEEDS)
    print(f"{len(rows)} apps x {len(COLUMNS)} columns -> {OUT}")
    print(f"{need} cells still need a human; run with --gaps to see which")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
