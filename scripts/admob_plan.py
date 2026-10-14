#!/usr/bin/env python3
"""The founder's AdMob ad-units plan, kept in the repo and checked against what ships.

    python3 scripts/admob_plan.py                       # re-measure store/admob/ad-units-plan.csv
    python3 scripts/admob_plan.py --import <plan.csv>   # take a new export of the founder's sheet
    python3 scripts/admob_plan.py --check               # exit 1 if a unit's data is missing or wrong

The plan is 43 apps x 2 platforms x 6 formats (Banner, Interstitial, Rewarded,
Rewarded Interstitial, Native Advanced, App Open) = 516 ad units. The founder's
columns (# … Notes) are kept as given, except a package/bundle id that differs
from the app's real one for that platform (apps.json), which is corrected and
noted in Checks. The measured columns are rewritten on every run:

    Repo                        the repo the row belongs to (matched by ad unit id)
    Define                      the --dart-define that carries the unit (agl_paths.admob_defines)
    In build data               the unit and app id equal docs/admob-ids.json, which the builds read
    App ID in app               the AdMob app id in Info.plist / AndroidManifest.xml equals this row's.
                                A wrong iOS id terminates the app at launch.
    Read by app                 the app's code reads that define (agl_ads reads banner + interstitial)
    Ad code in app              code for that format exists in lib/ (it may be unreachable)
    Shown in app                from the monetization review (ai-office/projects/admob-rollout/
                                placements/<repo>.json, file:line evidence): the app displays it
    Planned                     that review's plan under the founder's "fit per app" decision
                                (2026-10-14): keep / remove / add / no
    Checks                      anything wrong with the row

Also writes docs/ADMOB_PLAN.md, the per-app summary. Reads local files only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST, ROOT  # noqa: E402

PLAN = MANIFEST / "store" / "admob" / "ad-units-plan.csv"
REPORT = MANIFEST / "docs" / "ADMOB_PLAN.md"
FOUNDER = ["#", "App Name", "Package / Bundle ID", "Platform", "AdMob App ID", "Ad Format",
           "Ad Unit Name", "AdMob Ad Unit ID", "Status", "Notes"]
MEASURED = ["Repo", "Define", "In build data", "App ID in app", "Read by app", "Ad code in app",
            "Shown in app", "Planned", "Checks"]
FORMATS = {  # plan format -> (admob-ids.json / define suffix, code that loads it)
    "Banner": ("banner", r"AglAdBanner\b|\bBannerAd\("),
    "Interstitial": ("interstitial", r"AglAds\.onTransition|(?<!Rewarded)InterstitialAd\.load"),
    "Rewarded": ("rewarded", r"\bRewardedAd\.load"),
    "Rewarded Interstitial": ("rewarded_interstitial", r"RewardedInterstitialAd\.load"),
    "Native Advanced": ("native", r"\bNativeAd\("),
    "App Open": ("app_open", r"AppOpenAd\.load"),
}
UNIT = re.compile(r"ca-app-pub-\d{16}/\d{10}")
APP = re.compile(r"ca-app-pub-\d{16}~\d{10}")


def app_dir(a: dict) -> pathlib.Path:
    d = a.get("dir") or "."
    return ROOT / a["repo"] if d == "." else ROOT / a["repo"] / d


def shipped_app_ids(d: pathlib.Path) -> dict:
    out = {}
    plist = d / "ios/Runner/Info.plist"
    if plist.exists():
        m = re.search(r"<key>GADApplicationIdentifier</key>(?:\s|<!--.*?-->)*<string>([^<]+)</string>",
                      plist.read_text(), re.S)
        out["ios"] = m.group(1).strip() if m else ""
    man = d / "android/app/src/main/AndroidManifest.xml"
    if man.exists():
        t = man.read_text()
        m = re.search(r'<meta-data[^>]*com\.google\.android\.gms\.ads\.APPLICATION_ID[^>]*>', t, re.S)
        v = re.search(r'android:value="([^"]+)"', m.group(0)) if m else None
        out["android"] = v.group(1).strip() if v else ""
    return out


def code_of(d: pathlib.Path) -> dict[str, str]:
    lib = d / "lib"
    # Comments stripped: a doc comment naming loadRewarded is not a call.
    strip = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
    return {str(p): strip.sub("", p.read_text(errors="ignore")) for p in lib.rglob("*.dart")} if lib.exists() else {}


PLACEMENTS = MANIFEST / "ai-office" / "projects" / "admob-rollout" / "placements"


def reviewed(repo: str) -> dict:
    """The monetization review of one app (placements/<repo>.json): what it
    shows today, read from the code with file:line evidence, and what is
    planned. Whether an ad reaches the screen is not decidable by pattern
    matching — loaders nobody calls and widgets no screen places look the same
    as live ones — so the "Shown in app" column comes from this review."""
    f = PLACEMENTS / f"{repo}.json"
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--import", dest="src", type=pathlib.Path, help="founder's sheet exported as CSV")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    src = args.src or PLAN
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    missing_cols = [c for c in FOUNDER if c not in (rows[0] if rows else {})]
    if missing_cols:
        print(f"{src}: missing columns {missing_cols}")
        return 1

    apps = {a["repo"]: a for a in json.loads((MANIFEST / "apps.json").read_text())["apps"]}
    ids = json.loads((MANIFEST / "docs/admob-ids.json").read_text())
    unit_owner = {v: (repo, k) for repo, d in ids.items() for k, v in d.items()}
    facts = {}
    for repo, a in apps.items():
        d = app_dir(a)
        files = code_of(d)
        code = "\n".join(files.values())
        facts[repo] = {
            "app_ids": shipped_app_ids(d),
            "review": reviewed(repo),
            "code": code,
            "agl_ads": "AglAdIds.fromEnvironment" in code,
            "ads_on": bool(re.search(r"AglAds\.configure|MobileAds\.instance\.initialize|AglAds\.initialize", code)),
        }

    out, problems = [], 0
    seen_units = collections.Counter(r["AdMob Ad Unit ID"].strip() for r in rows)
    for r in rows:
        row = {c: (r.get(c) or "").strip() for c in FOUNDER}
        checks = []
        plat = row["Platform"].lower()
        fmt = FORMATS.get(row["Ad Format"])
        if plat not in ("android", "ios"):
            checks.append(f"unknown platform '{row['Platform']}'")
        if not fmt:
            checks.append(f"unknown format '{row['Ad Format']}'")
        for c in FOUNDER[:-1]:
            if not row[c]:
                checks.append(f"{c} empty")
        if row["AdMob Ad Unit ID"] and not UNIT.fullmatch(row["AdMob Ad Unit ID"]):
            checks.append("ad unit id malformed")
        if row["AdMob App ID"] and not APP.fullmatch(row["AdMob App ID"]):
            checks.append("app id malformed")
        if seen_units[row["AdMob Ad Unit ID"]] > 1:
            checks.append("ad unit id used twice")
        owner = unit_owner.get(row["AdMob Ad Unit ID"])
        repo = owner[0] if owner else next((k for k, a in apps.items() if row["App Name"] in (k, a.get("name"))), "")
        key = f"{plat}_{fmt[0]}" if fmt else ""
        define = f"ADMOB_{fmt[0].upper()}_{plat.upper()}" if fmt else ""
        in_data = bool(repo) and ids.get(repo, {}).get(key) == row["AdMob Ad Unit ID"] \
            and ids.get(repo, {}).get(f"{plat}_app_id") == row["AdMob App ID"]
        if not in_data:
            checks.append("differs from docs/admob-ids.json")
        a = apps.get(repo, {})
        real_pkg = (a.get("application_id") or a.get("bundle_id")) if plat == "android" else a.get("bundle_id")
        if real_pkg and row["Package / Bundle ID"] != real_pkg:
            checks.append(f"package corrected (was {row['Package / Bundle ID']})")
            row["Package / Bundle ID"] = real_pkg
        f = facts.get(repo, {})
        shipped = f.get("app_ids", {}).get(plat)
        if shipped is None:
            app_id_state = "no project"
        elif not shipped:
            app_id_state = "none (app has no AdMob)"
        elif shipped == row["AdMob App ID"]:
            app_id_state = "yes"
        else:
            app_id_state = f"NO: app ships {shipped}"
            checks.append("app id in app differs")
        code = f.get("code", "")
        read = bool(fmt) and (define in code or (f.get("agl_ads") and fmt[0] in ("banner", "interstitial")))
        present = bool(fmt) and bool(re.search(fmt[1], code))
        rv = f.get("review", {})
        key_ = fmt[0] if fmt else ""
        if not rv:
            shown, planned = "not reviewed", ""
        else:
            shown = "yes" if key_ in ("banner", "interstitial") and (rv.get(key_) or {}).get("present") else "no"
            planned = {"banner": "keep" if (rv.get("banner") or {}).get("present") else "no",
                       "interstitial": (rv.get("interstitial") or {}).get("recommend", "") if (rv.get("interstitial") or {}).get("present") else "no",
                       "rewarded": "add" if (rv.get("rewarded") or {}).get("use") else "no",
                       "native": "add" if (rv.get("native") or {}).get("use") else "no"}.get(key_, "no")
        hard = [c for c in checks if not c.startswith("package corrected")]
        problems += bool(hard)
        out.append({**row, "Repo": repo, "Define": define, "In build data": "yes" if in_data else "NO",
                    "App ID in app": app_id_state, "Read by app": "yes" if read else "no",
                    "Ad code in app": "yes" if present else "no", "Shown in app": shown,
                    "Planned": planned, "Checks": "; ".join(checks)})

    PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAN, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FOUNDER + MEASURED)
        w.writeheader()
        w.writerows(out)

    by_app = collections.defaultdict(list)
    for r in out:
        by_app[r["Repo"] or r["App Name"]].append(r)
    fmt_names = list(FORMATS)
    lines = [
        "# AdMob ad-units plan — measured",
        "",
        "Generated by `python3 scripts/admob_plan.py` from `store/admob/ad-units-plan.csv` "
        "(the founder's plan plus measured columns). Do not hand-edit; re-run the script.",
        "",
        f"- Units in the plan: **{len(out)}** across **{len(by_app)}** apps "
        f"({sum(len(v) == 12 for v in by_app.values())} apps have all 12: 6 formats x 2 platforms)",
        f"- Units equal to `docs/admob-ids.json` (what builds pass): "
        f"**{sum(r['In build data'] == 'yes' for r in out)}/{len(out)}**",
        f"- Rows with a problem: **{problems}**",
        "",
        "Formats, from the monetization review (`ai-office/projects/admob-rollout/placements/<repo>.json`, "
        "file:line evidence) under the founder's \"fit per app\" decision (2026-10-14): ✅ shown and kept · "
        "➖ shown, review recommends removing · ➕ not shown, review recommends adding · ▫️ unit exists, not used. "
        "App open and rewarded interstitial are \"no\" for every app by that decision.",
        "",
        "| App | Units | App id iOS / Android | " + " | ".join(fmt_names) + " | Checks |",
        "| --- | --- | --- | " + " | ".join("---" for _ in fmt_names) + " | --- |",
    ]
    for app in sorted(by_app, key=str.lower):
        rs = by_app[app]
        ida = {r["Platform"].lower(): r["App ID in app"] for r in rs}
        marks = []
        for fn in fmt_names:
            r0 = next((r for r in rs if r["Ad Format"] == fn), {})
            shown, plan = r0.get("Shown in app") == "yes", r0.get("Planned", "")
            marks.append("❔" if r0.get("Shown in app") == "not reviewed" else
                         "➖" if shown and plan == "remove" else "✅" if shown else "➕" if plan == "add" else "▫️")
        chk = sorted({c for r in rs for c in r["Checks"].split("; ") if c})
        lines.append(f"| {app} | {len(rs)} | {ida.get('ios', '-')} / {ida.get('android', '-')} | "
                     + " | ".join(marks) + f" | {'; '.join(chk)} |")
    def n(fmt, col, val):
        return sum(any(r["Ad Format"] == fmt and r[col] == val for r in rs) for rs in by_app.values())
    lines += ["", "| Format | Apps showing it today | Review: remove | Review: add |", "| --- | --- | --- | --- |"]
    for fn in fmt_names:
        lines.append(f"| {fn} | {n(fn, 'Shown in app', 'yes')} | {n(fn, 'Planned', 'remove')} | {n(fn, 'Planned', 'add')} |")
    lines.append("")
    REPORT.write_text("\n".join(lines))

    print(f"{PLAN.relative_to(MANIFEST)}: {len(out)} units, {len(by_app)} apps, {problems} with a problem")
    print(f"{REPORT.relative_to(MANIFEST)} written")
    for r in out:
        if r["Checks"]:
            print(f"  {r['Repo'] or r['App Name']} {r['Platform']} {r['Ad Format']}: {r['Checks']}")
    return 1 if (args.check and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
