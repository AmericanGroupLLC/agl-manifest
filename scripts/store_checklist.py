#!/usr/bin/env python3
"""Produce a per-app store submission checklist, measured rather than asserted.

Every row is a real check against the tree, the store records, or an artefact on
disk. Nothing here is a judgement about whether the app is *good*; it is whether
each concrete thing a store demands is present. Items a machine cannot settle
(age rating questionnaires, Firebase console downloads, an Apple ID login) are
listed as HUMAN so they are visible rather than silently missing.

    python3 scripts/store_checklist.py            # -> docs/store-checklist.json
    python3 scripts/store_checklist.py --app Verba
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import plistlib
import re
import subprocess
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as _MANIFEST, ROOT as _ROOT  # noqa: E402

ROOT = _ROOT
MANIFEST_DIR = _MANIFEST
DIST = ROOT / ".dist"
SWEEP = ROOT / ".sweep"

# The stock Flutter placeholder icon, by content hash of the 1024 slot.
FLUTTER_DEFAULT_ICON = "7770183009e9"

OK, NO, HUMAN, NA = "PASS", "FAIL", "HUMAN", "n/a"


def load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def app_dir(a: dict) -> pathlib.Path:
    return ROOT / a["repo"] if a.get("dir", ".") == "." else ROOT / a["repo"] / a["dir"]


def icon_state(d: pathlib.Path) -> tuple[str, str]:
    appicon = d / "ios/Runner/Assets.xcassets/AppIcon.appiconset"
    master = appicon / "Icon-App-1024x1024@1x.png"
    if not master.exists():
        cands = sorted(appicon.glob("*1024*.png")) if appicon.is_dir() else []
        if not cands:
            return NO, "no 1024 icon"
        master = cands[0]
    digest = hashlib.sha256(master.read_bytes()).hexdigest()[:12]
    if digest == FLUTTER_DEFAULT_ICON:
        return NO, "stock Flutter placeholder"
    try:
        from PIL import Image
        alpha = [p.name for p in appicon.glob("*.png")
                 if Image.open(p).mode in ("RGBA", "LA", "P")]
        if alpha:
            return NO, f"alpha channel in {len(alpha)} slot(s) (ITMS-90717)"
    except Exception:
        pass
    return OK, digest


def plist_get(d: pathlib.Path, key: str):
    p = d / "ios/Runner/Info.plist"
    if not p.exists():
        return None
    try:
        return plistlib.loads(p.read_bytes()).get(key)
    except Exception:
        return None


def linked_frameworks_needing_strings(d: pathlib.Path) -> list[str]:
    """Purpose strings Apple demands for APIs the app links, even via a plugin.

    A missing one does not fail the build; App Store processing accepts the
    upload and then silently never lists the build. Two apps here lost a day to
    exactly that.
    """
    # Only the dependency blocks. Matching the whole file made the app's own
    # `description:` trip this: MileMaster's says "record" and WiFiTrail's says
    # "nearby", which flagged a microphone and a Bluetooth purpose string
    # neither app needs. Declaring a purpose string for an API the app does not
    # use is its own small dishonesty, so the check has to read dependencies.
    pubspec = ""
    if (d / "pubspec.yaml").exists():
        keep, out = False, []
        for line in (d / "pubspec.yaml").read_text().splitlines():
            if re.match(r"^(dependencies|dev_dependencies|dependency_overrides):", line):
                keep = True
                continue
            if re.match(r"^[A-Za-z_]", line):
                keep = False
            if keep:
                out.append(line.split("#", 1)[0])
        pubspec = "\n".join(out)
    need = {
        "NSCameraUsageDescription": ("camera", "image_picker", "mobile_scanner", "qr_code"),
        "NSPhotoLibraryUsageDescription": ("image_picker", "photo_manager", "file_picker"),
        "NSMicrophoneUsageDescription": ("record", "speech_to_text", "audio", "just_audio"),
        "NSLocationWhenInUseUsageDescription": ("geolocator", "location", "google_maps"),
        "NSFaceIDUsageDescription": ("local_auth",),
        "NSMotionUsageDescription": ("pedometer", "sensors_plus", "health"),
        "NSCalendarsUsageDescription": ("device_calendar", "add_2_calendar"),
        "NSContactsUsageDescription": ("contacts_service", "flutter_contacts"),
        "NSBluetoothAlwaysUsageDescription": ("flutter_blue", "blue_plus", "nearby"),
    }
    missing = []
    for key, markers in need.items():
        if any(m in pubspec for m in markers) and not plist_get(d, key):
            missing.append(key)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app")
    args = ap.parse_args()

    # store_eligible is still honoured so the manifest can exclude an app, but
# nothing sets it false any more: all 43 are in scope. This comment used to
# say the portfolio was 42.
    # `_blocked` in its store JSON, so store_eligible is false. It is not a
    # store candidate and counting its gaps as failures made the portfolio
    # look 43 apps wide when 42 are actually going to a store.
    apps = [a for a in load(MANIFEST_DIR / "apps.json", {"apps": []})["apps"]
            if a.get("flutter") and a.get("store_eligible", True)]
    if args.app:
        apps = [a for a in load(MANIFEST_DIR / "apps.json", {"apps": []})["apps"]
                if a["repo"] == args.app]

    aab = {r["repo"]: r for r in load(MANIFEST_DIR / "docs/build-evidence.json", [])}
    apk = {r["repo"]: r for r in load(MANIFEST_DIR / "docs/build-evidence-apk.json", [])}
    ipa = {r["repo"]: r for r in load(MANIFEST_DIR / "docs/ios-ipa-evidence.json", [])}
    shots_ev = {r["repo"]: r for r in load(SWEEP / "screenshot-evidence.json", [])}
    uploaded = set()
    up = SWEEP / "asc_upload.psv"
    if up.exists():
        uploaded = {l.split("|")[0] for l in up.read_text().splitlines()
                    if "|UPLOADED" in l}
    # A 200 is not evidence. www.safecodeg.com serves its SPA for every
    # unmatched path, so a policy URL for an app that does not exist returned
    # byte-identical content to a real one - 131 URLs "passed" while none of
    # the pages was actually published. The evidence file must therefore record
    # a content check, not a status code; until it does, this row cannot pass.
    # Written by scripts/verify_policy_urls.py, which fetches each URL, proves
    # it is not the SPA catch-all by comparing against a nonsense control path,
    # and checks the page title names the right app. The older
    # .sweep/store_url_verified.psv recorded status codes, which is how 131
    # URLs were once reported as passing while none of the pages existed.
    policy_urls = load(DIST / "policy-urls.json", {})
    urls_ok = {repo for repo, pages in policy_urls.items()
               if pages and all(p.get("state") == "OK" for p in pages.values())}
    # Real per-app Play state, written by scripts/play_internal_share.py. The
    # Play row used to be hardcoded HUMAN with the reason "no Play
    # service-account JSON exists", which stopped being true once
    # ~/.secrets/play-publisher-agl.json was created.
    play_state = {r["repo"]: r for r in
                  load(DIST / "play-internal-share.json", {}).get("artifacts", [])}
    # Apple's age-rating questionnaire is not a human gate: ageRatingDeclarations
    # is in the public ASC API and the team key can write it. Written by
    # scripts/testflight/sync_age_rating.rb. Play's IARC really has no API.
    age_rating = load(DIST / "age-rating-sync.json", {})

    rows = []
    for a in apps:
        repo = a["repo"]
        d = app_dir(a)
        rec = load(MANIFEST_DIR / f"store/apps/{repo}.json", {})
        en = rec.get("copy", {}).get("en", {})
        checks: list[tuple[str, str, str]] = []

        def add(name, state, note=""):
            checks.append((name, state, note))

        # --- binaries -------------------------------------------------------
        a_ev = aab.get(repo, {})
        add("Android .aab signed with this app's upload key",
            OK if a_ev.get("result") == "SIGNED" else NO,
            a_ev.get("result", "not built"))
        k_ev = apk.get(repo, {})
        add("Android .apk (release, sideload/test)",
            OK if k_ev.get("result") == "SIGNED" else NO,
            k_ev.get("result", "not built"))
        i_ev = ipa.get(repo, {})
        add("iOS .ipa exported for the App Store",
            OK if i_ev.get("result") == "EXPORTED" else NO,
            i_ev.get("result", "not built"))
        # An icon change invalidates a binary built before it.
        icon_p = d / "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png"
        stale = ""
        if icon_p.exists() and (DIST / f"{repo}.ipa").exists():
            if icon_p.stat().st_mtime > (DIST / f"{repo}.ipa").stat().st_mtime:
                stale = "icon changed after the .ipa was built - rebuild"
        add("Binaries newer than the app icon", NO if stale else OK, stale)

        # --- identity and signing -------------------------------------------
        add("Bundle id / applicationId", OK, a["bundle_id"])
        add("Release signing configured", OK if a_ev.get("keystore_sha256") else NO,
            "upload keystore matched" if a_ev.get("keystore_sha256") == a_ev.get("signer_sha256")
            else "signer != upload key")

        # --- store artwork ---------------------------------------------------
        state, note = icon_state(d)
        add("App icon (1024, opaque, not a placeholder)", state, note)
        fg = MANIFEST_DIR / f"store/graphics/{repo}/feature-graphic.png"
        add("Play feature graphic 1024x500", OK if fg.exists() else NO,
            "" if fg.exists() else "missing")
        sh = shots_ev.get(repo, {})
        n = sh.get("count", 0)
        add("Screenshots (Apple >=1, Play >=2)",
            OK if n >= 2 else (NO if sh else NO),
            f"{n} captured {sh.get('sizes', '')}" if sh else "not captured")

        # --- listing ----------------------------------------------------------
        add("App Store name", OK if en.get("name") else NO, en.get("name", "missing"))
        add("Play title", OK if (en.get("title") or en.get("name")) else NO,
            en.get("title") or en.get("name") or "missing")
        desc = en.get("description") or en.get("full_description")
        add("Full description", OK if desc else NO,
            f"{len(desc)} chars" if desc else "missing")
        short = en.get("short_description")
        add("Play short description (<=80)",
            OK if short and len(short) <= 80 else NO,
            f"{len(short)} chars" if short else "missing")
        kw = en.get("keywords")
        add("App Store keywords (<=100)",
            OK if kw and len(kw) <= 100 else (NO if kw else NO),
            f"{len(kw)} chars" if kw else "missing")
        promo = en.get("promotional_text")
        if promo:
            add("Promotional text (<=170)", OK if len(promo) <= 170 else NO,
                f"{len(promo)} chars")
        add("Primary category", OK if rec.get("primary_category") else NO,
            rec.get("primary_category", "missing"))
        add("Per-app review notes",
            OK if rec.get("review_information", {}).get("notes") else NO, "")

        # --- policy + compliance ---------------------------------------------
        pages = policy_urls.get(repo) or {}
        bad_pages = [k for k, v in pages.items() if v.get("state") != "OK"]
        add("Privacy & support URLs serve the right page",
            OK if repo in urls_ok else (NO if pages else HUMAN),
            f"{len(pages)} checked" if repo in urls_ok else
            (", ".join(bad_pages) if bad_pages else "not measured yet"))
        auth = a.get("auth", {})
        needs_delete = bool(set(auth.get("providers") or []) &
                            {"Supabase", "Google", "Apple", "Firebase"})
        slug = rec.get("slug", repo.lower())
        del_page = (ROOT / "www.safecodeg.com/client/public/policy" / slug /
                    "delete-account.html")
        add("Account-deletion page (if accounts)",
            NA if not needs_delete else (OK if del_page.exists() else NO),
            "" if not needs_delete else ("" if del_page.exists() else "required by Play"))
        priv = d / "ios/Runner/PrivacyInfo.xcprivacy"
        add("iOS privacy manifest", OK if priv.exists() else NO, "")
        missing_strings = linked_frameworks_needing_strings(d)
        add("iOS purpose strings for linked APIs",
            OK if not missing_strings else NO,
            ", ".join(missing_strings) if missing_strings else "")
        # Declaring this in Info.plist is the answer - Apple stops asking at
        # upload and no export-compliance step appears in ASC. Measuring it
        # beats calling it HUMAN, which is what this row used to do.
        enc = plist_get(d, "ITSAppUsesNonExemptEncryption")
        add("Export compliance answered",
            OK if enc is False else (NO if enc is None else HUMAN),
            "ITSAppUsesNonExemptEncryption=false" if enc is False else
            ("key absent - ASC will ask on every upload" if enc is None else
             "declared true - needs an encryption declaration in ASC"))
        ar = (age_rating.get(repo) or {}).get("state")
        add("Apple age rating answered",
            NA if ar == "no-asc-record" else
            (OK if ar in ("already-correct", "updated") else NO),
            {"already-correct": "declaration matches the shipped binary",
             "updated": "declaration corrected by sync_age_rating.rb",
             "no-asc-record": "",
             "no-declaration": "app has no ageRatingDeclaration",
             }.get(ar, "not measured yet"))
        add("Play IARC questionnaire", HUMAN, "no API - Play Console only")

        # --- delivery ----------------------------------------------------------
        add("Build live on App Store Connect", OK if repo in uploaded else NO,
            "uploaded" if repo in uploaded else "no ASC record or not uploaded")
        pst = (play_state.get(repo) or {}).get("state")
        add("Play delivery to account users",
            OK if pst == "SHARED" else (NO if pst else HUMAN),
            {"SHARED": "internal app sharing link issued",
             "NOT_PUBLISHED": "still a Draft app in Console - MA-022",
             "NO_LISTING": "no Play entry - MA-021"}.get(pst, "not measured yet"))
        # Shipping the file is not the same as shipping it in the app. This
        # row passed for all 43 apps while Firebase was dead on iOS in 36 of
        # them, because Xcode only copies what the project references and the
        # check only asked whether the file was on disk. It now asks both.
        gs = (d / "android/app/google-services.json").exists()
        gi_file = d / "ios/Runner/GoogleService-Info.plist"
        gi = gi_file.exists()
        pbx = d / "ios/Runner.xcodeproj/project.pbxproj"
        bundled = pbx.exists() and "GoogleService-Info.plist" in pbx.read_text(
            errors="ignore")
        add("Firebase config (crash reporting works)",
            OK if (gs and gi and bundled) else NO,
            f"android={'y' if gs else 'n'} ios={'y' if gi else 'n'} "
            f"ios-bundled={'y' if bundled else 'n'}"
            + ("" if bundled else "  <- plist not referenced by Xcode"))

        rows.append((repo, checks))

    # ---- emit ----------------------------------------------------------------
    # Results as data only. status.py folds the state of each check into the
    # `check: *` columns of status.csv, which is the single sheet for the
    # portfolio; this file additionally keeps each check's detail string, which
    # does not fit a spreadsheet cell. There used to be a STORE_CHECKLIST.md
    # rendering too, but eleven overlapping status documents is how they drift.
    total_fail = sum(1 for _, checks in rows for _, s, _ in checks if s == NO)
    import json as _json
    (MANIFEST_DIR / "docs/store-checklist.json").write_text(
        _json.dumps({repo: {name: state for name, state, _ in checks}
                     for repo, checks in rows}, indent=1) + "\n")
    (MANIFEST_DIR / "docs/store-checklist-detail.json").write_text(
        _json.dumps({repo: [{"check": n, "state": s, "detail": d}
                            for n, s, d in checks]
                     for repo, checks in rows}, indent=1) + "\n")
    print(f"{len(rows)} apps -> docs/store-checklist.json "
          f"({total_fail} failing checks) — the `check: *` columns of status.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
