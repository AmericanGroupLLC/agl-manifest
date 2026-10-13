#!/usr/bin/env python3
"""The iOS pre-delivery checklist: 45 checks, 5 gates, a release record — per app, per build.

    python3 scripts/predelivery.py BodyQuest                 # run every check on ~/agl/.dist/BodyQuest.ipa
    python3 scripts/predelivery.py BodyQuest --after-upload  # also section 6 (asks App Store Connect)
    python3 scripts/predelivery.py BodyQuest --sign 5.1 --by "Sri" \\
        --device "iPhone 15, iOS 27.0" --evidence "release build installed via TestFlight smoke group; launched, played 3 games"
    python3 scripts/predelivery.py --all                     # every app, sections 1-5

Founder rule (2026-10-12): **no checklist pass, no delivery.** `ipa_blocker()`
in testflight/transporter_upload.py — the gate both upload paths call, CI
included — refuses an IPA unless this script has a PASS record for that exact
file (sha256) with gates 1-4 met.

Each check is one of:
  auto   — measured here from the IPA, the source, or a live request
  human  — a person signs it off (--sign) with who, device/iOS and evidence;
           signatures are bound to the IPA's sha256, so a new build needs new ones.
           Where a human check has a measurable precondition (e.g. Google
           Sign-In configured), a failing precondition fails the check outright.
  post   — section 6, only after upload: read from App Store Connect
           (testflight/build_delivery_state.rb, GET only).

Writes docs/predelivery/<App>.md (the checklist, rendered) and
docs/predelivery/<App>.json; signatures live in store/predelivery/<App>.json.
Nothing here marks a check PASS without evidence printed next to it.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import plistlib
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "testflight"))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402

FLUTTER = str(ROOT / ".flutter-sdk/bin/flutter")
OUT_DIR = M / "docs/predelivery"
SIGN_DIR = M / "store/predelivery"
PASS, FAIL, HUMAN, NA = "PASS", "FAIL", "HUMAN", "n/a"

SECTIONS = {
    "1": "App functionality", "2": "iOS permissions and privacy", "3": "Flutter and iOS build",
    "4": "Backend and environment", "5": "Device testing", "6": "App Store Connect and TestFlight",
}
CHECKS = [  # (id, kind, text)
    ("1.1", "human", "App launches without crashing"),
    ("1.2", "human", "Every screen opens and renders correctly"),
    ("1.3", "human", "Navigation, back buttons, and deep links work"),
    ("1.4", "human", "Login, signup, logout, and password reset work"),
    ("1.5", "human", "API calls, database operations, and error handling work"),
    ("1.6", "human", "Loading states, empty states, and offline behavior are handled"),
    ("1.7", "auto", "No placeholder content, debug menus, or test-only screens remain"),
    ("2.1", "auto", "Audit location-related dependencies and SDKs"),
    ("2.2", "auto", "NSLocationAlwaysAndWhenInUseUsageDescription only if required, with an accurate purpose string"),
    ("2.3", "auto", "Other required Info.plist purpose strings for APIs actually referenced"),
    ("2.4", "human", "Permission prompts appear at the correct time"),
    ("2.5", "auto", "Privacy policy URL is valid and accessible"),
    ("2.6", "auto", "App Privacy disclosures match actual data collection"),
    ("2.7", "auto", "Account deletion works if account creation is supported"),
    ("3.1", "auto", "Flutter dependencies resolve successfully"),
    ("3.2", "auto", "Release build succeeds without errors"),
    ("3.3", "auto", "Xcode archive completes successfully"),
    ("3.4", "auto", "Correct bundle identifier is configured"),
    ("3.5", "auto", "Version and build number are correct and incremented"),
    ("3.6", "auto", "Signing certificate and provisioning profile are valid"),
    ("3.7", "auto", "Deployment target matches supported iOS versions"),
    ("3.8", "auto", "Required entitlements are correct"),
    ("3.9", "auto", "No unintended development configuration or debug logging is enabled"),
    ("4.1", "auto", "Production or intended testing API URL is configured"),
    ("4.2", "human", "Backend is reachable from a real device"),
    ("4.3", "human", "Authentication and test accounts work"),
    ("4.4", "auto", "Required services, API keys, and configuration are present"),
    ("4.5", "auto", "No localhost URLs or developer-only endpoints remain"),
    ("4.6", "human", "Push notifications and other integrations are tested if applicable"),
    ("5.1", "human", "Install and launch the release build on a physical iPhone"),
    ("5.2", "human", "Test on the minimum supported iOS version when possible"),
    ("5.3", "human", "Test on a current iOS version"),
    ("5.4", "human", "Test clean installation and upgrade from the previous build"),
    ("5.5", "human", "Verify app behavior after force quit and relaunch"),
    ("5.6", "human", "Check layout, keyboard, safe areas, and different screen sizes"),
    ("5.7", "human", "Check performance, memory use, and crash logs"),
    ("6.1", "post", "Upload the correct .ipa/build through the intended workflow"),
    ("6.2", "post", "Wait until build processing finishes"),
    ("6.3", "post", "Confirm the build appears under TestFlight → Builds"),
    ("6.4", "human", "Resolve blocking errors and investigate warnings"),
    ("6.5", "post", "Complete export-compliance questions if required"),
    ("6.6", "post", "Confirm internal testers are App Store Connect users with appropriate access"),
    ("6.7", "post", "Add the build to the internal testing group"),
    ("6.8", "post", "Verify testers can see the build and install it"),
    ("6.9", "post", "Send the testing notification and provide test instructions"),
]
GATES = [
    ("Gate 1 — Build", "Flutter release build and Xcode archive succeed",
     ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"]),
    ("Gate 2 — Installation", "The release build installs and launches on a physical iPhone", ["5.1"]),
    ("Gate 3 — Functionality", "Core journeys work: login, navigation, backend", ["1.1", "1.3", "1.4", "1.5", "4.2"]),
    ("Gate 4 — Privacy", "Purpose strings and entitlements are correct", ["2.1", "2.2", "2.3", "2.7", "3.8"]),
    ("Gate 5 — Distribution", "Processed, in the internal group, installable by testers", ["6.2", "6.3", "6.7", "6.8"]),
]
# Delivery needs every section 1-5 check PASS (or n/a) and gates 1-4; gate 5 is after upload.
PRE_UPLOAD_SECTIONS = ("1", "2", "3", "4", "5")


def sh(cmd, cwd=None, timeout=600):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def code_lines(lib: pathlib.Path):
    for f in sorted(lib.rglob("*.dart")):
        if ".g.dart" in f.name or "/l10n/" in str(f):
            continue
        for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            s = line.strip()
            if s and not s.startswith("//"):
                yield f, i, line


class Ctx:
    def __init__(self, a: dict):
        self.a, self.repo = a, a["repo"]
        self.repo_dir = ROOT / a["repo"]
        self.d = self.repo_dir / (a.get("dir") or ".")
        self.lib = self.d / "lib"
        self.ipa = DIST / f"{self.repo}.ipa"
        self.info, self.app_dir, self.tmp = {}, None, None
        self.pubspec = (self.d / "pubspec.yaml").read_text() if (self.d / "pubspec.yaml").exists() else ""
        self.rr = next((x for x in json.loads((M / "docs/release-readiness.json").read_text())
                        if x["repo"] == self.repo), {})
        if self.ipa.exists():
            self.ipa_sha = sha256(self.ipa)
            self.tmp = tempfile.TemporaryDirectory()
            with zipfile.ZipFile(self.ipa) as z:
                z.extractall(self.tmp.name)
            apps = list(pathlib.Path(self.tmp.name, "Payload").glob("*.app"))
            if apps:
                self.app_dir = apps[0]
                self.info = plistlib.loads((self.app_dir / "Info.plist").read_bytes())
        else:
            self.ipa_sha = None

    def dep(self, name: str) -> bool:
        return re.search(rf"(?m)^\s+{re.escape(name)}\s*:", self.pubspec) is not None

    def auth_providers(self) -> list[str]:
        """Sign-in the CURRENT source offers (measured docs go stale the moment an app is reworked)."""
        found = set()
        for _f, _i, line in code_lines(self.lib):
            if re.search(r"GoogleSignIn\(|signInWithIdToken\(\s*provider:\s*OAuthProvider\.google|OAuthProvider\.google", line):
                found.add("Google")
            if re.search(r"SignInWithApple\.|OAuthProvider\.apple", line):
                found.add("Apple")
            if re.search(r"\.auth\.(signUp|signInWithPassword|signInWithOtp)\(", line):
                found.add("Supabase")
        return sorted(found)

    @property
    def build(self) -> str:
        return str(self.info.get("CFBundleVersion", ""))

    @property
    def entitlements(self) -> str:
        if not self.app_dir:
            return ""
        return sh(["codesign", "-d", "--entitlements", ":-", str(self.app_dir)])[1]


def run_auto(c: Ctx) -> dict:
    r: dict[str, tuple[str, str]] = {}
    no_ipa = (FAIL, f"no IPA at {c.ipa} — run `python3 scripts/build_ipa.py {c.repo}`")

    # 1.7 placeholder / debug / test-only content
    pat = re.compile(r"lorem ipsum|coming soon|\bTODO\b|placeholder text|debugShowCheckedModeBanner:\s*true|"
                     r"'/(debug|test|dev)[-_a-z]*'", re.I)
    hits = [f"{f.relative_to(c.repo_dir)}:{i}" for f, i, l in code_lines(c.lib) if pat.search(l)]
    gated = [h for h in hits if "kDebugMode" in h]
    r["1.7"] = (FAIL, f"{len(hits)} line(s): " + ", ".join(hits[:6])) if hits else \
        (PASS, "no lorem/coming-soon/TODO/debug-banner/debug routes in lib/")

    # 2.1-2.3 purpose strings, judged on the binary like Apple
    loc_deps = [d for d in ("geolocator", "location", "google_maps_flutter", "flutter_map", "background_location",
                            "permission_handler") if c.dep(d)]
    if not c.app_dir:
        r["2.1"] = r["2.2"] = r["2.3"] = no_ipa
    else:
        from privacy_scan import scan, RULES
        _info, missing = scan(c.ipa)
        blob = b""
        for p in [c.app_dir / c.info.get("CFBundleExecutable", "Runner")] + \
                 list((c.app_dir / "Frameworks").glob("*.framework/*")):
            if p.is_file() and "." not in p.name:
                blob += p.read_bytes()
        needs_always = b"requestAlwaysAuthorization" in blob
        r["2.1"] = (PASS, f"location deps: {', '.join(loc_deps) or 'none'}; binary references "
                          f"requestAlwaysAuthorization={needs_always}, "
                          f"requestWhenInUseAuthorization={b'requestWhenInUseAuthorization' in blob}")
        has_always = bool(c.info.get("NSLocationAlwaysAndWhenInUseUsageDescription"))
        if needs_always and not has_always:
            r["2.2"] = (FAIL, "binary references requestAlwaysAuthorization; key missing (ITMS-90683)")
        elif has_always and not needs_always:
            r["2.2"] = (FAIL, "key declared but nothing in the binary needs it — remove it")
        elif has_always:
            r["2.2"] = (PASS, f"required and present: \"{c.info['NSLocationAlwaysAndWhenInUseUsageDescription'][:90]}\"")
        else:
            r["2.2"] = (NA, "not required by the binary, not declared")
        other = [f"{k} ({api})" for k, api in missing if k != "NSLocationAlwaysAndWhenInUseUsageDescription"]
        r["2.3"] = (FAIL, "missing: " + ", ".join(other)) if other else \
            (PASS, "every purpose string the binary's APIs require is present")

    # 2.5 privacy policy URL, fetched live
    rec = json.loads((M / f"store/apps/{c.repo}.json").read_text()) if (M / f"store/apps/{c.repo}.json").exists() else {}
    url = ((rec.get("copy") or {}).get("en") or {}).get("privacy_url")
    if not url:
        # 24 store records carry no privacy_url; the policy page App Store
        # Connect gets is the one verify_policy_urls.py proved live (asc_urls.rb
        # sets it from there). It is still fetched below, now, not trusted.
        pu = DIST / "policy-urls.json"
        url = ((json.loads(pu.read_text()).get(c.repo) or {}).get("privacy") or {}).get("url") if pu.exists() else None
    if not url:
        r["2.5"] = (FAIL, "no privacy URL in the store record or in verify_policy_urls.py's results")
    else:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agl-predelivery"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read(200000).decode(errors="ignore")
            ok = resp.status == 200 and "privacy" in body.lower()
            r["2.5"] = (PASS if ok else FAIL, f"{url} → HTTP {resp.status}, mentions privacy={('privacy' in body.lower())}")
        except Exception as e:
            r["2.5"] = (FAIL, f"{url} → {type(e).__name__}: {e}")

    # 2.6 privacy label vs what the code links
    lab = M / f"store/privacy/{c.repo}.json"
    if not lab.exists():
        r["2.6"] = (FAIL, "no store/privacy label")
    else:
        text = lab.read_text().lower()
        gaps = []
        if c.dep("google_mobile_ads") or c.dep("agl_ads"):
            if "advertis" not in text:
                gaps.append("links AdMob but the label declares no advertising data")
        if c.dep("firebase_crashlytics") or c.dep("agl_observability"):
            if "crash" not in text:
                gaps.append("reports crashes but the label declares no crash data")
        r["2.6"] = (FAIL, "; ".join(gaps)) if gaps else (PASS, f"label covers the SDKs the app links ({lab.name})")

    # 2.7 account deletion — the App Review requirement check
    from apple_requirements import account_deletion_in_app, _dart, _load, _shared
    try:
        st, detail = account_deletion_in_app({"repo": c.repo, "d": c.d, "dart": _dart(c.d),
                                              "rec": _load(M / f"store/apps/{c.repo}.json", {}), **_shared()})
    except Exception as e:  # a broken check must show, not pass
        st, detail = FAIL, f"check errored: {type(e).__name__}: {e}"
    r["2.7"] = ({"PASS": PASS, "FAIL": FAIL, "n/a": NA}.get(st, HUMAN), detail)

    # 3.1 dependencies resolve without touching the lockfile
    rc, out = sh([FLUTTER, "pub", "get", "--enforce-lockfile"], cwd=c.d, timeout=900)
    r["3.1"] = (PASS, "flutter pub get --enforce-lockfile: ok") if rc == 0 else \
        (FAIL, "flutter pub get --enforce-lockfile failed: " + out.strip().splitlines()[-1][:200])

    # 3.2 / 3.3 the IPA exists, is an App Store export, and is newer than the source
    if not c.app_dir:
        r["3.2"] = r["3.3"] = no_ipa
    else:
        last = sh(["git", "-C", str(c.repo_dir), "log", "-1", "--format=%ct", "--", str(c.d.relative_to(c.repo_dir))
                   if c.d != c.repo_dir else "."])[1].strip()
        stale = last.isdigit() and int(last) > c.ipa.stat().st_mtime
        built = datetime.datetime.fromtimestamp(c.ipa.stat().st_mtime).isoformat(timespec="minutes")
        r["3.2"] = (FAIL, f"IPA built {built} is older than the last commit — rebuild") if stale else \
            (PASS, f"release IPA built {built}, newer than the last commit")
        ev = next((x for x in json.loads((M / "docs/ios-ipa-evidence.json").read_text())
                   if x.get("repo") == c.repo), {}) if (M / "docs/ios-ipa-evidence.json").exists() else {}
        exported = ev.get("result") == "EXPORTED"
        r["3.3"] = (PASS, f"archive exported ({ev.get('export_method')}, profile '{ev.get('profile')}')") if exported \
            else (FAIL, f"archive/export evidence: {ev.get('result') or 'none'}")

    if not c.app_dir:
        for k in ("3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "4.5"):
            r[k] = no_ipa
        return r

    # 3.4 bundle id
    bid = c.info.get("CFBundleIdentifier")
    r["3.4"] = (PASS if bid == c.a.get("bundle_id") else FAIL, f"IPA {bid} vs manifest {c.a.get('bundle_id')}")

    # 3.5 version matches pubspec, build number above everything Apple holds
    m = re.search(r"(?m)^version:\s*([0-9.]+)", c.pubspec)
    want_ver = m.group(1) if m else None
    ver = c.info.get("CFBundleShortVersionString")
    ev = next((x for x in json.loads((M / "docs/beta-evidence.json").read_text()).get("apps", [])
               if isinstance(x, dict) and x.get("repo") == c.repo), None) \
        if (M / "docs/beta-evidence.json").exists() else None
    held = []
    for f in ("docs/asc-build-state.json",):
        d = json.loads((M / f).read_text())
        rows = d if isinstance(d, list) else d.get("apps", [])
        held += [str(x.get("version")) for x in rows if isinstance(x, dict) and x.get("repo") == c.repo]
    top = max((int(h) for h in held if str(h).isdigit()), default=0)
    probs = []
    if want_ver and ver != want_ver:
        probs.append(f"version {ver} ≠ pubspec {want_ver}")
    if not c.build.isdigit() or int(c.build) <= top:
        probs.append(f"build {c.build} is not above the newest build Apple holds ({top})")
    r["3.5"] = (FAIL, "; ".join(probs)) if probs else (PASS, f"{ver} ({c.build}); newest uploaded {top or 'none'}")

    # 3.6 signing
    _rc, cs = sh(["codesign", "-dvvv", str(c.app_dir)])
    auth = re.search(r"Authority=([^\n]+)", cs)
    ver_rc, _ = sh(["codesign", "--verify", "--strict", str(c.app_dir)])
    prof = c.app_dir / "embedded.mobileprovision"
    exp = None
    if prof.exists():
        _r, dec = sh(["security", "cms", "-D", "-i", str(prof)])
        try:
            pl = plistlib.loads(dec.encode())
            exp = pl.get("ExpirationDate")
        except Exception:
            pass
    sp = []
    if not auth or "Apple Distribution" not in auth.group(1):
        sp.append(f"signed by {auth.group(1) if auth else 'nothing'}")
    if ver_rc != 0:
        sp.append("codesign --verify --strict fails")
    if exp and exp < datetime.datetime.now(exp.tzinfo):
        sp.append(f"profile expired {exp:%Y-%m-%d}")
    if not prof.exists():
        sp.append("no embedded.mobileprovision")
    r["3.6"] = (FAIL, "; ".join(sp)) if sp else \
        (PASS, f"{auth.group(1)}; signature valid; profile expires {exp:%Y-%m-%d}" if exp else f"{auth.group(1)}; valid")

    # 3.7 deployment target consistent
    ipa_min = c.info.get("MinimumOSVersion")
    podf = c.d / "ios/Podfile"
    m2 = re.search(r"(?m)^\s*platform\s*:ios,\s*'([0-9.]+)'", podf.read_text()) if podf.exists() else None
    pod = m2.group(1) if m2 else None
    pbx = c.d / "ios/Runner.xcodeproj/project.pbxproj"
    proj = sorted(set(re.findall(r"IPHONEOS_DEPLOYMENT_TARGET = ([0-9.]+);", pbx.read_text()))) if pbx.exists() else []
    vals = {v for v in [ipa_min, pod, *proj] if v}
    r["3.7"] = (PASS, f"iOS {ipa_min} (IPA, Podfile, project agree)") if len(vals) == 1 else \
        (FAIL, f"IPA {ipa_min}, Podfile {pod}, project {proj} disagree")

    # 3.8 entitlements
    ent = c.entitlements
    ep = []
    if re.search(r"get-task-allow</key>\s*<true/>", ent):
        ep.append("get-task-allow=true (development entitlement)")
    push = c.dep("firebase_messaging") or c.dep("flutter_local_notifications") and "remote-notification" in str(
        c.info.get("UIBackgroundModes", ""))
    if c.dep("firebase_messaging") and "aps-environment" not in ent:
        ep.append("uses firebase_messaging but has no aps-environment (ITMS-90078)")
    if "aps-environment" in ent and not c.dep("firebase_messaging"):
        ep.append("aps-environment present but no push dependency")
    apple = c.dep("sign_in_with_apple") or "Apple" in c.auth_providers()
    if apple and "com.apple.developer.applesignin" not in ent:
        ep.append("Sign in with Apple used but entitlement missing")
    if "com.apple.developer.applesignin" in ent and not apple:
        ep.append("Sign in with Apple entitlement present but the current source has no Apple sign-in")
    keys = [k for k in re.findall(r"<key>([^<]+)</key>", ent) if k != "get-task-allow"]
    r["3.8"] = (FAIL, "; ".join(ep)) if ep else (PASS, "entitlements: " + ", ".join(keys) + "; get-task-allow=false")

    # 3.9 release mode, no dev configuration, no print logging
    app_fw = c.app_dir / "Frameworks/App.framework"
    debug_kernel = any(app_fw.rglob("kernel_blob.bin")) if app_fw.exists() else False
    prints = [f"{f.relative_to(c.repo_dir)}:{i}" for f, i, l in code_lines(c.lib)
              if re.search(r"(^|[^.\w])print\(", l) and "kDebugMode" not in l]
    dp = []
    if debug_kernel:
        dp.append("App.framework contains kernel_blob.bin — this is a debug build")
    if "get-task-allow" in ent and re.search(r"get-task-allow</key>\s*<true/>", ent):
        dp.append("debuggable (get-task-allow)")
    if prints:
        dp.append(f"{len(prints)} print() call(s): " + ", ".join(prints[:4]))
    r["3.9"] = (FAIL, "; ".join(dp)) if dp else (PASS, "AOT release build, not debuggable, no print() in lib/")

    # 4.1 API hosts — from the portfolio host scan
    hosts = json.loads((M / "docs/api-hosts.json").read_text()).get("apps", {}).get(c.repo, {})
    dead = hosts.get("dead") or {}
    unv = hosts.get("unverified") or {}
    r["4.1"] = (FAIL, "dead hosts: " + ", ".join(dead)) if dead else \
        (PASS, f"every host the code calls resolves{' (' + str(len(unv)) + ' unverified)' if unv else ''} — docs/api-hosts.json")

    # 4.4 credentials the code reads that are empty in a release build
    keys_json = json.loads((M / "docs/api-vendor-keys.json").read_text())["apps"].get(c.repo, {})
    optional = ("SENTRY", "POSTHOG")
    empty = [k for k, v in keys_json.items() if not v.get("default") and not k.startswith(optional)]
    r["4.4"] = (FAIL, "empty in this build: " + ", ".join(empty) +
                " — wire it, or remove the feature that needs it") if empty else \
        (PASS, "every credential the code reads has a value in the release build")

    # 4.5 localhost / developer endpoints, in source and in the shipped binary
    dev_pat = re.compile(r"localhost|127\.0\.0\.1|10\.0\.2\.2|0\.0\.0\.0:|\.ngrok|\.local[:/]")
    src = [f"{f.relative_to(c.repo_dir)}:{i}" for f, i, l in code_lines(c.lib) if dev_pat.search(l)]
    app_bin = c.app_dir / "Frameworks/App.framework/App"
    in_bin = sorted({m.group(0).decode() for m in re.finditer(rb"https?://(localhost|127\.0\.0\.1|10\.0\.2\.2)[:/\w.-]*",
                                                              app_bin.read_bytes())}) if app_bin.exists() else []
    r["4.5"] = (FAIL, "source: " + ", ".join(src[:5]) + (f"; binary: {in_bin[:3]}" if in_bin else "")) \
        if (src or in_bin) else (PASS, "no localhost/emulator/dev endpoints in lib/ or the App binary")
    return r


def preconditions(c: Ctx, auto: dict) -> dict:
    """Measurable failures that fail a human check before anyone tests it."""
    pre = {}
    providers = c.auth_providers()
    if not providers:
        pre["1.4"] = (NA, "the app has no sign-in")
        pre["4.3"] = (NA, "the app has no accounts")
    elif "Google" in providers and c.info:
        url_types = json.dumps(c.info.get("CFBundleURLTypes", []))
        if not c.info.get("GIDClientID") and "com.googleusercontent.apps" not in url_types:
            pre["1.4"] = (FAIL, "Google Sign-In is offered but the build has no GIDClientID and no reversed-client-id "
                                "URL scheme — it cannot complete on iOS (GOOGLE_IOS_CLIENT_ID is empty)")
    if not (c.dep("firebase_messaging") or c.dep("onesignal_flutter")):
        pre["4.6"] = (NA, "no push or third-party integration that needs device testing")
    if auto.get("4.1", (PASS,))[0] == FAIL:
        pre["1.5"] = (FAIL, "the code calls hosts that do not exist (4.1)")
        pre["4.2"] = (FAIL, "the code calls hosts that do not exist (4.1)")
    return pre


def post_upload(c: Ctx) -> dict:
    r = {}
    env = M / "scripts/testflight/env.sh"
    cmd = f"source {env} >/dev/null 2>&1; bundle exec ruby build_delivery_state.rb {c.a['bundle_id']} {c.build}"
    rc, out = sh(["bash", "-c", cmd], cwd=M / "scripts/testflight", timeout=300)
    try:
        s = json.loads(out[out.index("{"):])
    except Exception:
        return {k: (FAIL, f"could not read App Store Connect: {out[-200:]}") for k in
                ("6.1", "6.2", "6.3", "6.5", "6.6", "6.7", "6.8", "6.9")}
    if not s.get("found"):
        for k in ("6.1", "6.2", "6.3", "6.5", "6.6", "6.7", "6.8", "6.9"):
            r[k] = (FAIL, f"build {c.build} not in App Store Connect (newest there: {s.get('latest_uploaded')})")
        return r
    r["6.1"] = (PASS, f"build {c.build} from IPA sha256 {c.ipa_sha[:12]} is the one Apple holds")
    ps = s.get("processing_state")
    r["6.2"] = (PASS if ps == "VALID" else FAIL, f"processing state {ps}")
    r["6.3"] = (PASS if ps == "VALID" and not s.get("expired") else FAIL,
                f"listed; internal state {s.get('internal_build_state')}, expired={s.get('expired')}")
    enc = s.get("uses_non_exempt_encryption")
    r["6.5"] = (PASS if enc is False else FAIL if enc is None else HUMAN,
                {False: "answered: no non-exempt encryption", None: "unanswered", True: "declared true — needs documentation"}[enc])
    groups = s.get("internal_groups") or []
    r["6.6"] = (PASS, ", ".join(f"'{g['name']}': {g['testers']} ASC user(s)" for g in groups)) \
        if any(g["testers"] for g in groups) else (FAIL, "no internal group with testers")
    seen = [g for g in groups if g["sees_build"]]
    r["6.7"] = (PASS, "in " + ", ".join(g["name"] + (" (all builds)" if g["all_builds"] else "") for g in seen)) \
        if seen else (FAIL, "no internal group has this build")
    states = {}
    for g in seen:
        for k, v in (g.get("tester_states") or {}).items():
            states[k] = states.get(k, 0) + v
    can = states.get("INSTALLED", 0) + states.get("ACCEPTED", 0)
    ok_state = s.get("internal_build_state") == "IN_BETA_TESTING"
    r["6.8"] = (PASS if ok_state and can else FAIL,
                f"internal state {s.get('internal_build_state')}; testers {states or 'none'}"
                + ("" if can else " — no tester has accepted the invitation, so nobody can install it"))
    wtt = [w for w in (s.get("what_to_test") or []) if (w.get("text") or "").strip()]
    r["6.9"] = (PASS, f"What to Test set ({wtt[0]['locale']}): \"{wtt[0]['text'][:80]}\"") if wtt else \
        (FAIL, "no What to Test text — testers get no instructions")
    return r


def load_signs(repo: str) -> dict:
    f = SIGN_DIR / f"{repo}.json"
    return json.loads(f.read_text()) if f.exists() else {}


def evaluate(a: dict, after_upload: bool) -> dict:
    c = Ctx(a)
    auto = run_auto(c)
    pre = preconditions(c, auto)
    signs = load_signs(c.repo).get(c.ipa_sha or "-", {})
    post = post_upload(c) if after_upload and c.app_dir else {}
    rows = []
    for cid, kind, text in CHECKS:
        if cid in auto:
            st, ev = auto[cid]
        elif cid in pre and pre[cid][0] in (FAIL, NA):
            st, ev = pre[cid]
        elif kind == "post" and not after_upload:
            st, ev = HUMAN, "after upload: run with --after-upload"
        elif cid in post:
            st, ev = post[cid]
        elif cid in signs:
            s = signs[cid]
            st, ev = PASS, f"signed by {s['by']} on {s['date']} ({s['device']}): {s['evidence']}"
        else:
            st, ev = HUMAN, "needs a person: --sign " + cid
        rows.append({"id": cid, "section": cid.split(".")[0], "kind": kind, "text": text, "state": st, "evidence": ev})
    by = {r["id"]: r for r in rows}
    gates = [{"gate": g, "rule": rule, "checks": ids,
              "met": all(by[i]["state"] in (PASS, NA) for i in ids)} for g, rule, ids in GATES]
    pre_rows = [r for r in rows if r["section"] in PRE_UPLOAD_SECTIONS]
    deliverable = all(r["state"] in (PASS, NA) for r in pre_rows) and all(g["met"] for g in gates[:4])
    done = sum(r["state"] in (PASS, NA) for r in rows)
    head = sh(["git", "-C", str(c.repo_dir), "rev-parse", "--short", "HEAD"])[1].strip()
    record = {
        "app": c.repo, "store_name": ((json.loads((M / f"store/apps/{c.repo}.json").read_text()).get("copy") or {})
                                      .get("en") or {}).get("title") if (M / f"store/apps/{c.repo}.json").exists() else c.repo,
        "version": c.info.get("CFBundleShortVersionString"), "build": c.build or None,
        "git_commit": head, "configuration": "Release", "ipa_sha256": c.ipa_sha,
        "measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "devices": sorted({s["device"] for s in signs.values()}),
        "outstanding": [f"{r['id']} {r['text']}: {r['evidence']}" for r in rows if r["state"] == FAIL],
    }
    return {"record": record, "rows": rows, "gates": gates, "deliverable": deliverable,
            "done": done, "total": len(rows)}


def render(res: dict) -> str:
    rec, rows = res["record"], res["rows"]
    pct = round(100 * res["done"] / res["total"])
    mark = {PASS: "[x]", NA: "[x]", FAIL: "[ ] ❌", HUMAN: "[ ] 👤"}
    out = [f"# iOS pre-delivery checklist — {rec['store_name']}", "",
           f"Internal TestFlight · version {rec['version']} ({rec['build']}) · commit `{rec['git_commit']}` · "
           f"measured {rec['measured_at']}", "",
           f"**{pct}% complete — {res['done']} of {res['total']} checks.** "
           f"Deliverable: **{'YES' if res['deliverable'] else 'NO'}** "
           "(every section 1–5 check passed and gates 1–4 met; the upload gate refuses otherwise).", "",
           "Generated by `scripts/predelivery.py` — do not edit. ❌ = failed (fix it), "
           "👤 = needs a person (`--sign`), [x] = passed or not applicable.", ""]
    for sec, title in SECTIONS.items():
        sr = [r for r in rows if r["section"] == sec]
        n = sum(r["state"] in (PASS, NA) for r in sr)
        out += [f"## {sec}. {title} — {n} of {len(sr)} complete", ""]
        for r in sr:
            out.append(f"- {mark[r['state']]} **{r['id']}** {r['text']}  \n  _{r['state']}: {r['evidence']}_")
        out.append("")
    out += ["## Delivery gates", ""]
    for g in res["gates"]:
        out.append(f"- {'✅' if g['met'] else '⛔'} **{g['gate']}** — {g['rule']} ({', '.join(g['checks'])})")
    out += ["", "## Release record", "",
            f"- App version: `{rec['version']}`", f"- Build number: `{rec['build']}`",
            f"- Git commit: `{rec['git_commit']}`", "- Build configuration: Release",
            f"- IPA sha256: `{rec['ipa_sha256']}`",
            f"- Test devices / iOS: {', '.join(rec['devices']) or 'none signed yet'}",
            "- Outstanding: " + ("none" if not rec["outstanding"] else ""),
            *[f"  - {o}" for o in rec["outstanding"]],
            "- Delivery owner and date: recorded by the upload (results in `~/agl/.dist`)", ""]
    return "\n".join(out)


def sign(repo: str, cid: str, by: str, device: str, evidence: str) -> None:
    ids = {c[0]: c for c in CHECKS}
    if cid not in ids or ids[cid][1] == "auto":
        sys.exit(f"{cid} is not a check a person signs (auto checks are measured, not signed)")
    if not by or not device or not evidence:
        sys.exit("--by, --device and --evidence are all required")
    ipa = DIST / f"{repo}.ipa"
    if not ipa.exists():
        sys.exit(f"no IPA at {ipa}: a signature is bound to one build")
    h = sha256(ipa)
    data = load_signs(repo)
    data.setdefault(h, {})[cid] = {"by": by, "device": device, "evidence": evidence,
                                   "date": datetime.date.today().isoformat()}
    SIGN_DIR.mkdir(parents=True, exist_ok=True)
    (SIGN_DIR / f"{repo}.json").write_text(json.dumps(data, indent=1) + "\n")
    print(f"  signed {cid} for {repo} build sha256 {h[:12]}")


def gate_for_upload(repo: str, ipa: pathlib.Path) -> str | None:
    """Used by transporter_upload.ipa_blocker: why this IPA may not be delivered, or None."""
    f = OUT_DIR / f"{repo}.json"
    if not f.exists():
        return f"no pre-delivery checklist — run `python3 scripts/predelivery.py {repo}`"
    res = json.loads(f.read_text())
    if res["record"].get("ipa_sha256") != sha256(ipa):
        return "the pre-delivery checklist was run on a different IPA — re-run it on this build"
    if not res.get("deliverable"):
        failed = [r["id"] for r in res["rows"] if r["section"] in PRE_UPLOAD_SECTIONS and r["state"] not in (PASS, NA)]
        return f"pre-delivery checklist not passed ({res['done']}/{res['total']}); open: {', '.join(failed)}"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--after-upload", action="store_true")
    ap.add_argument("--sign")
    ap.add_argument("--by")
    ap.add_argument("--device")
    ap.add_argument("--evidence")
    a = ap.parse_args()
    manifest = {x["repo"]: x for x in json.loads((M / "apps.json").read_text())["apps"]}
    if a.sign:
        if len(a.apps) != 1:
            ap.error("--sign takes exactly one app")
        sign(a.apps[0], a.sign, a.by, a.device, a.evidence)
    names = list(manifest) if a.all else a.apps
    if not names:
        ap.error("name an app or pass --all")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for n in names:
        if n not in manifest:
            print(f"  {n}: not in apps.json"); continue
        res = evaluate(manifest[n], a.after_upload)
        (OUT_DIR / f"{n}.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
        (OUT_DIR / f"{n}.md").write_text(render(res))
        fails = [r["id"] for r in res["rows"] if r["state"] == FAIL]
        human = [r["id"] for r in res["rows"] if r["state"] == HUMAN]
        print(f"  {n}: {res['done']}/{res['total']} — deliverable={'YES' if res['deliverable'] else 'NO'} "
              f"— FAIL {fails or 'none'} — needs a person {len(human)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
