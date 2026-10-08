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

# First-party API hostnames that are not under one of our two domains. Every
# one of them is NXDOMAIN: placeholders for backends that were never built.
FIRST_PARTY = {"api.myhealth.app", "api.virtuband.app", "virtuband.app",
               "photriya.cloud", "grocerymatch.app", "uscis-case94.manus.app"}


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


AUTH_CALL = re.compile(r"signInWithPassword|SupabaseAuthService|signInWithOtp"
                       r"|FirebaseAuth\.instance\.signIn")
GUEST = re.compile(r"(?i)continue as guest|guest mode|skip sign|browse as guest"
                   r"|continue without")


def login_gate(d: pathlib.Path) -> bool:
    """True when the app signs in and offers no way past it.

    Five apps ship a sign-in wall whose only bypass is compiled out of
    release builds, and all 43 declared demoAccountRequired: false. That is
    the Guideline 2.1 "we were unable to review" rejection, written down.
    """
    lib = d / "lib"
    if not lib.exists():
        return False
    auth = guest = False
    for f in lib.rglob("*.dart"):
        if "generated" in str(f):
            continue
        try:
            s = f.read_text(errors="ignore")
        except OSError:
            continue
        auth = auth or bool(AUTH_CALL.search(s))
        guest = guest or bool(GUEST.search(s))
    return auth and not guest


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
    # docs/asc-build-state.json is committed and readable on a runner. The
    # old source, .sweep/asc_upload.psv, is outside the repository and went
    # stale silently — it was five days old and made this row report 14 apps
    # with no App Store build when Apple had 38 uploaded. The .psv is still
    # accepted as a fallback so an older checkout keeps working.
    asc_state = load(MANIFEST_DIR / "docs/asc-build-state.json", [])
    uploaded = {r["repo"] for r in asc_state if r.get("state") == "UPLOADED"}
    if not uploaded:
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
    play_release = load(DIST / "play-release-results.json", {})
    play_gaps = load(DIST / "play-gap-audit.json", {})

    # Capture and launch evidence. Both are written by the scripts that do
    # the work, so a missing entry reads as "not verified" rather than PASS.
    shots_meta = load(DIST / "screenshots-results.json", {})
    # Every report, oldest first, so a later run overwrites an earlier
    # result for the same app and platform. One run is not enough: a full
    # sweep covers 43 apps, and a retry of the ones a frozen simulator
    # skipped covers 12 — reading only the newest file threw away the 31
    # that had already passed.
    _sim_reports = sorted((DIST / "sim-install").glob("20*.json")) \
        if (DIST / "sim-install").is_dir() else []
    sim_meta = {}
    for _f in _sim_reports:
        for r in (load(_f, {}).get("results") or []):
            if r.get("repo") and r.get("platform"):
                sim_meta.setdefault(r["repo"], {})[r["platform"]] = r.get("status")
    sim_raw = {}

    # Every host the app calls must exist. See verify_api_hosts.py: 18 apps
    # shipped calls to backends that were never deployed — GroceryMatch's
    # sign-in among them — and nothing that runs on the laptop can notice.
    api_hosts = load(MANIFEST_DIR / "docs/api-hosts.json", {}).get("apps", {})

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

        # --- the network: real endpoints only -------------------------------
        ah = api_hosts.get(repo)
        if ah is None:
            add("Every API host the app calls exists", NO,
                "not measured - run scripts/verify_api_hosts.py")
        else:
            dead = ah.get("dead") or {}
            # Ours vs theirs needs different advice. Ours never existed — the
            # org has no API server, so the call belongs on Supabase. Theirs
            # existed and went away (feeds.reuters.com, retired radio-browser
            # mirrors), so it needs a live replacement, not Supabase.
            def hint(h, v):
                ours = h.endswith(("americangroupllc.com", "safecodeg.com")) or \
                    h in FIRST_PARTY
                return (f"{h} ({v[0]}) - ours, never deployed: move to Supabase"
                        if ours else f"{h} ({v[0]}) - third-party host is gone: replace it")
            add("Every API host the app calls exists",
                NO if dead else OK,
                "; ".join(hint(h, v) for h, v in sorted(dead.items()))
                if dead else f"{ah.get('hosts', 0)} host(s), all resolve")

        # --- launches on current iOS ---------------------------------------
        # iOS 27 traps at launch in _UIApplicationEvaluateRuntimeIssueFor-
        # NoSceneLifecycleAdoption for any app without a scene manifest. 21
        # apps shipped without one. scripts/ios_scene_lifecycle.py fixes it.
        import plistlib as _pl
        _ip = d / "ios/Runner/Info.plist"
        if _ip.exists():
            try:
                _info = _pl.loads(_ip.read_bytes())
                _scene = bool(_info.get("UIApplicationSceneManifest"))
                _launch = bool(_info.get("UILaunchStoryboardName"))
            except Exception as _e:  # malformed plist is itself a failure
                _scene, _launch = False, False
            add("Adopts the UIScene lifecycle (launches on iOS 27)",
                OK if _scene else NO,
                "UIApplicationSceneManifest present" if _scene else
                "no UIApplicationSceneManifest: crashes on launch on iOS 27 — "
                "run scripts/ios_scene_lifecycle.py")
            add("Has a launch screen", OK if _launch else NO,
                "UILaunchStoryboardName set" if _launch else
                "UILaunchStoryboardName empty: no launch screen")

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
        # Counted from the repo, not from ~/agl/.sweep/screenshot-evidence.json.
        # Nothing in this repository writes that file — it is left over from the
        # retired sweep — and it does not exist on a runner, so every CI
        # regeneration flipped this row from 43 PASS to 43 FAIL and committed
        # the result. Both platforms keep their shots in fastlane/, which CI
        # checks out, so the real answer is available everywhere.
        ios_shots = sorted((d / "fastlane/screenshots").rglob("*.png")) \
            if (d / "fastlane/screenshots").is_dir() else []
        play_dir = d / "fastlane/metadata/android/en-US/images/phoneScreenshots"
        play_shots = sorted(play_dir.glob("*.png")) + sorted(play_dir.glob("*.jpg")) \
            if play_dir.is_dir() else []
        # Apple needs at least one, Play at least two. Reporting a single number
        # hid the case where an app had plenty of one and none of the other.
        shots_ok = len(ios_shots) >= 1 and len(play_shots) >= 2
        add("Screenshots (Apple >=1, Play >=2)",
            OK if shots_ok else NO,
            f"apple {len(ios_shots)}, play {len(play_shots)}")

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
        # Two different Play mechanisms, and collapsing them into one row was
        # actively misleading: it reported 37 failures while Play itself had 27
        # apps carrying a live internal-track release. Both numbers were true
        # about different things, and the pessimistic one hid real progress.
        #
        #   the TRACK    a release on internal testing. Automatable, and done.
        #                Reaches testers only via a Google Group, and the
        #                decision on this account is to use none.
        #   SHARING      internal app sharing, which is how people already on
        #                the Play Console account get a build. Gated on the
        #                app's Draft state in Console, which no API clears.
        # "Has Play got a release for this app", which the production track
        # answers just as well as the internal one. Reading only the internal
        # track failed TripNest, Uscis-Case, VirtuBand, iMaps and iMeasure —
        # every one of which has a *completed production* release. Promoting
        # an app is progress; a check that calls it a regression is wrong.
        prel = (play_release.get(repo) or {}).get("status")
        pgap = (play_gaps.get(repo) or {})
        prod = pgap.get("production_release")
        if prod == "completed":
            add("Play release", OK, "live on production")
        elif prel == "live-internal":
            add("Play release", OK, "live on the internal testing track")
        elif prod == "draft":
            add("Play release", OK,
                "staged on the production track, goes live when the app is published")
        else:
            add("Play release", NO, "no release on any track")

        pst = (play_state.get(repo) or {}).get("state")
        add("Play reaches Console account users",
            OK if pst == "SHARED" else HUMAN,
            {"SHARED": "internal app sharing link issued",
             "NOT_PUBLISHED": "app is still a Draft in Console - MA-022",
             "NO_LISTING": "no Play entry - MA-021"}.get(
                 pst, "not measured yet"))
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

        # --- what Apple actually rejected us for ----------------------------
        # Every check above passed for apps that were then rejected. These
        # six are the gaps those rejections went through, each measured.

        # 2.1: the notes must answer Apple's current seven-item request, not
        # the five-item one it used to ask. Numbered headings are the marker.
        notes = (rec.get("review_information") or {}).get("notes") or ""
        answered = [n for n in range(2, 8) if f"\n{n}." in notes or notes.startswith(f"{n}.")]
        add("Review notes answer Apple's 7 items",
            OK if len(answered) >= 6 else NO,
            f"{len(answered)}/6 numbered answers present")

        # 2.1: an app behind a sign-in wall must hand the reviewer a way in.
        gate = login_gate(d)
        demo = (rec.get("review_information") or {}).get("demo_account_name") or ""
        add("Demo account when the app gates on sign-in",
            OK if (not gate or demo) else NO,
            "no sign-in gate" if not gate
            else (f"demo user {demo}" if demo else "sign-in wall with NO demo account"))

        # 2.3.3: screenshots must show the app, not its login screen. The
        # capture records which screen it reached; a run that never got past
        # the gate is the rejection Apple already sent us.
        shot = (shots_meta.get(repo) or {})
        past = shot.get("passed_sign_in")
        add("Screenshots show the app, not a login screen",
            OK if past is True else (NO if past is False else HUMAN),
            "capture walked past the sign-in gate" if past is True
            else ("capture stopped at the sign-in screen" if past is False
                  else "not recorded — re-run scripts/screenshots.py"))

        # The app preview video Apple shows on the product page. Optional for
        # approval, but asked for here so its absence is a decision.
        vid = sorted(d.glob("fastlane/screenshots/**/*.mp4")) + \
              sorted(d.glob("store_video/*.mp4")) + sorted(d.glob("videos/*.mp4"))
        add("App preview video", OK if vid else HUMAN,
            vid[0].name if vid else "none recorded")

        # Proof the build starts. A binary that crashes on launch is the
        # fastest possible 2.1.
        sim = (sim_meta.get(repo) or {})
        add("Launches on a simulator and stays up",
            OK if sim.get("ios") == "running" and sim.get("android") == "running"
            else (NO if sim else HUMAN),
            f"ios={sim.get('ios', '?')} android={sim.get('android', '?')}")

        # 4.3: the question Apple asks every app in a large portfolio. A
        # written answer has to exist before submission, not after rejection.
        diff = (rec.get("differentiation") or "").strip()
        todos = diff.count("TODO")
        add("4.3 differentiation statement",
            OK if (len(diff) >= 200 and todos == 0) else NO,
            "missing" if not diff
            else (f"{todos} unanswered question(s)" if todos
                  else f"{len(diff)} chars, complete"))

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
