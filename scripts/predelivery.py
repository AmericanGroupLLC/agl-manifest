#!/usr/bin/env python3
"""The iOS pre-delivery checklist: 46 checks, 5 gates, two stages, a release record — per app, per build.

    python3 scripts/predelivery.py BodyQuest --stage A       # Stage A on ~/agl/.dist/BodyQuest.ipa (the default)
    python3 scripts/predelivery.py BodyQuest --after-upload  # also section 6 (asks App Store Connect)
    python3 scripts/predelivery.py BodyQuest --sign 5.1 --build 202610151200 --by "Sri" \\
        --device "iPhone 15, iOS 27.0" --evidence "TestFlight build installed from the internal group; launched, played 3 games"
    python3 scripts/predelivery.py BodyQuest --stage B --build 202610151200   # is that TestFlight build submittable?
    python3 scripts/predelivery.py --all                     # every app, Stage A

Founder rule (2026-10-12): **no checklist pass, no delivery.** Split into two
stages by decision #48 (decision log, 2026-10-15):

  Stage A — before TestFlight (internal testers). The 20 `auto` checks in
            sections 1-5 must be PASS or n/a on the exact IPA (sha256).
            `gate_for_upload()`, called by testflight/transporter_upload.py's
            ipa_blocker() on every upload path (CI's run_batch.py included),
            refuses an IPA without a passing Stage A record for that file:
            store/predelivery/stage-a/<App>/<build>-<sha12>.json.
            `human` checks do not block Stage A.
  Stage B — before App Store review. Every `human` check signed (--sign)
            against the **TestFlight build number** that was tested, plus the
            Stage A record for that build, plus the submission-hold rules of
            2026-10-15 (no build older than the app's last lib/ commit; at most
            3 apps submitted in any 7 days; a 4.3(a) distinctness review, D.1).
            `gate_for_submission()` enforces it; every submit script calls it
            through testflight/submission_gate.rb (`--gate-submission`).

Each check is one of:
  auto   — measured here from the IPA, the source, or a live request
  human  — a person signs it off (--sign) with who, device/iOS and evidence;
           signatures are bound to the TestFlight build number, so a new build
           needs new ones. Where a human check has a measurable precondition
           (e.g. Google Sign-In configured), a failing precondition fails the
           check outright and Stage B cannot pass for that build.
  post   — section 6, only after upload: read from App Store Connect
           (testflight/build_delivery_state.rb, GET only).

Writes docs/predelivery/<App>.md (the checklist, rendered) and
docs/predelivery/<App>.json (plus a copy in <DIST>/predelivery/ for CI
artefacts); signatures live in store/predelivery/<App>.json; every submission
is appended to <DIST>/appstore-submissions.jsonl. Exit status: 0 when every
named app passes the requested stage, 1 otherwise.
Nothing here marks a check PASS without evidence printed next to it.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
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
from agl_paths import ROOT, MANIFEST as M, DIST, flutter_bin  # noqa: E402

# The pinned laptop SDK when it exists, else the one setup-agl installs on a
# runner (FLUTTER_ROOT). Was ROOT/.flutter-sdk unconditionally, which does not
# exist in CI and would have failed 3.1 on every runner.
FLUTTER = str(flutter_bin())
OUT_DIR = M / "docs/predelivery"
SIGN_DIR = M / "store/predelivery"
STAGE_A_DIR = SIGN_DIR / "stage-a"
SUBMISSION_LOG = DIST / "appstore-submissions.jsonl"
# Written by the submit scripts before the log existed. Neither carries a
# timestamp, so an entry counts at the file's mtime (never earlier than the
# real submission, so the 3-per-week count can only over-count).
LEGACY_SUBMISSION_FILES = (DIST / "appstore-resubmit-in-place.json", DIST / "appstore-submit-results.json")
SUBMITTED_STATES = ("submitted", "resubmitted")
MAX_APPS_PER_WEEK = 3
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"
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
    ("2.8", "auto", "Store policy audit (Apple + Google) — no FAIL"),
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
    ("Gate 4 — Privacy", "Purpose strings and entitlements are correct; no store-policy rule fails",
     ["2.1", "2.2", "2.3", "2.7", "2.8", "3.8"]),
    ("Gate 5 — Distribution", "Processed, in the internal group, installable by testers", ["6.2", "6.3", "6.7", "6.8"]),
]
PRE_UPLOAD_SECTIONS = ("1", "2", "3", "4", "5")
# Stage A (TestFlight internal): the 20 automated checks in sections 1-5.
# Gates 1 and 4 consist only of these, so Stage A meets them by construction.
STAGE_A_IDS = [cid for cid, kind, _t in CHECKS if kind == "auto" and cid.split(".")[0] in PRE_UPLOAD_SECTIONS]
# Stage B (App Store review): every human check, signed against the TestFlight
# build number, plus the reviews the 2026-10-15 submission hold added.
STAGE_B_IDS = [cid for cid, kind, _t in CHECKS if kind == "human"]
SUBMISSION_REVIEWS = [
    ("D.1", "4.3(a) distinctness review: this build is a distinct product from every other AGL app and "
            "substantially changed from the binary Apple rejected"),
]


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


# 1.7. TODO is matched case-sensitively: comment lines never reach the check
# (code_lines drops them), so a hit is a string or identifier. In run
# 38785102658 every case-insensitive hit was an ordinary word: MarkType.todo,
# IncidentStatus.todo, `final todo =`, Spanish 'Borrar todo' / 'Todo'.
PLACEHOLDER = re.compile(r"(?i:lorem ipsum|coming soon|placeholder text|debugShowCheckedModeBanner:\s*true|"
                         r"'/(debug|test|dev)[-_a-z]*')|\bTODO\b")
# 4.5.
DEV_ENDPOINT = re.compile(r"localhost|127\.0\.0\.1|10\.0\.2\.2|0\.0\.0\.0:|\.ngrok|\.local[:/]")
HINT_FIELD = re.compile(r"\b(hintText|helperText|labelText|hint|placeholder)\s*:")


def dev_endpoint_hit(line: str) -> bool:
    """A developer endpoint on this source line. A `.local` (mDNS) host in a
    field's hint text is an example of the user's own device, not a developer
    endpoint (PlantPulse's Home Assistant form: 'http://homeassistant.local:8123/
    api/webhook/…'); localhost, 127.0.0.1, 10.0.2.2, 0.0.0.0 and ngrok count anywhere."""
    found = {m.group(0) for m in DEV_ENDPOINT.finditer(line)}
    return bool(found) and not (all(x.startswith(".local") for x in found) and HINT_FIELD.search(line))


def run_auto(c: Ctx) -> dict:
    r: dict[str, tuple[str, str]] = {}
    no_ipa = (FAIL, f"no IPA at {c.ipa} — run `python3 scripts/build_ipa.py {c.repo}`")

    # 1.7 placeholder / debug / test-only content
    hits = [f"{f.relative_to(c.repo_dir)}:{i}" for f, i, l in code_lines(c.lib) if PLACEHOLDER.search(l)]
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
        # policy-urls.json is a laptop run artefact (~/agl/.dist), absent on a
        # CI runner. The URL itself is not laptop data: verify_policy_urls.py
        # derives it from the store record's slug, so derive it the same way.
        # It is still fetched live below — a missing page fails, never passes.
        from verify_policy_urls import BASE as POLICY_BASE
        url = f"{POLICY_BASE}/{rec.get('slug') or c.repo.lower()}/"
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
    st = {"PASS": PASS, "FAIL": FAIL, "n/a": NA}.get(st, HUMAN)
    if st == HUMAN and "server not probed" in detail:
        # The server half needs Supabase credentials: the laptop's `supabase`
        # CLI login, or SUPABASE_ANON_KEY on a runner. Without them this stays
        # open (blocks Stage A) and says why; it is never assumed to pass.
        detail += (" — no Supabase credentials on this runner (SUPABASE_ANON_KEY secret unset)" if IN_CI
                   else " — `supabase` CLI not logged in and SUPABASE_ANON_KEY unset")
    r["2.7"] = (st, detail)

    # 2.8 every applicable Apple/Google rule in store/policy/catalogue.json —
    # docs/store-policy/<App>.json, re-run here when stale. HUMAN and FOUNDER
    # rules are listed in that report; only a FAIL blocks this check.
    # Stage A (decision log 2026-10-15, c579677): only rules judged on the
    # binary itself block (catalogue `judged_on: binary`, apple — this is the
    # iOS TestFlight gate). App Review / listing rules are listed here and
    # block at Stage B (gate_for_submission -> policy_fails).
    try:
        from store_policy_audit import audit_for_gate
        pol = audit_for_gate(c.a)
        sm = pol["summary"]
        binary, review = policy_fails(pol)
        tail = (f" — docs/store-policy/{c.repo}.md (audited {pol['generated_at']}"
                + (f", re-run: {pol['rerun_reason']}" if pol.get("rerun_reason") else "") + ")")
        later = (f"; {len(review)} App Review/listing rule(s) fail and block Stage B: " + ", ".join(review)) if review else ""
        r["2.8"] = (FAIL, f"{len(binary)} binary rule(s) fail: " + ", ".join(binary) + later + tail) if binary else \
            (PASS, f"no binary rule fails ({sm.get('PASS', 0)} pass, {sm.get('HUMAN', 0)} for a person, "
                   f"{sm.get('FOUNDER', 0)} founder overall)" + later + tail)
    except Exception as e:  # a broken check must show, not pass
        r["2.8"] = (FAIL, f"store policy audit errored: {type(e).__name__}: {e}")

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

    # 3.3 also: App Store review refuses builds from a pre-release Xcode/SDK
    # (BUILD_SDK_NOT_ALLOWED / BUILD_XCODE_NOT_ALLOWED_FOR_APP_STORE_SUBMISSION).
    # 2026-10-14: SDK 24A94403 refused for 5 apps; 23F81a and 24A430 accepted.
    # Seed builds carry a 5-digit number after the train letter (24A94403,
    # 24A94232); some releases have 4 (16C5032a), so 4 digits is not flagged.
    pre = [f"{k} {c.info.get(k)}" for k in ("DTSDKBuild", "DTXcodeBuild")
           if re.fullmatch(r"\d+[A-Z]\d{5,}[a-z]?", str(c.info.get(k) or ""))]
    if pre and r.get("3.3", (None,))[0] != FAIL:
        r["3.3"] = (FAIL, "built with a pre-release Xcode/SDK (" + ", ".join(pre) + ") — Apple refuses it for "
                    "review; build with a release Xcode (CI macos-latest)")
    elif r.get("3.3", (None,))[0] == PASS:
        r["3.3"] = (PASS, r["3.3"][1] + f"; SDK {c.info.get('DTSDKBuild')}, Xcode {c.info.get('DTXcodeBuild')}")

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

    # 4.4 credentials the code reads that are empty in a release build —
    # measured on the current source with api_vendor_audit's own patterns.
    # It read the committed docs/api-vendor-keys.json, last regenerated
    # 2026-10-13, so run 38785102658 failed 6 apps on GOOGLE_IOS_CLIENT_ID
    # reads the Real Apps rebuilds had already removed.
    from api_vendor_audit import credential_reads
    keys_now = credential_reads(c.lib, c.repo_dir)
    optional = ("SENTRY", "POSTHOG")
    empty = [f"{k} ({v['sites'][0]})" for k, v in keys_now.items() if not v.get("default") and not k.startswith(optional)]
    r["4.4"] = (FAIL, "empty in this build: " + ", ".join(empty) +
                " — wire it, or remove the feature that needs it") if empty else \
        (PASS, f"every credential the code reads ({len(keys_now)}) has a value in the release build")

    # 4.5 localhost / developer endpoints, in source and in the shipped binary
    src = [f"{f.relative_to(c.repo_dir)}:{i}" for f, i, l in code_lines(c.lib) if dev_endpoint_hit(l)]
    app_bin = c.app_dir / "Frameworks/App.framework/App"
    in_bin = sorted({m.group(0).decode() for m in re.finditer(rb"https?://(localhost|127\.0\.0\.1|10\.0\.2\.2)[:/\w.-]*",
                                                              app_bin.read_bytes())}) if app_bin.exists() else []
    r["4.5"] = (FAIL, "source: " + ", ".join(src[:5]) + (f"; binary: {in_bin[:3]}" if in_bin else "")) \
        if (src or in_bin) else (PASS, "no localhost/emulator/dev endpoints in lib/ or the App binary")
    return r


def policy_fails(pol: dict) -> tuple[list[str], list[str]]:
    """FAILing rules of a store-policy audit, split by store/policy/catalogue.json
    `judged_on`: (apple binary rules — block Stage A, every other rule — block
    Stage B). A rule missing from the catalogue or without a class counts as review."""
    cat = {(x["store"], x["ref"]): x.get("judged_on", "review")
           for x in json.loads((M / "store/policy/catalogue.json").read_text())["rules"]}
    binary, review = [], []
    for x in pol["rules"]:
        if x["state"] != "FAIL":
            continue
        name = f"{x['store']} {x['ref']}"
        (binary if x["store"] == "apple" and cat.get((x["store"], x["ref"])) == "binary" else review).append(name)
    return binary, review


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
    """{"builds": {"<TestFlight build number>": {"<check id>": {by, device, evidence, date}}}}"""
    f = SIGN_DIR / f"{repo}.json"
    data = json.loads(f.read_text()) if f.exists() else {}
    data.setdefault("builds", {})
    return data


def signs_for_build(repo: str, build: str | None) -> dict:
    return load_signs(repo)["builds"].get(str(build or "-"), {})


def stage_a_state(rows: list[dict]) -> dict:
    """Stage A = the 20 auto checks of sections 1-5, PASS or n/a. Human checks do not block it."""
    by = {r["id"]: r for r in rows}
    open_ = [cid for cid in STAGE_A_IDS if by[cid]["state"] not in (PASS, NA)]
    # A failing precondition on a human check is measured, so it is reported
    # now; it blocks Stage B (that build can never be signed off), not Stage A.
    pre_fail = [cid for cid in STAGE_B_IDS if by[cid]["state"] == FAIL]
    return {"passed": not open_, "open": open_, "stage_b_blocked_by": pre_fail,
            "checks": len(STAGE_A_IDS)}


def evaluate(a: dict, after_upload: bool) -> dict:
    c = Ctx(a)
    auto = run_auto(c)
    pre = preconditions(c, auto)
    signs = signs_for_build(c.repo, c.build)
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
            st, ev = PASS, f"signed by {s['by']} on {s['date']} for build {c.build} ({s['device']}): {s['evidence']}"
        else:
            st, ev = HUMAN, f"needs a person (Stage B): --sign {cid} --build <TestFlight build>"
        rows.append({"id": cid, "section": cid.split(".")[0], "kind": kind, "text": text, "state": st, "evidence": ev})
    by = {r["id"]: r for r in rows}
    gates = [{"gate": g, "rule": rule, "checks": ids,
              "met": all(by[i]["state"] in (PASS, NA) for i in ids)} for g, rule, ids in GATES]
    stage_a = stage_a_state(rows)
    done = sum(r["state"] in (PASS, NA) for r in rows)
    head = sh(["git", "-C", str(c.repo_dir), "rev-parse", "--short", "HEAD"])[1].strip()
    record = {
        "app": c.repo, "store_name": ((json.loads((M / f"store/apps/{c.repo}.json").read_text()).get("copy") or {})
                                      .get("en") or {}).get("title") if (M / f"store/apps/{c.repo}.json").exists() else c.repo,
        "version": c.info.get("CFBundleShortVersionString"), "build": c.build or None,
        "git_commit": head, "configuration": "Release", "ipa_sha256": c.ipa_sha,
        "measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "runner": (f"ci run {os.environ.get('GITHUB_RUN_ID')}" if IN_CI else "local"),
        "devices": sorted({s["device"] for s in signs.values()}),
        "outstanding": [f"{r['id']} {r['text']}: {r['evidence']}" for r in rows if r["state"] == FAIL],
    }
    # "deliverable" is what the upload gate reads: Stage A (decision #48).
    return {"record": record, "rows": rows, "gates": gates, "stage_a": stage_a,
            "deliverable": stage_a["passed"], "done": done, "total": len(rows)}


def render(res: dict) -> str:
    rec, rows = res["record"], res["rows"]
    sa = res.get("stage_a") or stage_a_state(rows)
    pct = round(100 * res["done"] / res["total"])
    mark = {PASS: "[x]", NA: "[x]", FAIL: "[ ] ❌", HUMAN: "[ ] 👤"}
    out = [f"# iOS pre-delivery checklist — {rec['store_name']}", "",
           f"Internal TestFlight · version {rec['version']} ({rec['build']}) · commit `{rec['git_commit']}` · "
           f"measured {rec['measured_at']} ({rec.get('runner', 'local')})", "",
           f"**{pct}% complete — {res['done']} of {res['total']} checks.**", "",
           f"- **Stage A (TestFlight internal): {'PASS' if sa['passed'] else 'NOT PASSED'}** — "
           f"the {sa['checks']} automated checks in sections 1–5 on this exact IPA"
           + (f"; open: {', '.join(sa['open'])}" if sa["open"] else "") + ". The upload gate refuses otherwise.",
           "- **Stage B (App Store review)** — every 👤 check signed against the TestFlight build number, "
           "plus D.1 and the 2026-10-15 submission-hold rules: "
           f"`python3 scripts/predelivery.py {rec['app']} --stage B --build <n>`"
           + (f". Already blocked for this build by failed preconditions: {', '.join(sa['stage_b_blocked_by'])}"
              if sa["stage_b_blocked_by"] else "") + ".", "",
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


def sign(repo: str, cid: str, build: str | None, by: str, device: str, evidence: str) -> None:
    ids = {c[0]: c for c in CHECKS}
    reviews = {r[0] for r in SUBMISSION_REVIEWS}
    if cid not in reviews and (cid not in ids or ids[cid][1] == "auto"):
        sys.exit(f"{cid} is not a check a person signs (auto checks are measured, not signed)")
    if not by or not device or not evidence:
        sys.exit("--by, --device and --evidence are all required")
    if not build or not str(build).isdigit():
        sys.exit("--build <TestFlight build number> is required: a signature is bound to the build that was tested")
    data = load_signs(repo)
    data["builds"].setdefault(str(build), {})[cid] = {
        "by": by, "device": device, "evidence": evidence, "date": datetime.date.today().isoformat()}
    SIGN_DIR.mkdir(parents=True, exist_ok=True)
    (SIGN_DIR / f"{repo}.json").write_text(json.dumps(data, indent=1) + "\n")
    print(f"  signed {cid} for {repo} TestFlight build {build}")


# ------------------------------------------------------------------ Stage A records

def ipa_build(ipa: pathlib.Path) -> str | None:
    """CFBundleVersion inside the IPA — the number App Store Connect will list."""
    try:
        with zipfile.ZipFile(ipa) as z:
            name = next(n for n in z.namelist() if n.startswith("Payload/") and n.endswith(".app/Info.plist")
                        and n.count("/") == 2)
            return str(plistlib.loads(z.read(name)).get("CFBundleVersion") or "") or None
    except Exception:
        return None


def stage_a_path(repo: str, build: str, sha: str) -> pathlib.Path:
    return STAGE_A_DIR / repo / f"{build}-{sha[:12]}.json"


def write_stage_a_record(res: dict) -> pathlib.Path | None:
    """A passing Stage A, kept per build so Stage B can find it after the IPA is gone."""
    rec = res["record"]
    if not (res["stage_a"]["passed"] and rec.get("build") and rec.get("ipa_sha256")):
        return None
    rows = {r["id"]: r for r in res["rows"]}
    out = {"record": rec, "stage_a": res["stage_a"],
           "checks": {cid: {"state": rows[cid]["state"], "evidence": rows[cid]["evidence"]} for cid in STAGE_A_IDS},
           # Human checks a precondition already decided (n/a, or FAIL) for this build.
           "preconditions": {cid: {"state": rows[cid]["state"], "evidence": rows[cid]["evidence"]}
                             for cid in STAGE_B_IDS if rows[cid]["state"] in (NA, FAIL)}}
    p = stage_a_path(rec["app"], rec["build"], rec["ipa_sha256"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, default=str) + "\n")
    return p


def stage_a_records(repo: str, build: str) -> list[dict]:
    d = STAGE_A_DIR / repo
    out = []
    for f in sorted(d.glob(f"{build}-*.json")) if d.is_dir() else []:
        try:
            out.append(json.loads(f.read_text()))
        except ValueError:
            continue
    return out


def gate_for_upload(repo: str, ipa: pathlib.Path) -> str | None:
    """Used by transporter_upload.ipa_blocker (every upload path, CI included):
    why this IPA may not go to TestFlight, or None. Stage A, bound to the IPA's sha256."""
    h, build = sha256(ipa), ipa_build(ipa)
    if build:
        p = stage_a_path(repo, build, h)
        if p.exists():
            try:
                rec = json.loads(p.read_text())
            except ValueError:
                rec = {}
            if rec.get("stage_a", {}).get("passed") and rec.get("record", {}).get("ipa_sha256") == h:
                return None
    # No passing record for this file: say why, from the latest run on file.
    for f in (DIST / "predelivery" / f"{repo}.json", OUT_DIR / f"{repo}.json"):
        if not f.exists():
            continue
        res = json.loads(f.read_text())
        if res["record"].get("ipa_sha256") != h:
            continue
        sa = res.get("stage_a") or stage_a_state(res["rows"])
        if not sa["passed"]:
            return f"pre-delivery Stage A not passed for build {build}; open: {', '.join(sa['open'])}"
        return (f"Stage A passed for this IPA but its record {stage_a_path(repo, build or '?', h).relative_to(M)} "
                "is missing — re-run `predelivery.py --stage A`")
    if not (OUT_DIR / f"{repo}.json").exists() and not (DIST / "predelivery" / f"{repo}.json").exists():
        return f"no pre-delivery checklist — run `python3 scripts/predelivery.py {repo} --stage A`"
    return "the pre-delivery checklist was run on a different IPA — re-run it on this build"


# ------------------------------------------------------------------ Stage B and the submission hold

def _parse_time(s: str | None) -> datetime.datetime | None:
    if not s:
        return None
    try:
        t = datetime.datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()


def _app(repo: str) -> dict | None:
    return next((x for x in json.loads((M / "apps.json").read_text())["apps"] if x["repo"] == repo), None)


def last_lib_commit(a: dict, fetch: bool = True) -> tuple[str, datetime.datetime] | str:
    """(sha, commit time) of the newest commit touching the app's lib/ on its main line, or why unknown."""
    repo_dir = ROOT / a["repo"]
    rel = (a.get("dir") or ".").strip("/")
    lib = "lib" if rel in ("", ".") else f"{rel}/lib"
    if not (repo_dir / ".git").exists():
        return f"{repo_dir} is not a git checkout — cannot find the app's last lib/ commit"
    if fetch and sh(["git", "-C", str(repo_dir), "remote"])[1].split():
        rc, out = sh(["git", "-C", str(repo_dir), "fetch", "--quiet", "origin"], timeout=120)
        if rc != 0:
            return f"could not fetch origin for {a['repo']} to find its newest lib/ commit: {out.strip()[-160:]}"
    best = None
    for ref in ("HEAD", "origin/main", "origin/master"):
        if sh(["git", "-C", str(repo_dir), "rev-parse", "--verify", "--quiet", ref])[0] != 0:
            continue
        rc, out = sh(["git", "-C", str(repo_dir), "log", "-1", "--format=%H %cI", ref, "--", lib])
        parts = out.strip().split()
        if rc == 0 and len(parts) == 2:
            t = _parse_time(parts[1])
            if t and (best is None or t > best[1]):
                best = (parts[0], t)
    return best or f"no commit touches {lib} in {a['repo']}"


def _backfill_submission_log() -> None:
    """Seed the log once from the timestamp-less JSON the submit scripts used to
    leave behind, before a later run overwrites them and the history is lost."""
    if SUBMISSION_LOG.exists():
        return
    lines = []
    for f in LEGACY_SUBMISSION_FILES:
        if not f.exists():
            continue
        at = datetime.datetime.fromtimestamp(f.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        try:
            data = json.loads(f.read_text())
        except ValueError:
            continue
        for repo, v in data.items():
            if isinstance(v, dict) and v.get("status") in SUBMITTED_STATES:
                lines.append({"at": at, "repo": repo, "build": v.get("build"), "status": v["status"],
                              "script": f.name, "source": f"backfill: {f.name} mtime (no timestamp in file)"})
    if lines:
        SUBMISSION_LOG.parent.mkdir(parents=True, exist_ok=True)
        SUBMISSION_LOG.write_text("".join(json.dumps(x) + "\n" for x in lines))


def submissions(since: datetime.datetime, asc: list[dict] | None = None) -> list[dict] | str:
    """Every App Review submission at or after `since`, or why the history cannot be trusted.

    `asc` is App Store Connect's own record (reviewSubmissions.submittedDate,
    read by testflight/submission_gate.rb). Without it only the local log and
    the legacy files count, and with none of those the answer is "unknown"."""
    _backfill_submission_log()
    sources = [SUBMISSION_LOG, *LEGACY_SUBMISSION_FILES]
    if asc is None and not any(f.exists() for f in sources):
        return (f"no submission history at {SUBMISSION_LOG} (nor {', '.join(f.name for f in LEGACY_SUBMISSION_FILES)}) "
                "and none from App Store Connect — cannot prove the 3-apps-per-week limit")
    out = []
    for x in asc or []:
        t = _parse_time(x.get("at"))
        if t and t >= since and x.get("repo"):
            out.append({**x, "status": "submitted"})
    if SUBMISSION_LOG.exists():
        for line in SUBMISSION_LOG.read_text().splitlines():
            try:
                x = json.loads(line)
            except ValueError:
                continue
            t = _parse_time(x.get("at"))
            if t and t >= since and x.get("status") in SUBMITTED_STATES:
                out.append(x)
    # The legacy files still count (at their mtime) in case the log was seeded
    # before they were last written.
    for f in LEGACY_SUBMISSION_FILES:
        if not f.exists():
            continue
        t = datetime.datetime.fromtimestamp(f.stat().st_mtime).astimezone()
        if t < since:
            continue
        try:
            data = json.loads(f.read_text())
        except ValueError:
            continue
        out += [{"at": t.isoformat(timespec="seconds"), "repo": r, "status": v["status"], "script": f.name}
                for r, v in data.items() if isinstance(v, dict) and v.get("status") in SUBMITTED_STATES]
    return out


def record_submission(repo: str, build: str | None, status: str, script: str) -> None:
    _backfill_submission_log()
    SUBMISSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBMISSION_LOG, "a") as fh:
        fh.write(json.dumps({"at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                             "repo": repo, "build": build, "status": status, "script": script}) + "\n")


def stage_b_open(repo: str, build: str) -> list[str]:
    """What stops this TestFlight build from passing Stage B (checklist part only)."""
    why = []
    recs = [r for r in stage_a_records(repo, build) if r.get("stage_a", {}).get("passed")]
    if not recs:
        why.append(f"no passing Stage A record for build {build} (store/predelivery/stage-a/{repo}/{build}-*.json)")
        pre = {}
    else:
        pre = recs[-1].get("preconditions") or {}
    signs = signs_for_build(repo, build)
    failed_pre = [f"{cid} ({pre[cid]['evidence']})" for cid in STAGE_B_IDS if pre.get(cid, {}).get("state") == FAIL]
    if failed_pre:
        why.append(f"build {build} fails measured preconditions, so it cannot be signed off: " + "; ".join(failed_pre))
    unsigned = [cid for cid in STAGE_B_IDS if cid not in signs and pre.get(cid, {}).get("state") != NA]
    unsigned += [cid for cid, _t in SUBMISSION_REVIEWS if cid not in signs]
    if unsigned:
        why.append(f"not signed for build {build}: {', '.join(unsigned)} "
                   f"(`predelivery.py {repo} --sign <id> --build {build} --by … --device … --evidence …`)")
    return why


def gate_for_submission(repo: str, build_number: str, uploaded_at: str | None = None,
                        now: datetime.datetime | None = None, asc_submissions: list[dict] | None = None) -> str | None:
    """Used by every App Review submit path (testflight/submission_gate.rb): why this
    TestFlight build may not be submitted, or None. Stage B + the 2026-10-15 submission hold."""
    build = str(build_number or "").strip()
    a = _app(repo)
    if not a:
        return f"{repo} is not in apps.json"
    if not build.isdigit():
        return f"no TestFlight build number given ({build_number!r})"
    now = now or datetime.datetime.now().astimezone()
    why = stage_b_open(repo, build)

    # Hold rule 1: never a build older than the app's rebuilt code.
    up = _parse_time(uploaded_at)
    if up is None:
        rows = json.loads((M / "docs/asc-build-state.json").read_text())
        up = next((_parse_time(x.get("uploaded_at")) for x in (rows if isinstance(rows, list) else rows.get("apps", []))
                   if isinstance(x, dict) and x.get("repo") == repo and str(x.get("version")) == build), None)
    lib = last_lib_commit(a)
    if up is None:
        why.append(f"upload date of build {build} unknown (pass it from App Store Connect, or refresh "
                   "docs/asc-build-state.json) — cannot prove it is newer than the app's code")
    if isinstance(lib, str):
        why.append(lib)
    elif up is not None and up < lib[1]:
        why.append(f"build {build} was uploaded {up.isoformat(timespec='minutes')}, before the last lib/ commit "
                   f"{lib[0][:9]} ({lib[1].isoformat(timespec='minutes')}) — build a new one from current main "
                   "(submission hold, 2026-10-15)")
    if not isinstance(lib, str):
        # The binary, not just the upload, must contain that commit: the Stage A
        # record says which commit the IPA was checked against.
        commits = [r["record"].get("git_commit") for r in stage_a_records(repo, build)
                   if r.get("stage_a", {}).get("passed") and r.get("record", {}).get("git_commit")]
        if commits and not any(sh(["git", "-C", str(ROOT / repo), "merge-base", "--is-ancestor", lib[0], c])[0] == 0
                               for c in commits):
            why.append(f"build {build} was checked at commit {', '.join(commits)}, which does not contain the last "
                       f"lib/ commit {lib[0][:9]} — build a new one from current main")

    # Every store-policy rule blocks submission; the binary ones were already
    # proven on this build's IPA by Stage A, so only the rest are read here,
    # from the current audit (re-run when stale).
    try:
        from store_policy_audit import audit_for_gate
        _binary, review = policy_fails(audit_for_gate(a))
        if review:
            why.append(f"{len(review)} App Review/listing store-policy rule(s) fail: {', '.join(review)} "
                       f"(docs/store-policy/{repo}.md)")
    except Exception as e:  # fail closed
        why.append(f"store policy audit could not run: {type(e).__name__}: {e}")

    # Hold rule 3: at most 3 apps a week, never dozens at once.
    subs = submissions(now - datetime.timedelta(days=7), asc_submissions)
    if isinstance(subs, str):
        why.append(subs)
    else:
        others = sorted({s["repo"] for s in subs if s.get("repo") and s["repo"] != repo})
        if len(others) >= MAX_APPS_PER_WEEK:
            why.append(f"{len(others)} other app(s) were submitted in the last 7 days ({', '.join(others[:8])}"
                       f"{'…' if len(others) > 8 else ''}); the hold allows at most {MAX_APPS_PER_WEEK} apps a week")
    return "; ".join(why) or None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--stage", choices=["A", "B"], default="A",
                    help="A (default): the 20 automated checks on the IPA, before TestFlight. "
                         "B: is TestFlight build --build ready for App Review?")
    ap.add_argument("--build", help="TestFlight build number (for --sign, --stage B, --gate-submission)")
    ap.add_argument("--after-upload", action="store_true")
    ap.add_argument("--sign")
    ap.add_argument("--by")
    ap.add_argument("--device")
    ap.add_argument("--evidence")
    ap.add_argument("--gate-submission", metavar="APP",
                    help="exit 0 only if --build of APP may be submitted for App Review (submit scripts call this)")
    ap.add_argument("--uploaded-at", help="with --gate-submission: the build's uploadedDate from App Store Connect")
    ap.add_argument("--asc-submissions", help="with --gate-submission: JSON list of {repo, at} — App Store Connect's "
                                              "submittedDate for recent review submissions")
    ap.add_argument("--record-submission", metavar="APP", help="append a submission of --build to the log")
    ap.add_argument("--status", default="submitted")
    ap.add_argument("--script", default="manual")
    a = ap.parse_args()
    if a.gate_submission:
        asc = json.loads(pathlib.Path(a.asc_submissions).read_text()) if a.asc_submissions else None
        why = gate_for_submission(a.gate_submission, a.build, a.uploaded_at, asc_submissions=asc)
        print(f"REFUSED {a.gate_submission} build {a.build}: {why}" if why
              else f"PASS {a.gate_submission} build {a.build}: Stage B complete and the submission hold allows it")
        return 3 if why else 0
    if a.record_submission:
        record_submission(a.record_submission, a.build, a.status, a.script)
        print(f"  recorded {a.status} of {a.record_submission} build {a.build} -> {SUBMISSION_LOG}")
        return 0
    manifest = {x["repo"]: x for x in json.loads((M / "apps.json").read_text())["apps"]}
    if a.sign:
        if len(a.apps) != 1:
            ap.error("--sign takes exactly one app")
        sign(a.apps[0], a.sign, a.build, a.by, a.device, a.evidence)
        if a.stage != "B":
            return 0
    names = list(manifest) if a.all else a.apps
    if not names:
        ap.error("name an app or pass --all")
    if a.stage == "B":
        if not a.build:
            ap.error("--stage B needs --build <TestFlight build number>")
        bad = 0
        for n in names:
            why = gate_for_submission(n, a.build) if n in manifest else "not in apps.json"
            bad += bool(why)
            print(f"  {n} build {a.build}: Stage B {'NOT PASSED — ' + why if why else 'PASS (submittable)'}")
        print("  (3-apps-per-week counted from the local log only here; the submit scripts also count "
              "App Store Connect's submittedDate via testflight/submission_gate.rb)")
        return 1 if bad else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bad = 0
    for n in names:
        if n not in manifest:
            print(f"  {n}: not in apps.json"); bad += 1; continue
        res = evaluate(manifest[n], a.after_upload)
        blob, md = json.dumps(res, indent=1, default=str) + "\n", render(res)
        (OUT_DIR / f"{n}.json").write_text(blob)
        (OUT_DIR / f"{n}.md").write_text(md)
        # This run's copy, outside the committed tree, for CI artefacts.
        (DIST / "predelivery").mkdir(parents=True, exist_ok=True)
        (DIST / "predelivery" / f"{n}.json").write_text(blob)
        (DIST / "predelivery" / f"{n}.md").write_text(md)
        rec_path = write_stage_a_record(res)
        sa = res["stage_a"]
        bad += not sa["passed"]
        fails = [r["id"] for r in res["rows"] if r["state"] == FAIL]
        human = [r["id"] for r in res["rows"] if r["state"] == HUMAN]
        print(f"  {n}: build {res['record']['build']} — Stage A {'PASS' if sa['passed'] else 'NOT PASSED'} "
              f"({sa['checks'] - len(sa['open'])}/{sa['checks']} automated)"
              + (f" — open: {', '.join(sa['open'])}" if sa["open"] else "")
              + f" — {res['done']}/{res['total']} overall — FAIL {fails or 'none'} — needs a person {len(human)}"
              + (f" — record {rec_path.relative_to(M)}" if rec_path else ""))
        for r in res["rows"]:
            if r["id"] in sa["open"]:
                print(f"      {r['id']} {r['state']}: {r['evidence'][:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
