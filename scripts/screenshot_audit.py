#!/usr/bin/env python3
"""Read every store screenshot the way App Review reads it, and fail the ones Apple rejects.

    bundle exec ruby scripts/testflight/asc_screenshots.rb   # fetch what Apple holds
    python3 scripts/screenshot_audit.py                      # -> docs/screenshot-audit.json
    python3 scripts/screenshot_audit.py --local MyCard       # the PNGs fastlane would upload

Guideline 2.3.3: "App screenshots on the App Store must show the actual app in
use, and not merely the title art, login page, or splash screen." Six apps
were rejected for it while the gate said PASS, because the gate judged the
PNGs on this laptop by pixel variance. On App Store Connect, measured
2026-10-08, MyCard's iPhone screenshots were the system passcode prompt with
the keyboard up, and HerJourney's only iPhone screenshot was its
"Welcome / Get Started" onboarding page. Neither is blank, so variance passed
them.

So this reads the text on each screenshot (RapidOCR in <DIST>/ocr-venv;
macOS Vision fails on this machine with "e5rt_e5_compiler_compile call
failed") and names what the screen is:

  blank        a solid frame
  system       an iOS system sheet — passcode, permission, tracking alert
  keyboard     the software keyboard covers the screen
  login        a sign-in / sign-up form and little else
  onboarding   a welcome, splash or "Get Started" page and little else
  error        an error or offline message
  empty        an empty state ("Nothing saved yet") — warned, not failed
  app          anything else: the app in use

An app fails when a set's first screenshot, or the majority of a set, is not
the app in use, or when it has no iPhone screenshots at all.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402

OUT = M / "docs/screenshot-audit.json"
ASC = DIST / "asc-screenshots"
VENV_PY = DIST / "ocr-venv/bin/python"

SYSTEM = re.compile(r"(?i)passcode|would like to|don.t allow|allow once|allow while using|"
                    r"track your activity|face id|touch id|enter password for")
LOGIN = re.compile(r"(?i)\b(sign ?in|log ?in|sign ?up|create (an )?account|password|"
                   r"forgot|continue with (apple|google|email)|e-?mail address)\b")
ONBOARD = re.compile(r"(?i)\b(welcome|get ?started|let.s go|skip|onboarding|next)\b")
ERROR = re.compile(r"(?i)something went wrong|failed to load|no internet|you.re offline|"
                   r"connection (failed|error)|exception|error loading|try again later")
EMPTY = re.compile(r"(?i)nothing (here|saved|yet)|no (items|data|results|entries)( yet)?\b|"
                   r"you have(n.t| no)")
STATUS = re.compile(r"^\d{1,2}:\d{2}$")
# Found on App Store Connect on 2026-10-09 by reading the uploaded pixels:
# "Use test account" and "Demo mode (dev) — skip to app" buttons that release
# builds compile out (Kinnav, MyHealth, PilotEnRoute) — the store page shows a
# feature the reviewer cannot find; "SAMPLE DATA — these are not live quotes"
# banners (RideZap, AeroSwift); AGrammarly's screenshots were the iOS home
# screen and the Messages app; Uscis-Case's showed Photriya's permission sheet.
DEV_UI = re.compile(r"(?i)test account|demo mode|\(dev\)|skip to app|debug menu|debug build")
SAMPLE = re.compile(r"(?i)sample data|not real (flights|data|quotes)|not live quotes|"
                    r"local placeholder|lorem ipsum")
SPRINGBOARD = {"contacts", "files", "fitness", "watch", "health", "shortcuts", "passwords",
               "preview", "settings", "photos", "camera", "maps", "calendar", "clock",
               "weather", "notes", "reminders", "app store", "safari", "wallet", "freeform"}
APP_NAMES: dict[str, str] = {}   # lower-case display name -> repo, filled in main()


def ocr(paths: list[pathlib.Path]) -> dict[str, list[str]]:
    """{path: [text lines]} via RapidOCR in its own venv (onnxruntime has no 3.14 wheel)."""
    if not VENV_PY.exists():
        sys.exit(f"OCR venv missing: python3.12 -m venv {DIST}/ocr-venv && "
                 f"{DIST}/ocr-venv/bin/pip install rapidocr_onnxruntime")
    prog = ("import json,sys\nfrom rapidocr_onnxruntime import RapidOCR\no=RapidOCR()\n"
            "out={}\nfor p in sys.argv[1:]:\n r,_=o(p)\n out[p]=[x[1] for x in (r or [])]\n"
            "print(json.dumps(out))")
    res = {}
    for i in range(0, len(paths), 40):
        chunk = [str(p) for p in paths[i:i + 40]]
        r = subprocess.run([str(VENV_PY), "-c", prog, *chunk], capture_output=True, text=True)
        try:
            res.update(json.loads(r.stdout.strip().splitlines()[-1]))
        except Exception:
            res.update({p: None for p in chunk})
    return res


def stddev(path: pathlib.Path) -> float | None:
    out = subprocess.run(["magick", str(path), "-colorspace", "Gray", "-format",
                          "%[fx:standard_deviation]", "info:"],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return None


def classify(lines: list[str] | None, sd: float | None, repo: str = "") -> tuple[str, str]:
    if sd is not None and sd < 0.005:
        return "blank", "solid frame"
    if lines is None:
        return "unread", "OCR failed"
    body = [l for l in lines if not STATUS.match(l.strip())]
    text = " ".join(body)
    words = re.findall(r"[A-Za-z]{2,}", text)
    singles = sum(1 for l in body if len(l.strip()) <= 2)
    # iOS's back-to-previous-app link in the status bar ("◀ Kinnav").
    # OCR drops the arrow and reads it as the bare name on its own line, so
    # any other app's exact name among the first lines is that link.
    back = next((l for l in lines[:4] if re.match(r"^\s*[◀<]\s*\w", l)
                 or (APP_NAMES.get(l.strip().lower()) not in (None, repo))), None)
    if back:
        return "other_app", f"status bar links back to another app: {back.strip()}"
    icons = {l.strip().lower() for l in body} & SPRINGBOARD
    if len(icons) >= 4:
        return "not_this_app", "iOS home screen (" + ", ".join(sorted(icons)[:4]) + ")"
    own = {n for n, r in APP_NAMES.items() if r == repo}
    others = [n for n, r in APP_NAMES.items() if r != repo and len(n) > 4
              and re.search(rf"(?i)[\"“”']{re.escape(n)}[\"“”']|^{re.escape(n)}$", text)
              and not any(o in text.lower() for o in own)]
    if others:
        return "other_app", f"shows another app: {others[0]}"
    if DEV_UI.search(text):
        return "dev_ui", DEV_UI.search(text).group(0)
    if SAMPLE.search(text):
        return "sample", SAMPLE.search(text).group(0)
    if SYSTEM.search(text):
        return "system", SYSTEM.search(text).group(0)
    # A keyboard shows ~26 single letters; a weekday chart shows 7 (M T W T F
    # S S), so the threshold sits above that, or the keyboard's own keys.
    if singles >= 12 or ".?123" in text or (singles >= 8 and re.search(r"(?m)^\s*123\s*$", "\n".join(body))):
        return "keyboard", "software keyboard on screen"
    if ERROR.search(text):
        return "error", ERROR.search(text).group(0)
    # A sign-in form: a password field plus a sign-in verb. Kinnav's form has
    # enough legal text and provider buttons to pass a short word limit.
    if re.search(r"(?i)\bpassword\b", text) and LOGIN.search(text) and len(words) < 90:
        return "login", "sign-in form"
    if LOGIN.search(text) and len(words) < 40:
        return "login", LOGIN.search(text).group(0)
    if len(words) <= 3:
        return "onboarding", f"only {len(words)} word(s) — splash or title art"
    if ONBOARD.search(text) and len(words) < 30:
        return "onboarding", ONBOARD.search(text).group(0)
    if EMPTY.search(text) and len(words) < 30:
        return "empty", EMPTY.search(text).group(0)
    return "app", f"{len(words)} words"


BAD = {"blank", "system", "keyboard", "login", "onboarding", "error", "unread",
       "not_this_app", "other_app", "dev_ui", "sample"}
# Never acceptable anywhere in a set, not just as the first or the majority.
NEVER = {"not_this_app", "other_app", "dev_ui", "sample"}


def judge(sets: dict[str, list[dict]]) -> list[str]:
    problems = []
    if not any(t.startswith("APP_IPHONE") or "iphone" in t.lower() for t in sets):
        problems.append("no iPhone screenshots")
    for t, shots in sorted(sets.items()):
        if not shots:
            continue
        bad = [s for s in shots if s["kind"] in BAD]
        if shots[0]["kind"] in BAD:
            problems.append(f"{t}: first screenshot is {shots[0]['kind']} ({shots[0]['why']})")
        if len(bad) * 2 > len(shots):
            problems.append(f"{t}: {len(bad)} of {len(shots)} are not the app in use")
        for s in shots:
            if s["kind"] in NEVER:
                problems.append(f"{t}: {s['file']} is {s['kind']} ({s['why']})")
        hashes = [s["sha"] for s in shots]
        if len(set(hashes)) < len(hashes):
            problems.append(f"{t}: {len(hashes) - len(set(hashes))} duplicate screenshot(s)")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true",
                    help="judge <app>/fastlane/screenshots instead of what Apple holds")
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    apps = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        apps = [a for a in apps if a["repo"] in args.apps]
    index = json.loads((ASC / "index.json").read_text()) if (ASC / "index.json").exists() else {}
    for a in json.loads((M / "apps.json").read_text())["apps"]:
        rec = json.loads((M / f"store/apps/{a['repo']}.json").read_text()) \
            if (M / f"store/apps/{a['repo']}.json").exists() else {}
        name = ((rec.get("copy") or {}).get("en") or {}).get("name") or a["repo"]
        for n in {a["repo"], name.split(":")[0].split(" - ")[0].strip()}:
            APP_NAMES[n.lower()] = a["repo"]

    plan: dict[str, dict[str, list[pathlib.Path]]] = {}
    for a in apps:
        repo = a["repo"]
        if args.local:
            d = ROOT / repo / (a.get("dir") or ".") / "fastlane/screenshots"
            files = sorted(d.rglob("*.png")) if d.is_dir() else []
            sets: dict[str, list[pathlib.Path]] = {}
            for f in files:
                sets.setdefault(f.stem.rsplit("-", 1)[0], []).append(f)
        else:
            rec = index.get(repo)
            if not rec:
                continue
            sets = {t: [ASC / repo / f for f in fs] for t, fs in rec["sets"].items()}
        plan[repo] = sets

    every = [p for s in plan.values() for fs in s.values() for p in fs]
    text = ocr(every)
    report = json.loads(OUT.read_text()) if (OUT.exists() and not args.local) else {}
    if args.local:
        report = {}
    for repo, sets in plan.items():
        judged = {}
        for t, fs in sets.items():
            judged[t] = []
            for f in fs:
                kind, why = classify(text.get(str(f)), stddev(f), repo)
                judged[t].append({"file": f.name, "kind": kind, "why": why,
                                  "sha": hashlib.sha1(f.read_bytes()).hexdigest()[:12],
                                  "text": (text.get(str(f)) or [])[:12]})
        problems = judge(judged)
        report[repo] = {"source": "local" if args.local else "app_store_connect",
                        "version": (index.get(repo) or {}).get("version"),
                        "verdict": "FAIL" if problems else "PASS",
                        "problems": problems, "sets": judged}
        kinds = [s["kind"] for ss in judged.values() for s in ss]
        print(f"  {repo:18} {report[repo]['verdict']:4} "
              f"{len(kinds):2} shots  " + " ".join(f"{k}={kinds.count(k)}" for k in sorted(set(kinds)))
              + (f"\n{'':24}" + f"\n{'':24}".join(problems) if problems else ""))
    if not args.local:
        OUT.write_text(json.dumps(report, indent=1) + "\n")
        bad = sorted(r for r, v in report.items() if v["verdict"] == "FAIL")
        print(f"\n  {len(report)} apps judged, {len(bad)} fail 2.3.3: {', '.join(bad)}")
        print(f"  -> {OUT.relative_to(M)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
