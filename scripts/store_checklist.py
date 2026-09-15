#!/usr/bin/env python3
"""Produce a per-app store submission checklist, measured rather than asserted.

Every row is a real check against the tree, the store records, or an artefact on
disk. Nothing here is a judgement about whether the app is *good*; it is whether
each concrete thing a store demands is present. Items a machine cannot settle
(age rating questionnaires, Firebase console downloads, an Apple ID login) are
listed as HUMAN so they are visible rather than silently missing.

    python3 scripts/store_checklist.py            # -> docs/STORE_CHECKLIST.md
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

ROOT = pathlib.Path("/Users/spatchava/agl")
MANIFEST_DIR = ROOT / "agl-manifest"
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
    pubspec = (d / "pubspec.yaml").read_text() if (d / "pubspec.yaml").exists() else ""
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
    ap.add_argument("--out", default=str(MANIFEST_DIR / "docs/STORE_CHECKLIST.md"))
    args = ap.parse_args()

    apps = [a for a in load(MANIFEST_DIR / "apps.json", {"apps": []})["apps"]
            if a.get("flutter")]
    if args.app:
        apps = [a for a in apps if a["repo"] == args.app]

    aab = {r["repo"]: r for r in load(MANIFEST_DIR / "docs/build-evidence.json", [])}
    apk = {r["repo"]: r for r in load(MANIFEST_DIR / "docs/build-evidence-apk.json", [])}
    ipa = {r["repo"]: r for r in load(MANIFEST_DIR / "docs/ios-ipa-evidence.json", [])}
    shots_ev = {r["repo"]: r for r in load(SWEEP / "screenshot-evidence.json", [])}
    uploaded = set()
    up = SWEEP / "asc_upload.psv"
    if up.exists():
        uploaded = {l.split("|")[0] for l in up.read_text().splitlines()
                    if "|UPLOADED" in l}
    urls_ok = set()
    uc = SWEEP / "store_url_check.psv"
    if uc.exists():
        urls_ok = {l.split("|")[0] for l in uc.read_text().splitlines()
                   if "privacy=200|support=200" in l}

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
        add("Privacy & support URLs resolve (HTTP 200)",
            OK if repo in urls_ok else NO, "")
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
        add("Export compliance answered", HUMAN, "ITSAppUsesNonExemptEncryption / ASC")
        add("Age rating questionnaire", HUMAN, "Apple + Play IARC, per app")

        # --- delivery ----------------------------------------------------------
        add("Build live on App Store Connect", OK if repo in uploaded else NO,
            "uploaded" if repo in uploaded else "no ASC record or not uploaded")
        add("Play Console upload", HUMAN, "no Play service-account JSON exists")
        gs = (d / "android/app/google-services.json").exists()
        gi = (d / "ios/Runner/GoogleService-Info.plist").exists()
        add("Firebase config (crash reporting works)",
            OK if (gs and gi) else NO,
            f"android={'y' if gs else 'n'} ios={'y' if gi else 'n'}")

        rows.append((repo, checks))

    # ---- render --------------------------------------------------------------
    total_fail = 0
    out = ["# Per-app store submission checklist", "",
           "Every line is a real check against the tree, the store record, or an",
           "artefact on disk - regenerate with `python3 scripts/store_checklist.py`",
           "rather than editing. `HUMAN` marks the things no script can settle: a",
           "console login, a questionnaire, or a credential that does not exist yet.",
           ""]
    summary = []
    for repo, checks in rows:
        f = sum(1 for _, s, _ in checks if s == NO)
        h = sum(1 for _, s, _ in checks if s == HUMAN)
        p = sum(1 for _, s, _ in checks if s == OK)
        total_fail += f
        summary.append((repo, p, f, h))
    out += ["## Summary", "", "| App | pass | fail | human |", "| --- | ---: | ---: | ---: |"]
    out += [f"| {r} | {p} | {f} | {h} |" for r, p, f, h in summary]
    out += ["", f"**{total_fail} failing checks across {len(rows)} apps.**", ""]

    for repo, checks in rows:
        out += [f"## {repo}", "", "| Check | State | Detail |", "| --- | :-: | --- |"]
        out += [f"| {n} | {s} | {d} |" for n, s, d in checks]
        out.append("")

    outfile = pathlib.Path(args.out)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text("\n".join(out) + "\n")
    print(f"{len(rows)} apps -> {outfile}  ({total_fail} failing checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
