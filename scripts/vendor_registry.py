#!/usr/bin/env python3
"""The vendor registry: every affiliate programme, data API and partner per app, kept and added to.

    python3 scripts/vendor_registry.py --from-code                 # sync what the app code uses
    python3 scripts/vendor_registry.py --import-research run.json  # merge a vendor-scout result
    python3 scripts/vendor_registry.py --set GadgetNest "Best Buy" signed-up
    .venv/bin/python3 scripts/vendor_registry.py --workbook        # regenerate the measured xlsx
    python3 scripts/vendor_registry.py --summary

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
    if DIRECTORY.exists():
        md = wb.create_sheet("Measured - code audit", 1)
        for r in csv.reader(open(DIRECTORY)):
            md.append(r)
        for c in md[1]:
            c.font = Font(bold=True)
    wb.save(WB_OUT)
    print(f"  -> {WB_OUT}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-code", action="store_true")
    ap.add_argument("--import-research", type=pathlib.Path)
    ap.add_argument("--label", default=None, help="source label for an import, e.g. research-2026-10-12")
    ap.add_argument("--set", nargs=3, metavar=("APP", "VENDOR", "STATUS"))
    ap.add_argument("--workbook", action="store_true")
    ap.add_argument("--summary", action="store_true")
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
    if a.from_code or a.import_research or a.set:
        save(reg)
    if a.workbook:
        workbook(reg)
    if a.summary or not (a.from_code or a.import_research or a.set or a.workbook):
        summary(reg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
