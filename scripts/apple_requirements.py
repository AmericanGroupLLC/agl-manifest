#!/usr/bin/env python3
"""Every requirement App Review has raised against our apps, each with the check that enforces it.

    python3 scripts/apple_requirements.py            # -> docs/apple-requirements.json + docs/APPLE_REQUIREMENTS.md
    python3 scripts/apple_requirements.py MyCard     # one app, printed

store_checklist.py imports evaluate() and adds every row below to the
submission gate, so store_watch.py (scheduled) and ship.yml (CI) refuse an app
that fails one. A requirement is added here the day Apple first raises it,
with Apple's own words and the apps it was raised against, and its check
reads the artefact Apple inspects — the uploaded screenshots, the IPA's
binaries, the review notes as stored — not a proxy for it.

The catalogue is built from the Resolution Center text of all 42 rejected
apps (rejection_reasons.rb, 2026-10-08). Three kinds of finding are not
here because no check can satisfy them: 4.3 (answered in writing; the gate
row "4.3 differentiation statement" covers the draft), 5.6 (account-level;
store_watch.py ACCOUNT_FREEZE), and the 2.1 screen recording on a physical
device (a person records it; this reports whether one is on file).
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import zipfile
import plistlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "testflight"))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402

OK, NO, HUMAN, NA = "PASS", "FAIL", "HUMAN", "n/a"


def _load(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text())
    except Exception:
        return default


def _dart(d: pathlib.Path) -> dict[pathlib.Path, str]:
    lib = d / "lib"
    out = {}
    for f in (lib.rglob("*.dart") if lib.is_dir() else []):
        if "/generated/" in str(f) or f.name.endswith((".g.dart", ".freezed.dart")):
            continue
        try:
            out[f] = f.read_text(errors="ignore")
        except OSError:
            pass
    return out


def _code_lines(src: str):
    for n, line in enumerate(src.splitlines(), 1):
        s = line.strip()
        if not s.startswith(("//", "*", "/*")):
            yield n, line


# ---------------------------------------------------------------- checks
# Each takes the app context and returns (state, detail).

def screenshots_show_app(ctx):
    """2.3.3 — judged on what App Store Connect holds (screenshot_audit.py)."""
    a = ctx["shots"].get(ctx["repo"])
    if not a:
        return HUMAN, ("not audited — run asc_screenshots.rb then screenshot_audit.py")
    return (OK, f"v{a.get('version')}: every set shows the app in use") if a["verdict"] == "PASS" \
        else (NO, "; ".join(a["problems"]))


def launches_ios27_iphone_ipad(ctx):
    """2.1(a) — the binary adopts UIScene, and a build launched on both device families."""
    ipa = DIST / f"{ctx['repo']}.ipa"
    detail = []
    if ipa.exists():
        with zipfile.ZipFile(ipa) as z:
            n = next((x for x in z.namelist()
                      if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", x)), None)
            info = plistlib.loads(z.read(n)) if n else {}
        if not info.get("UIApplicationSceneManifest"):
            return NO, f"{ipa.name} build {info.get('CFBundleVersion')} has no UIApplicationSceneManifest — crashes on iOS 27"
        detail.append(f"IPA build {info.get('CFBundleVersion')} adopts UIScene")
        ipad_family = 2 in (info.get("UIDeviceFamily") or [])
    else:
        return HUMAN, "no staged IPA to inspect"
    sim = ctx["sim"].get(ctx["repo"], {})
    iphone, ipad = sim.get("ios"), sim.get("ipad")
    if iphone and iphone != "running":
        return NO, f"iPhone simulator: {iphone}"
    if ipad_family and ipad and ipad != "running":
        return NO, f"iPad simulator: {ipad}"
    if ipad_family and not ipad:
        return HUMAN, "; ".join(detail + ["no iPad launch recorded — sim_install.py --ios --ipad"])
    return OK, "; ".join(detail + [f"iPhone {iphone or '?'}", f"iPad {ipad or 'n/a'}"])


AUTH_URL = re.compile(r"(?i)(log-?in|sign-?in|sign-?up|register|oauth|/auth\b|/authorize)")
LAUNCH = re.compile(r"\b(launchUrl|launchUrlString|launch)\s*\(")


def sign_in_inside_app(ctx):
    """4 — sign-in and registration must not leave for the default browser."""
    bad = []
    for f, src in ctx["dart"].items():
        lines = list(_code_lines(src))
        for i, (n, line) in enumerate(lines):
            if "externalApplication" in line and ("signInWithOAuth" in src or AUTH_URL.search(line)):
                bad.append(f"{f.relative_to(ctx['d'])}:{n}")
                continue
            if LAUNCH.search(line):
                window = " ".join(l for _, l in lines[max(0, i - 3):i + 4])
                if AUTH_URL.search(window) and "inAppBrowserView" not in window \
                        and "inAppWebView" not in window:
                    bad.append(f"{f.relative_to(ctx['d'])}:{n}")
    return (NO, "opens the default browser to sign in: " + ", ".join(sorted(set(bad))[:5])) \
        if bad else (OK, "no sign-in flow leaves the app")


IAP_CODE = re.compile(r"InAppPurchase\.instance|package:in_app_purchase/|package:purchases_flutter/"
                      r"|Purchases\.(configure|purchase)")


def iap_submitted_with_app(ctx):
    """2.1(b) / 3.1.1 — products the binary sells must be configured and submittable."""
    uses = [f for f, s in ctx["dart"].items() if IAP_CODE.search(s)]
    if not uses:
        return NA, "no in-app purchase code"
    rec = ctx["iap"].get(ctx["repo"]) if ctx["iap"] else None
    if rec is None:
        return HUMAN, ("sells in-app purchases; product state not measured — "
                       "run scripts/testflight/iap_readiness.rb")
    problems = rec.get("issues") or []
    return (NO, "; ".join(problems)) if problems else (OK, f"{len(rec.get('products', []))} product(s) ready")


ATT_REQ = re.compile(r"requestTrackingAuthorization")


def att_prompt_when_tracking(ctx):
    """2.1 / 5.1.2 — an app that asks for tracking must show the prompt before tracking."""
    asks = any(ATT_REQ.search(s) for s in ctx["dart"].values())
    plist = ctx["d"] / "ios/Runner/Info.plist"
    has_key = plist.exists() and b"NSUserTrackingUsageDescription" in plist.read_bytes()
    if asks and not has_key:
        return NO, "requests tracking but Info.plist has no NSUserTrackingUsageDescription"
    if has_key and not asks:
        return NO, ("declares NSUserTrackingUsageDescription but never shows the prompt — "
                    "Apple: 'we are unable to locate the App Tracking Transparency permission request'")
    if asks:
        proof = sorted((DIST / "att-proof").glob(f"{ctx['repo']}*.png")) if (DIST / "att-proof").is_dir() else []
        return (OK, f"prompt captured: {proof[-1].name}") if proof else \
            (HUMAN, "requests tracking; no capture of the prompt appearing on a fresh install")
    return NA, "does not request tracking (App Privacy must not declare tracking)"


def vpn_statement(ctx):
    """Automated VPN analysis — a binary that links NetworkExtension needs a written answer."""
    ipa = DIST / f"{ctx['repo']}.ipa"
    if not ipa.exists():
        return HUMAN, "no staged IPA to inspect"
    from privacy_scan import vpn_scan
    hits = vpn_scan(ipa)
    if not hits:
        return NA, "binary does not link NetworkExtension"
    notes = (ctx["rec"].get("review_information") or {}).get("notes") or ""
    return (OK, f"{', '.join(hits)}; review notes answer the VPN questions") \
        if "VPN FUNCTIONALITY" in notes else \
        (NO, f"{', '.join(hits)} — Apple will ask about VPN functionality; add a "
             "'VPN FUNCTIONALITY' section to review_information.notes")


# Every Supabase call that can create an account, not only signUp(): an OTP
# sign-in creates the user unless shouldCreateUser is false, and OAuth or an
# Apple/Google ID token creates one on first use.
SIGN_UP = re.compile(r"\bsignUp\s*\(|createUserWithEmailAndPassword|signInWithOtp|"
                     r"signInWithOAuth|signInWithIdToken|signInWithApple|"
                     r"FirebaseAuth\.instance\.signInWith(Credential|Provider)")
# The one deletion that deletes: public.delete_user() in Supabase
# (AmericanGroupLLC-Backend/supabase/migrations/20261009_delete_user.sql),
# called as rpc('delete_user'). Measured 2026-10-08, before it existed, the
# "deletions" in the apps were: Kinnav signs out and clears local storage;
# DriftDate invokes an Edge Function 'wipe-me' that answers 404; GroceryMatch
# sends DELETE to api.americangroupllc.com, which has no DNS record. A text
# match on "deleteAccount" passed all three.
DELETE_CALL = re.compile(r"""rpc\(\s*['"]delete_user['"]""")


def _rpc_exists(name: str) -> bool | None:
    import subprocess, urllib.request, urllib.error
    try:
        keys = json.loads(subprocess.run(
            ["supabase", "projects", "api-keys", "--project-ref", "smvvjivvlprjhzhoizym", "-o", "json"],
            capture_output=True, text=True, timeout=60).stdout)
        anon = next(k["api_key"] for k in keys if k["name"] == "anon")
        req = urllib.request.Request(
            f"https://smvvjivvlprjhzhoizym.supabase.co/rest/v1/rpc/{name}", data=b"{}", method="POST",
            headers={"apikey": anon, "Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=20)
            return True
        except urllib.error.HTTPError as e:
            # PGRST202: no such function. Anything else (401/400 "not
            # authenticated") means it exists and refused an anonymous caller.
            return "PGRST202" not in e.read().decode(errors="ignore")
    except Exception:
        return None


def account_deletion_in_app(ctx):
    """5.1.1(v) — 'Account deletion is required in apps that support account creation.'"""
    if not any(SIGN_UP.search(s) for s in ctx["dart"].values()):
        return NA, "no account creation"
    hits = [f for f, s in ctx["dart"].items() if DELETE_CALL.search(s)]
    if not hits:
        return NO, "creates accounts but nothing deletes the account on the server (rpc('delete_user'))"
    live = ctx["rpc_delete_user"]
    where = hits[0].relative_to(ctx["d"])
    if live is False:
        return NO, f"{where} calls delete_user, which is not applied in Supabase (MA-044)"
    return (OK if live else HUMAN), f"rpc('delete_user') in {where}" + ("" if live else "; server not probed")


UGC = re.compile(r"(?i)\b(createPost|addComment|postComment|sendMessage|submitReview|uploadPost|"
                 r"from\(['\"](posts|comments|messages|reviews)['\"]\)\.insert)")
REPORT = re.compile(r"(?i)\breport(ing)?\b.{0,30}(content|post|user|comment|message|abuse)|reportContent|flagContent")
BLOCK = re.compile(r"(?i)block(ed)?[_ ]?user|blockUser|\bblock\b.{0,20}(user|account)")


def ugc_report_and_block(ctx):
    """1.2 — 'Any user-generated content, including the required content reporting and blocking mechanisms.'"""
    if not any(UGC.search(s) for s in ctx["dart"].values()):
        return NA, "no user-generated content found"
    rep = any(REPORT.search(s) for s in ctx["dart"].values())
    blk = any(BLOCK.search(s) for s in ctx["dart"].values())
    missing = [n for n, ok in (("reporting", rep), ("blocking", blk)) if not ok]
    return (NO, "user-generated content without " + " and ".join(missing)) if missing \
        else (OK, "reporting and blocking present")


def recording_on_file(ctx):
    """2.1 item 1 — a screen recording on a physical device running the latest iOS."""
    rec_dir = M / "store/recordings"
    found = sorted(rec_dir.glob(f"{ctx['repo']}.*")) if rec_dir.is_dir() else []
    return (OK, found[-1].name) if found else \
        (HUMAN, "record on a physical iPhone on the latest iOS, save as store/recordings/<App>.mov")


REQUIREMENTS = [
    {"id": "screenshots-2.3.3", "guideline": "2.3.3",
     "name": "Screenshots on App Store Connect show the app in use",
     "apple": "App screenshots on the App Store must show the actual app in use, and not merely "
              "the title art, login page, or splash screen.",
     "raised": ["AGrammarly", "GroceryMatch", "HerJourney", "Kinnav", "MyCard", "Uscis-Case"],
     "check": screenshots_show_app},
    {"id": "launch-2.1a", "guideline": "2.1(a)",
     "name": "Launches on iOS 27, iPhone and iPad",
     "apple": "We were unable to review the app because it crashed on launch. ... iPhone 17 Pro Max, "
              "iOS 27.0. ... apps that may be downloaded onto iPad devices should function as "
              "expected for iPad users.",
     "raised": ["DriftDate", "Photriya", "PilotEnRoute", "Verba", "daily-pulse", "iMaps",
                "iMeasure", "portfolio-board", "yourtube"],
     "check": launches_ios27_iphone_ipad},
    {"id": "in-app-sign-in-4", "guideline": "4",
     "name": "Sign-in and registration happen inside the app",
     "apple": "The user is taken to the default web browser to sign in or register for an "
              "account, which provides a poor user experience.",
     "raised": ["CodeDeal"], "check": sign_in_inside_app},
    {"id": "iap-2.1b", "guideline": "2.1(b) / 3.1.1",
     "name": "In-app purchases are configured and submitted with the app",
     "apple": "We are unable to complete the review of the app because one or more of the "
              "In-App Purchase products have not been submitted for review.",
     "raised": ["NexusTransferPay"], "check": iap_submitted_with_app},
    {"id": "att-2.1", "guideline": "2.1 / 5.1.2",
     "name": "Tracking prompt appears when tracking is declared",
     "apple": "The app uses the AppTrackingTransparency framework, but we are unable to locate "
              "the App Tracking Transparency permission request.",
     "raised": ["CalcMaster"], "check": att_prompt_when_tracking},
    {"id": "vpn-notes", "guideline": "2.1 (automated)",
     "name": "VPN questions answered when the binary links NetworkExtension",
     "apple": "An automated analysis indicates the app contains VPN functionality. ... If the app "
              "does not have VPN features, reply to this message to confirm and include this "
              "clarification in the App Review Information section.",
     "raised": ["WiFiTrail"], "check": vpn_statement},
    {"id": "account-deletion-5.1.1v", "guideline": "5.1.1(v)",
     "name": "In-app account deletion when the app creates accounts",
     "apple": "Account registration, login, and account deletion flows. Account deletion is "
              "required in apps that support account creation.",
     "raised": ["(asked of all 22 'Information Needed' apps)"], "check": account_deletion_in_app},
    {"id": "ugc-1.2", "guideline": "1.2",
     "name": "User-generated content has reporting and blocking",
     "apple": "Any user-generated content, including the required content reporting and "
              "blocking mechanisms.",
     "raised": ["(asked of all 22 'Information Needed' apps)"], "check": ugc_report_and_block},
    {"id": "recording-2.1", "guideline": "2.1",
     "name": "Screen recording on a physical device is on file",
     "apple": "A screen recording captured on a physical device, running the latest operating "
              "system, demonstrating the app's functionality. The recording must begin with "
              "launching the app and show the typical user flow.",
     "raised": ["(asked of 24 apps)"], "check": recording_on_file},
]


_SHARED: dict = {}


def _shared():
    if not _SHARED:
        sim = {}
        for f in sorted((DIST / "sim-install").glob("20*.json")) if (DIST / "sim-install").is_dir() else []:
            for r in (_load(f, {}).get("results") or []):
                if r.get("repo") and r.get("platform"):
                    sim.setdefault(r["repo"], {})[r["platform"]] = r.get("status")
        _SHARED.update(shots=_load(M / "docs/screenshot-audit.json", {}),
                       iap=_load(DIST / "iap-readiness.json", {}), sim=sim,
                       rpc_delete_user=_rpc_exists("delete_user"))
    return _SHARED


def evaluate(app: dict) -> list[tuple[str, str, str]]:
    """[(gate row name, state, detail)] for one apps.json entry."""
    repo = app["repo"]
    d = ROOT / repo / (app.get("dir") or ".")
    ctx = {"repo": repo, "d": d, "dart": _dart(d),
           "rec": _load(M / f"store/apps/{repo}.json", {}), **_shared()}
    rows = []
    for r in REQUIREMENTS:
        try:
            state, detail = r["check"](ctx)
        except Exception as e:  # a broken check must show, not pass
            state, detail = NO, f"check errored: {type(e).__name__}: {e}"
        rows.append((f"Apple {r['guideline']}: {r['name']}", state, detail))
    return rows


def main() -> int:
    apps = json.loads((M / "apps.json").read_text())["apps"]
    only = sys.argv[1:]
    if only:
        apps = [a for a in apps if a["repo"] in only]
    result = {a["repo"]: [{"check": n, "state": s, "detail": d} for n, s, d in evaluate(a)]
              for a in apps}
    if only:
        for repo, rows in result.items():
            print(repo)
            for r in rows:
                print(f"  {r['state']:5} {r['check']}\n        {r['detail']}")
        return 0
    (M / "docs/apple-requirements.json").write_text(json.dumps(result, indent=1) + "\n")

    lines = ["# What App Review has required of our apps — generated by `scripts/apple_requirements.py`",
             "", "Every row is a requirement Apple raised in a rejection, in Apple's words, with the "
             "check that now enforces it in the submission gate (`store_checklist.py`, run by "
             "`store_watch.py` and `ship.yml`). Regenerate; do not edit.", "",
             "| Guideline | Requirement | Raised against | PASS | FAIL | HUMAN | n/a |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(REQUIREMENTS):
        states = [rows[i]["state"] for rows in result.values()]
        lines.append(f"| {r['guideline']} | {r['name']} | {', '.join(r['raised'])} | "
                     f"{states.count(OK)} | {states.count(NO)} | {states.count(HUMAN)} | {states.count(NA)} |")
    lines += ["", "## Apple's words", ""]
    for r in REQUIREMENTS:
        lines.append(f"- **{r['guideline']} — {r['name']}.** \"{r['apple']}\" "
                     f"Check: `{r['check'].__name__}` — {r['check'].__doc__.strip()}")
    lines += ["", "## Failing now", ""]
    for repo, rows in sorted(result.items()):
        for row in rows:
            if row["state"] == NO:
                lines.append(f"- **{repo}** — {row['check']}: {row['detail']}")
    lines += ["", "Not checks, by design: 4.3 (a written answer; gate row \"4.3 differentiation "
              "statement\"), 5.6 (account-level; `store_watch.py` ACCOUNT_FREEZE, MA-043).", ""]
    (M / "docs/APPLE_REQUIREMENTS.md").write_text("\n".join(lines))
    tot = [r["state"] for rows in result.values() for r in rows]
    print(f"  {len(result)} apps x {len(REQUIREMENTS)} requirements: {tot.count(OK)} pass, "
          f"{tot.count(NO)} fail, {tot.count(HUMAN)} need a person, {tot.count(NA)} n/a")
    print("  -> docs/apple-requirements.json, docs/APPLE_REQUIREMENTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
