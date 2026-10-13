#!/usr/bin/env python3
"""The founder's vendor sign-up tracker — ONE Excel file.

    .venv/bin/python3 scripts/signup_playbook.py      # refreshes ~/agl/AGL_Vendor_Signup_Playbook.xlsx

The workbook is the single tracker (founder's request, 2026-10-13): the founder
edits status, owner, dates, vault references and notes in it directly. A
refresh reads those columns back FROM the workbook and keeps them, refuses to
run while Excel has it open (the ~$ lock file), and first copies the previous
version to ~/agl/.dist/backups/. store/vendors/signup_playbook.csv is written
alongside as a history snapshot for git — nobody edits it.

Sheets:
  Start here       how to work through it, batch order, the no-secrets rule
  Company profile  answers every sign-up form asks — fill once, reuse everywhere
  Signups          one row per vendor, grouped in batches so a vendor several
                   apps need is done once: where to sign up (URL checked live),
                   how to join, what to submit, what you receive, where in their
                   dashboard it appears, where it goes in our system, apps that
                   need it (from the code), cost, approval — plus your columns
  Per app          every app × vendor, with your status pulled from Signups by
                   formula, so marking a vendor Done updates every app
  Batches          the sign-up sessions, in order

Sources: store/vendors/playbook.json (how-to text, written from knowledge — the
sheet says "confirm on the page"), store/vendors/url-checks.json (each URL
probed with probe_urls.py), store/vendors/signups.csv (needed_by_apps,
credentials and their state in the build, measured from the code), docs/ store
state. Founder columns are preserved from the existing CSV; a cell that looks
like a real key or token stops the run.
"""

from __future__ import annotations

import csv
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402
from vendor_registry import SECRET_LIKE  # noqa: E402

V = M / "store/vendors"
XLSX = ROOT / "AGL_Vendor_Signup_Playbook.xlsx"
CSV_OUT = V / "signup_playbook.csv"
MANUAL = ["status", "account_owner", "applied_on", "approved_on", "id_or_vault_ref", "your_notes"]
STATUS_LIST = ["Not started", "Applied", "Approved", "Rejected", "Done", "Not needed"]
COLS = ["priority", "batch", "vendor", "how_to_join", "signup_url", "url_check", "what_to_submit", "what_you_receive",
        "where_to_find_it", "where_it_goes_in_our_system", "needed_by_apps", "suits_apps", "credential_names",
        "state_in_current_build", "cost", "approval", "notes"] + MANUAL


def load(p, default):
    p = pathlib.Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def main() -> int:
    pb = load(V / "playbook.json", {})
    checks = load(V / "url-checks.json", {}).get("results", {})
    sig = {r["vendor"]: r for r in csv.DictReader(open(V / "signups.csv", newline=""))}
    lock = XLSX.with_name("~$" + XLSX.name)
    if lock.exists():
        print(f"refused — {XLSX.name} is open in Excel ({lock.name} exists). Save and close it, then re-run.")
        return 1
    kept = {}
    if XLSX.exists():  # the founder's edits live in the workbook
        from openpyxl import load_workbook
        ws = load_workbook(XLSX, read_only=True)["Signups"]
        it = ws.iter_rows(values_only=True)
        hdr = list(next(it))
        for row in it:
            d = dict(zip(hdr, row))
            if d.get("vendor"):
                kept[d["vendor"]] = {k: ("" if d.get(k) is None else str(d.get(k))) for k in MANUAL}
    elif CSV_OUT.exists():
        for r in csv.DictReader(open(CSV_OUT, newline="")):
            kept[r["vendor"]] = {k: r.get(k, "") for k in MANUAL}
    bad = [f"{v}: {k}" for v, m in kept.items() for k in MANUAL if SECRET_LIKE.search(m.get(k) or "")]
    if bad:
        print("refused — these cells look like real secrets; replace with a vault reference name:\n  " + "\n  ".join(bad))
        return 1

    rows = []
    for name, p in pb.items():
        s = sig.get(name, {})
        status_default = s.get("signup_status") or ("Done" if p["batch"].startswith("0 Done") else
                                                   "Not needed" if p["batch"].startswith("0 No signup") else "Not started")
        m = kept.get(name, {})
        rows.append({
            "priority": s.get("priority") or ("P4" if p["batch"].startswith("7") else "P3"),
            "batch": p["batch"], "vendor": name, "how_to_join": p["how_to_join"], "signup_url": p["signup_url"],
            "url_check": checks.get(p["signup_url"], "—" if not p["signup_url"] else "not checked"),
            "what_to_submit": p["what_to_submit"], "what_you_receive": p["what_you_receive"],
            "where_to_find_it": p["where_credential"], "where_it_goes_in_our_system": p["where_it_goes"],
            "needed_by_apps": s.get("needed_by_apps", ""), "suits_apps": s.get("suits_apps", ""),
            "credential_names": s.get("credential_names", ""), "state_in_current_build": s.get("token_in_build", ""),
            "cost": p["cost"], "approval": p["approval"], "notes": p["notes"],
            "status": m.get("status") or status_default, **{k: m.get(k, "") for k in MANUAL[1:]}})
    rows.sort(key=lambda r: (r["batch"], r["priority"], r["vendor"].lower()))
    with open(CSV_OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    # ---------- workbook ----------
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    bold = Font(bold=True)
    head_fill = PatternFill("solid", fgColor="1F3864")
    head_font = Font(bold=True, color="FFFFFF")
    wrap = Alignment(wrap_text=True, vertical="top")

    def header(ws, cols, widths=None):
        ws.append(cols)
        for i, c in enumerate(ws[1], 1):
            c.fill, c.font, c.alignment = head_fill, head_font, Alignment(wrap_text=True, vertical="center")
            ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(cols[i - 1], 18)
        ws.freeze_panes = "C2"

    # Start here
    st = wb.active
    st.title = "Start here"
    today = datetime.date.today().isoformat()
    lines = [
        ("Vendor sign-up playbook — American Group LLC", True),
        (f"Generated {today} by scripts/signup_playbook.py. Re-run it any time; your columns are kept.", False),
        ("", False),
        ("How to work through it", True),
        ("1. Fill the 'Company profile' sheet once — almost every form asks the same things.", False),
        ("2. Go to 'Signups' and work batch by batch (column B). One batch = one sitting, e.g. one Google Cloud session covers 7 apps' sign-in IDs.", False),
        ("3. Open signup_url. 'url_check' says whether it answered when probed today; 'open in a browser' means the site blocks automated checks, not that it is wrong.", False),
        ("4. Submit what 'what_to_submit' lists, then find your ID/key where 'where_to_find_it' says.", False),
        ("5. Set 'status' (dropdown) and dates. In 'id_or_vault_ref' put ONLY where the secret lives (e.g. 'GitHub secret AMAZON_TAG_CALCMASTER') — never the key itself.", False),
        ("6. 'Per app' fills its status column from 'Signups' automatically.", False),
        ("7. Tell the AI office (issue #26/#30) when a batch is done: it wires public IDs into the builds and secret keys into a Supabase Edge Function.", False),
        ("", False),
        ("What is measured vs. written", True),
        ("Measured: needed_by_apps, credential_names, state_in_current_build (from the app code), url_check (live probe), store links/state (App Store Connect / Play).", False),
        ("Written from knowledge — confirm on the vendor page: how_to_join, what_to_submit, what_you_receive, where_to_find_it, cost, approval.", False),
        ("Priority: P1 links already in the code earn as soon as you have the ID · P2 an API in the code whose key is empty · P3 working / no sign-up · P4 no app uses it yet (earns nothing until built).", False),
    ]
    for t, b in lines:
        st.append([t])
        st.cell(st.max_row, 1).font = Font(bold=b, size=14 if b and st.max_row == 1 else 11)
    st.column_dimensions["A"].width = 150

    # Company profile
    cp = wb.create_sheet("Company profile")
    header(cp, ["field", "value", "note"], {"field": 34, "value": 60, "note": 70})
    for f, v, n in [
        ("Legal company name", "American Group LLC", ""),
        ("Website", "https://www.americangroup.ai", "Live (domain monitor)"),
        ("Business email for sign-ups", "", "Use a role mailbox, e.g. partners@ or support@americangroup.ai — create it first (MA-045)"),
        ("Contact name / title", "", "fill once"),
        ("Business address", "", "fill once"),
        ("Phone", "", "fill once"),
        ("EIN (US tax ID)", "", "Needed for W-9 — store in your vault, not here; write only 'in vault: …'"),
        ("Tax form", "W-9 (US LLC)", "Most US affiliate programmes ask for it before paying"),
        ("Payout method", "", "bank account / PayPal — reference only"),
        ("Promotion method (paste)", "In-app links inside our own mobile apps (iOS and Android), shown next to the relevant feature, with an affiliate disclosure.", ""),
        ("Monthly audience (paste)", "", "Be truthful — the apps are pre-launch or newly live; do not inflate"),
    ]:
        cp.append([f, v, n])
    cp.append([])
    cp.append(["App", "Bundle id / package", "Google Play listing", "Play state", "App Store (Apple ID)", "Privacy policy URL"])
    for c in cp[cp.max_row]:
        c.font = bold
    apps = load(M / "apps.json", {}).get("apps", [])
    play = {x["repo"]: x for x in load(M / "docs/play-production-blockers.json", {}).get("apps", [])}
    asc_rows = load(M / "docs/asc-build-state.json", [])
    asc = {x.get("repo"): x for x in (asc_rows if isinstance(asc_rows, list) else asc_rows.get("apps", []))}
    pol = load(DIST / "policy-urls.json", {})
    for a in apps:
        r = a["repo"]
        pkg = a.get("application_id") or a.get("bundle_id")
        live = (play.get(r) or {}).get("state")
        cp.append([r, pkg, f"https://play.google.com/store/apps/details?id={pkg}", live or "",
                   f"https://apps.apple.com/app/id{(asc.get(r) or {}).get('apple_id')} (not public until approved)"
                   if (asc.get(r) or {}).get("apple_id") else "no App Store record",
                   ((pol.get(r) or {}).get("privacy") or {}).get("url", "")])

    # Signups
    sg = wb.create_sheet("Signups")
    widths = {"priority": 8, "batch": 22, "vendor": 26, "how_to_join": 34, "signup_url": 40, "url_check": 30,
              "what_to_submit": 60, "what_you_receive": 34, "where_to_find_it": 44, "where_it_goes_in_our_system": 40,
              "needed_by_apps": 30, "suits_apps": 26, "credential_names": 26, "state_in_current_build": 40,
              "cost": 22, "approval": 26, "notes": 40, "status": 14, "account_owner": 18, "applied_on": 12,
              "approved_on": 12, "id_or_vault_ref": 30, "your_notes": 30}
    header(sg, COLS, widths)
    pri_fill = {"P1": "FFE699", "P2": "FCE4D6", "P3": "E2EFDA", "P4": "F2F2F2"}
    for r in rows:
        sg.append([r[c] for c in COLS])
        rr = sg.max_row
        for c in sg[rr]:
            c.alignment = wrap
        sg.cell(rr, 1).fill = PatternFill("solid", fgColor=pri_fill.get(r["priority"], "FFFFFF"))
        if r["signup_url"]:
            cell = sg.cell(rr, COLS.index("signup_url") + 1)
            cell.hyperlink, cell.font = r["signup_url"], Font(color="0563C1", underline="single")
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUS_LIST) + '"', allow_blank=True)
    sg.add_data_validation(dv)
    sc = get_column_letter(COLS.index("status") + 1)
    dv.add(f"{sc}2:{sc}{sg.max_row}")
    sg.auto_filter.ref = sg.dimensions

    # Per app
    pa = wb.create_sheet("Per app")
    header(pa, ["app", "vendor", "relation", "priority", "batch", "status (from Signups)", "credential names"],
           {"app": 18, "vendor": 30, "relation": 24, "priority": 8, "batch": 24, "status (from Signups)": 18,
            "credential names": 34})
    vcol, scol = get_column_letter(COLS.index("vendor") + 1), get_column_letter(COLS.index("status") + 1)
    n = len(rows) + 1
    pairs = []
    for r in rows:
        for app in [x.strip() for x in r["needed_by_apps"].split(";") if x.strip()]:
            pairs.append((app, r, "needed (in the code)"))
        for app in [x.strip() for x in r["suits_apps"].split(";") if x.strip() and "all apps" not in x]:
            pairs.append((app, r, "suggested (not built)"))
    for app, r, rel in sorted(pairs, key=lambda x: (x[0].lower(), x[2], x[1]["priority"])):
        pa.append([app, r["vendor"], rel, r["priority"], r["batch"], None, r["credential_names"]])
        rr = pa.max_row
        pa.cell(rr, 6).value = f'=IFERROR(INDEX(Signups!${scol}$2:${scol}${n},MATCH(B{rr},Signups!${vcol}$2:${vcol}${n},0)),"")'
    pa.auto_filter.ref = pa.dimensions

    # Batches
    bt = wb.create_sheet("Batches")
    header(bt, ["batch", "vendors", "apps covered (needed)", "what this sitting achieves"],
           {"batch": 26, "vendors": 60, "apps covered (needed)": 60, "what this sitting achieves": 70})
    what = {"0 Done": "Accounts already exist — nothing to do.",
            "0 No signup": "Public sources — nothing to sign up for (check terms).",
            "1 Travelpayouts (TripNest)": "One account + joining brands inside it makes every TripNest partner link earn.",
            "2 Retail affiliates": "Amazon tags for CalcMaster/ChefCount/VirtuBand; networks (Rakuten, Awin, CJ, Impact) unlock many brands at once.",
            "3 Google Cloud console": "iOS sign-in client IDs for 7 apps, Maps keys, AI key and the AdMob apps — one console session.",
            "4 Free data keys": "Free keys that turn on iMaps' fire, EV-charging and alt-fuel layers (minutes each).",
            "5 AI / server-side keys": "Paid keys kept server-side: PilotEnRoute's AI, CalcMaster subscriptions.",
            "6 Optional monitoring": "Optional — Crashlytics already reports crashes.",
            "7 Later (no app uses it yet)": "Only after an app is built to use it."}
    by = {}
    for r in rows:
        by.setdefault(r["batch"], []).append(r)
    for b in sorted(by):
        need = sorted({a.strip() for r in by[b] for a in r["needed_by_apps"].split(";") if a.strip()})
        bt.append([b, ", ".join(r["vendor"] for r in by[b]), ", ".join(need), what.get(b, "")])
        for c in bt[bt.max_row]:
            c.alignment = wrap

    if XLSX.exists():
        import shutil
        bk = ROOT / ".dist/backups"
        bk.mkdir(parents=True, exist_ok=True)
        shutil.copy2(XLSX, bk / f"{XLSX.stem}-{datetime.datetime.now():%Y%m%d-%H%M%S}.xlsx")
    wb.save(XLSX)
    print(f"  -> {XLSX}  ({len(rows)} vendors, {len(pairs)} app/vendor rows)")
    print(f"  -> {CSV_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
