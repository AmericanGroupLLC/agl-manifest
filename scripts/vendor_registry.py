#!/usr/bin/env python3
"""The vendor registry: every affiliate programme, data API and partner per app, kept and added to.

    python3 scripts/vendor_registry.py --from-code                 # sync what the app code uses
    python3 scripts/vendor_registry.py --import-research run.json  # merge a vendor-scout result
    python3 scripts/vendor_registry.py --set GadgetNest "Best Buy" signed-up
    .venv/bin/python3 scripts/vendor_registry.py --workbook        # regenerate the measured xlsx
    python3 scripts/vendor_registry.py --summary
    python3 scripts/vendor_registry.py --export-apps      # store/vendors/apps/<App>.csv, one per app
    python3 scripts/vendor_registry.py --import-apps      # pull the founder's edits back in

The per-app CSVs are the working trackers. Measured columns are regenerated
on every export; the founder's columns (signup_status, api_access,
token_vault_ref, owner, next_action, notes) are preserved and flow back with
--import-apps. A cell that looks like a real key or token is refused — the
vault reference is the *name* of a secret (e.g. "GitHub secret
AMAZON_TAG_BODYQUEST"), never its value.

`store/vendors/registry.json` is **append-only by design**: the founder asked
(2026-10-12) that vendors keep being added, so a merge never drops an entry.
Re-imports update facts in place and keep `added`; a vendor that turns out to be
wrong is marked `status: rejected` with the reason, not deleted.

Status ladder per app/vendor pair:
    proposed → in-code → signed-up → live          (or rejected)
`in-code` comes only from the code audit (docs/api-vendor-usage.json, regenerated
by scripts/api_vendor_audit.py); `signed-up` and `live` only from --set, because
nothing in this repo can see a vendor account. No credentials are ever stored
here — the workbook's Credentials Register holds vault references only.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M  # noqa: E402

REG = M / "store/vendors/registry.json"
USAGE = M / "docs/api-vendor-usage.json"
KEYS = M / "docs/api-vendor-keys.json"
DIRECTORY = M / "docs/api-vendor-directory.csv"
WB_SRC = M / "AGL_43_App_Vendor_API_Affiliate_Master.xlsx"
WB_OUT = M / "AGL_43_App_Vendor_API_Affiliate_Master.measured.xlsx"
STATUSES = ("proposed", "in-code", "signed-up", "live", "rejected")
RANK = {s: i for i, s in enumerate(STATUSES[:-1])}

# Code-audit hits that are words, not vendors (checked by hand 2026-10-12):
# Portuguese "agora", "striped", "...Entry" classes, the Gemini zodiac sign.
FALSE_HITS = {("Agora", a) for a in ("AGStudio", "daily-pulse", "MyFinance", "NexusTransferPay")} | \
    {("Sentry", a) for a in ("BuddyPlay", "PilotEnRoute", "portfolio-board", "Uscis-Case")} | \
    {("Stripe", a) for a in ("FashionFactory", "RoomCraft", "Uscis-Case")} | \
    {("Google AI (Gemini)", "MyHealth"), ("Veryfi", "MyHealth"), ("Amazon Associates", "ApexMarketWatch")}
LINK_ONLY = {("FlightAware AeroAPI", "PilotEnRoute"), ("ForeFlight", "PilotEnRoute"), ("Garmin", "PilotEnRoute"),
             ("Garmin", "MyHealth"), ("OpenSky Network", "PilotEnRoute"), ("OurAirports", "AeroSwift")}


def today() -> str:
    return datetime.date.today().isoformat()


def load() -> dict:
    if REG.exists():
        return json.loads(REG.read_text())
    return {"_about": "Append-only vendor registry; see scripts/vendor_registry.py", "vendors": {}, "pairs": {}}


def save(reg: dict) -> None:
    REG.parent.mkdir(parents=True, exist_ok=True)
    reg["pairs"] = dict(sorted(reg["pairs"].items(), key=lambda kv: kv[0].lower()))
    reg["vendors"] = dict(sorted(reg["vendors"].items(), key=lambda kv: kv[0].lower()))
    REG.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")


def upsert_vendor(reg: dict, name: str, facts: dict) -> None:
    v = reg["vendors"].setdefault(name, {"added": today()})
    for k, val in facts.items():
        if val not in (None, "", []):
            if k == "sources":
                v["sources"] = sorted(set(v.get("sources", [])) | set(val))
            else:
                v[k] = val
    v["last_updated"] = today()


def upsert_pair(reg: dict, app: str, vendor: str, status: str, source: str, **facts) -> None:
    key = f"{app}|{vendor}"
    p = reg["pairs"].get(key)
    if p is None:
        p = reg["pairs"][key] = {"app": app, "vendor": vendor, "status": status, "added": today(),
                                 "history": []}
    # The founder's --set always wins; otherwise never move down the ladder
    # automatically, and a rejection sticks until someone sets it back.
    if source == "founder" or status == "rejected":
        p["status"] = status
    elif p["status"] != "rejected" and RANK.get(status, -1) > RANK.get(p["status"], -1):
        p["status"] = status
    for k, val in facts.items():
        if val not in (None, "", []):
            p[k] = val
    p["history"].append({"date": today(), "source": source, "status": status})
    p["history"] = p["history"][-20:]


def from_code(reg: dict) -> int:
    usage = json.loads(USAGE.read_text())["vendors"]
    keys = json.loads(KEYS.read_text())["apps"]
    n = 0
    for vendor, apps in usage.items():
        for app, site in apps.items():
            if (vendor, app) in FALSE_HITS:
                continue
            linked = (vendor, app) in LINK_ONLY
            cred = "; ".join(f"{k}={'default' if r['default'] else 'EMPTY in release'}"
                             for k, r in keys.get(app, {}).items()
                             if vendor.split()[0].upper().replace(".", "") in k)
            upsert_pair(reg, app, vendor, "proposed" if linked else "in-code", "code-audit",
                        code_evidence=site, credential_state=cred or None,
                        note="linked/named only, no API integration" if linked else None)
            n += 1
    # A pair the audit found before but not now: the feature left the code
    # (apps get reworked — BodyQuest lost its shop on 2026-10-12). Say so
    # instead of keeping a stale "in-code"; never delete the entry.
    seen = {f"{a}|{v}" for v, apps in usage.items() for a in apps if (v, a) not in FALSE_HITS}
    for key, p in reg["pairs"].items():
        if p["status"] == "in-code" and key not in seen:
            p["status"] = "proposed"
            p["note"] = f"removed from code on {today()} (was {p.get('code_evidence') or 'in code'})"
            p["code_evidence"] = ""
            p["history"].append({"date": today(), "source": "code-audit", "status": "removed-from-code"})
    if DIRECTORY.exists():
        for r in csv.DictReader(open(DIRECTORY)):
            upsert_vendor(reg, r["vendor"], {"money": r["money"], "signup_url": r["signup"],
                                              "directory_group": r["group"]})
    return n


def import_research(reg: dict, path: pathlib.Path, label: str) -> tuple[int, int]:
    data = json.loads(path.read_text())
    rows = data.get("vendors", data) if isinstance(data, dict) else data
    added = rejected = 0
    for v in rows:
        name, app = v["vendor"].strip(), v["app"].strip()
        check = v.get("check", "unchecked")
        upsert_vendor(reg, name, {
            "kind": v.get("kind"), "network": v.get("network"), "signup_url": v.get("signup_url"),
            "commission": v.get("commission"), "api_or_feed": v.get("api_or_feed"),
            "mobile_apps_allowed": v.get("mobile_apps_allowed"), "sources": v.get("sources") or [],
            "verified": bool(v.get("verified")) and check in ("confirmed", "corrected"),
        })
        status = "rejected" if check == "reject" else "proposed"
        rejected += status == "rejected"
        before = f"{app}|{name}" in reg["pairs"]
        upsert_pair(reg, app, name, status, label, fit=v.get("fit"), effort=v.get("effort"),
                    what_it_gives=v.get("what_it_gives_the_app"), domain=v.get("domain"),
                    check=check, correction=v.get("correction") or None,
                    check_evidence=(v.get("check_evidence") or "")[:500] or None)
        added += not before
    return added, rejected


def summary(reg: dict) -> None:
    by = {}
    for p in reg["pairs"].values():
        by.setdefault(p["status"], 0)
        by[p["status"]] += 1
    apps = {p["app"] for p in reg["pairs"].values() if p["status"] != "rejected"}
    print(f"  {len(reg['vendors'])} vendors, {len(reg['pairs'])} app/vendor pairs across {len(apps)} apps")
    print("  " + "  ".join(f"{s}={by.get(s, 0)}" for s in STATUSES))


def workbook(reg: dict) -> None:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.load_workbook(WB_SRC)
    for name in ("Vendor Registry", "Measured - code audit"):
        if name in wb.sheetnames:
            del wb[name]
    ws = wb.create_sheet("Vendor Registry", 0)
    cols = ["app", "vendor", "status", "kind", "network", "signup_url", "commission", "api_or_feed",
            "mobile_apps_allowed", "fit", "effort", "code_evidence", "credential_state", "check",
            "correction", "added", "verified", "sources"]
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True)
    fills = {"live": "C6EFCE", "signed-up": "DDEBF7", "in-code": "FFF2CC", "proposed": "FFFFFF",
             "rejected": "EDEDED"}
    for p in sorted(reg["pairs"].values(), key=lambda p: (p["app"].lower(), STATUSES.index(p["status"]),
                                                          p["vendor"].lower())):
        v = reg["vendors"].get(p["vendor"], {})
        row = [p["app"], p["vendor"], p["status"], v.get("kind"), v.get("network"), v.get("signup_url"),
               v.get("commission"), v.get("api_or_feed"), v.get("mobile_apps_allowed"), p.get("fit"),
               p.get("effort"), p.get("code_evidence"), p.get("credential_state"), p.get("check"),
               p.get("correction"), p.get("added"), v.get("verified"), "; ".join(v.get("sources", [])[:4])]
        ws.append(["" if x is None else x for x in row])
        for c in ws[ws.max_row]:
            c.fill = PatternFill("solid", fgColor=fills.get(p["status"], "FFFFFF"))
    apps = json.loads((M / "apps.json").read_text())["apps"]
    for a in apps:
        name = a["repo"][:31]
        if name in wb.sheetnames:
            del wb[name]
        sh = wb.create_sheet(name)
        sh.append(COLUMNS)
        for c in sh[1]:
            c.font = Font(bold=True)
        f = APPS_DIR / f"{a['repo']}.csv"
        src = list(csv.DictReader(open(f, newline=""))) if f.exists() else app_rows(reg, a["repo"], a)
        for r in src:
            sh.append([r.get(k, "") or "" for k in COLUMNS])
    if DIRECTORY.exists():
        md = wb.create_sheet("Measured - code audit", 1)
        for r in csv.reader(open(DIRECTORY)):
            md.append(r)
        for c in md[1]:
            c.font = Font(bold=True)
    wb.save(WB_OUT)
    print(f"  -> {WB_OUT}")



APPS_DIR = M / "store/vendors/apps"
MANUAL = ["signup_status", "api_access", "token_vault_ref", "owner", "next_action", "notes"]
AUTO = ["app", "vendor", "priority", "kind", "money", "what_it_does", "signup_url", "commission",
        "credential_names", "token_in_build", "code_evidence", "registry_status"]
COLUMNS = AUTO[:2] + ["priority"] + MANUAL[:3] + [c for c in AUTO if c not in ("app", "vendor", "priority")] + MANUAL[3:] + ["last_updated"]
SIGNUP_VALUES = ("Not started", "Applied", "Approved", "Rejected", "Done", "Not needed")
# Credential names each vendor's code reads (docs/api-vendor-keys.json has them per app).
KEYMAP = {
    "Amazon Associates": ["AGL_AFFILIATE_TAGS"], "Rakuten Advertising": ["AGL_AFFILIATE_TAGS"],
    "Awin": ["AGL_AFFILIATE_TAGS"], "Travelpayouts": ["AFFILIATE_MARKER"],
    "Impact": ["DOORDASH_AFFILIATE_ID", "UBEREATS_AFFILIATE_ID", "GRUBHUB_AFFILIATE_ID", "AFFILIATE_SUB_ID"],
    "DoorDash": ["DOORDASH_AFFILIATE_ID"], "Uber Eats": ["UBEREATS_AFFILIATE_ID"], "Grubhub": ["GRUBHUB_AFFILIATE_ID"],
    "Google Maps Platform": ["GOOGLE_MAPS_API_KEY", "MAPS_API_KEY"], "Firebase": ["FIREBASE_"],
    "OpenAI": ["OPENAI_API_KEY", "LLM_API_KEY", "AI_API_KEY"], "Anthropic": ["ANTHROPIC_API_KEY"],
    "USDA FoodData Central": ["USDA_API_KEY"], "NREL / NLR alt-fuel": ["NREL_API_KEY"],
    "Open Charge Map": ["OPENCHARGEMAP_KEY"], "NASA FIRMS": ["NASA_FIRMS_KEY"], "YouTube Data API": ["YOUTUBE_API_KEY"],
    "Yelp Fusion": ["YELP_API_KEY"], "RevenueCat": ["REVENUECAT"],
}
HARD_CODED = {  # partner ids typed into the code (measured 2026-10-12), not build-time keys
    ("BodyQuest", "Amazon Associates"): "hard-coded tag bodyquest-20 — registration not verified",
    ("CalcMaster", "Amazon Associates"): "hard-coded calcmaster-20/-21, marked REPLACE in code",
    ("VirtuBand", "Amazon Associates"): "hard-coded tag virtuband-20 — registration not verified",
    ("ChefCount", "Amazon Associates"): "tag 'americangroupllc' — not a valid store-ID format",
    ("TripNest", "Travelpayouts"): "marker 'americangroupllc' — Travelpayouts markers are numeric",
    ("EventSpark", "Travelpayouts"): "marker 'americangroupllc' — Travelpayouts markers are numeric",
    ("RideZap", "Expedia Group"): "placeholder affiliateId 'americangroupllc'",
    ("RideZap", "Booking.com"): "placeholder affiliateId 'americangroupllc'",
}
AFFILIATE_VENDORS = {"Amazon Associates", "Travelpayouts", "Impact", "DoorDash", "Uber Eats", "Grubhub",
                     "Rakuten Advertising", "Awin", "CJ Affiliate", "ShareASale", "FlexOffers", "Expedia Group",
                     "Booking.com", "Viator", "Rentalcars.com", "Busbud", "eBay Partner Network", "Best Buy",
                     "Walmart", "Instacart", "Ticketmaster", "Eventbrite", "Levanta", "Target"}
SECRET_LIKE = __import__("re").compile(r"(sk-[A-Za-z0-9]{10,}|AIza[0-9A-Za-z_-]{20,}|ghp_[A-Za-z0-9]{20,}|"
                                       r"eyJ[A-Za-z0-9_-]{20,}\.|-----BEGIN|(?<![A-Za-z0-9_])[A-Za-z0-9_\-]{32,}(?![A-Za-z0-9_]))")


def _token_state(app: str, vendor: str, keys: dict) -> tuple[str, str]:
    if (app, vendor) in HARD_CODED:
        return "", HARD_CODED[(app, vendor)]
    toks = KEYMAP.get(vendor) or [vendor.split()[0].upper().replace(".", "").replace("-", "")]
    hits = {k: r for k, r in keys.get(app, {}).items() if any(t in k for t in toks)}
    if not hits:
        return "", "no credential read by code"
    names = ", ".join(sorted(hits))
    state = "; ".join(f"{k}: {'default set' if r['default'] else 'EMPTY in release'}" for k, r in sorted(hits.items()))
    return names, state


def _platform_rows(app: str, a: dict) -> list[dict]:
    """App Store Connect, Google Play, AdMob — measured state, every app."""
    rows = []
    def load(rel, default):
        f = M / rel
        return json.loads(f.read_text()) if f.exists() else default
    asc = {x.get("repo"): x for x in (lambda d: d if isinstance(d, list) else d.get("apps", []))(load("docs/asc-build-state.json", []))}
    play = {x["repo"]: x for x in load("docs/play-production-blockers.json", {}).get("apps", [])}
    holds = load("docs/store-holds.json", {})
    admob = load("docs/admob-ids.json", {}).get(app) or {}
    x = asc.get(app, {})
    h = holds.get(app)
    rows.append({"vendor": "Apple App Store Connect", "kind": "platform", "money": "Distribution",
                 "signup_url": "appstoreconnect.apple.com", "signup_status": "Done",
                 "token_in_build": f"record {x.get('apple_id') or 'missing'}; build {x.get('version')} {x.get('processing_state')}; "
                                   f"review {x.get('review_state')}" + (f"; HOLD {h.get('guideline')}" if h else ""),
                 "priority": "P0", "what_it_does": "iOS distribution (TestFlight, App Store)"})
    p = play.get(app, {})
    rows.append({"vendor": "Google Play Console", "kind": "platform", "money": "Distribution",
                 "signup_url": "play.google.com/console", "signup_status": "Done",
                 "token_in_build": f"{p.get('state')}" + (f" — {p.get('blocker')}" if p.get("blocker") else ""),
                 "priority": "P0", "what_it_does": "Android distribution"})
    units = sum(1 for k, v in admob.items() if v and not k.endswith("app_id"))
    rows.append({"vendor": "Google AdMob", "kind": "monetization", "money": "Ad revenue",
                 "signup_url": "admob.google.com", "signup_status": "Done" if admob else "Not started",
                 "credential_names": "ADMOB_<FORMAT>_<PLATFORM>, android/ios app id",
                 "token_in_build": f"{units} ad unit(s) + app ids in docs/admob-ids.json, passed at build time" if admob
                                   else "no AdMob ids",
                 "priority": "P0", "what_it_does": "Banner/interstitial/rewarded/native/app-open ads"})
    keys = (json.loads(KEYS.read_text())["apps"] if KEYS.exists() else {}).get(app, {})
    g = {k: r for k, r in keys.items() if k.startswith("GOOGLE_") and "CLIENT_ID" in k}
    if g:
        rows.append({"vendor": "Google Sign-In (OAuth client)", "kind": "auth", "money": "Free",
                     "signup_url": "console.cloud.google.com/apis/credentials",
                     "credential_names": ", ".join(sorted(g)),
                     "token_in_build": "; ".join(f"{k}: {'default set' if r['default'] else 'EMPTY in release'}"
                                                 for k, r in sorted(g.items())),
                     "priority": "P1" if any(not r["default"] for r in g.values()) else "P3",
                     "what_it_does": "Google sign-in (iOS needs its own OAuth client id)"})
    return rows


def app_rows(reg: dict, app: str, a: dict) -> list[dict]:
    keys = json.loads(KEYS.read_text())["apps"] if KEYS.exists() else {}
    rows = _platform_rows(app, a)
    for p in sorted((p for p in reg["pairs"].values() if p["app"] == app),
                    key=lambda p: (STATUSES.index(p["status"]), p["vendor"].lower())):
        v = reg["vendors"].get(p["vendor"], {})
        names, state = _token_state(app, p["vendor"], keys)
        affiliate = p["vendor"] in AFFILIATE_VENDORS or "ffiliate" in (v.get("money") or "") \
            or "affiliate" in (v.get("kind") or "")
        empty = "EMPTY" in state or "not verified" in state or "not a valid" in state or "placeholder" in state \
            or "numeric" in state or "REPLACE" in state
        if p["status"] == "rejected":
            prio = "-"
        elif p["status"] == "in-code" and affiliate:
            prio = "P1"
        elif p["status"] == "in-code" and empty:
            prio = "P2"
        elif p["status"] == "in-code":
            prio = "P3"
        else:
            prio = "P4"
        rows.append({"vendor": p["vendor"], "kind": v.get("kind") or ("affiliate" if affiliate else "data-api"),
                     "money": v.get("money") or ("Affiliate commission" if affiliate else ""), "what_it_does": p.get("what_it_gives") or p.get("note") or "",
                     "signup_url": v.get("signup_url", ""), "commission": v.get("commission", ""),
                     "credential_names": names, "token_in_build": state,
                     "code_evidence": p.get("code_evidence", ""), "registry_status": p["status"],
                     "priority": prio, **{k: p.get(k, "") for k in MANUAL}})
    return rows


def export_apps(reg: dict) -> None:
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    apps = json.loads((M / "apps.json").read_text())["apps"]
    for a in apps:
        app = a["repo"]
        f = APPS_DIR / f"{app}.csv"
        kept = {}
        if f.exists():
            for r in csv.DictReader(open(f, newline="")):
                kept[r["vendor"]] = {k: r.get(k, "") for k in MANUAL + ["last_updated"]}
        rows = app_rows(reg, app, a)
        with open(f, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                r["app"] = app
                for k in MANUAL:
                    if kept.get(r["vendor"], {}).get(k):
                        r[k] = kept[r["vendor"]][k]
                r.setdefault("signup_status", "")
                if not r.get("signup_status"):
                    r["signup_status"] = "Not started"
                r["last_updated"] = kept.get(r["vendor"], {}).get("last_updated") or today()
                w.writerow({k: ("" if r.get(k) is None else r.get(k, "")) for k in COLUMNS})
    print(f"  -> {APPS_DIR}/<App>.csv for {len(apps)} apps")


def import_apps(reg: dict) -> int:
    n, problems = 0, []
    for f in sorted(APPS_DIR.glob("*.csv")):
        for i, r in enumerate(csv.DictReader(open(f, newline="")), 2):
            for k in MANUAL:
                if SECRET_LIKE.search(r.get(k) or ""):
                    problems.append(f"{f.name}:{i} {k} looks like a real secret — put only the vault reference name")
            if r.get("signup_status") and r["signup_status"] not in SIGNUP_VALUES:
                problems.append(f"{f.name}:{i} signup_status '{r['signup_status']}' not one of {SIGNUP_VALUES}")
    if problems:
        print("  refused, nothing imported:\n   " + "\n   ".join(problems))
        return 1
    for f in sorted(APPS_DIR.glob("*.csv")):
        for r in csv.DictReader(open(f, newline="")):
            key = f"{r['app']}|{r['vendor']}"
            p = reg["pairs"].get(key)
            if p is None:
                continue  # platform rows live in the measured docs, not the registry
            changed = {k: r[k] for k in MANUAL if (r.get(k) or "") != (p.get(k) or "")}
            if not changed:
                continue
            p.update(changed)
            if r.get("signup_status") in ("Approved", "Done"):
                upsert_pair(reg, r["app"], r["vendor"], "signed-up", "founder-csv")
            elif r.get("signup_status") == "Rejected":
                upsert_pair(reg, r["app"], r["vendor"], "rejected", "founder-csv")
            n += 1
    save(reg)
    print(f"  imported founder edits for {n} app/vendor pair(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-code", action="store_true")
    ap.add_argument("--import-research", type=pathlib.Path)
    ap.add_argument("--label", default=None, help="source label for an import, e.g. research-2026-10-12")
    ap.add_argument("--set", nargs=3, metavar=("APP", "VENDOR", "STATUS"))
    ap.add_argument("--workbook", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--export-apps", action="store_true")
    ap.add_argument("--import-apps", action="store_true")
    a = ap.parse_args()
    reg = load()
    if a.from_code:
        print(f"  code audit: {from_code(reg)} app/vendor hits synced")
    if a.import_research:
        added, rejected = import_research(reg, a.import_research, a.label or f"research-{today()}")
        print(f"  research: {added} new pairs, {rejected} rejected by verification")
    if a.set:
        app, vendor, status = a.set
        if status not in STATUSES:
            ap.error(f"status must be one of {STATUSES}")
        upsert_pair(reg, app, vendor, status, "founder")
    if a.import_apps and import_apps(reg):
        return 1
    if a.from_code or a.import_research or a.set:
        save(reg)
    if a.export_apps:
        export_apps(reg)
    if a.workbook:
        workbook(reg)
    if a.summary or not (a.from_code or a.import_research or a.set or a.workbook or a.export_apps or a.import_apps):
        summary(reg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
