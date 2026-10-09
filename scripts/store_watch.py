#!/usr/bin/env python3
"""Watch both stores, fix what is safely fixable, submit what is genuinely ready.

    python3 scripts/store_watch.py --dry-run
    python3 scripts/store_watch.py                 # one pass
    python3 scripts/store_watch.py --remediate     # also fix metadata drift

Built to run on a schedule. Each pass:

  1. reads the live state of all 43 apps on both stores;
  2. reads any new App Store rejection and classifies it by guideline;
  3. runs the submission gate;
  4. with --remediate, re-applies the metadata the gate found drifted;
  5. submits only the apps that pass the gate and carry no hold;
  6. writes docs/store-watch.json and prints a short report.

**It will not resubmit an app under a 4.3 or 2.1 hold, and that is the point.**
Apple's own words on the 4.3 rejections:

    If the app is resubmitted without substantial improvements, it will be
    rejected again, and may be rejected for additional issues.

A loop that resubmits on a timer would do exactly that, 14 times over, and
put the developer account at risk. So HOLD_GUIDELINES below is a refusal
list: an app whose latest Resolution Center message cites one of them is
reported and skipped until a person changes the app and clears the hold by
hand (`--clear-hold <app>`).

Reading rejection text needs an Apple ID web session, which expires. When it
is gone the pass still runs; it just cannot classify anything new, and says
so rather than assuming the holds are stale.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M, DIST  # noqa: E402

STATE = M / "docs/store-watch.json"
HOLDS = M / "docs/store-holds.json"

# A rejection citing any of these is a product problem, not a pipeline one.
# Resubmitting without a real change makes it worse.
HOLD_GUIDELINES = {
    "4.3": "Spam — duplicate or templated app",
    "4.2.6": "App generation service",
    "2.1": "Information needed — screen recording on a physical device",
    "5.1.1": "Privacy — data collection and storage",
    "4.2": "Minimum functionality",
}


def run(cmd, timeout=3600, cwd=M):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def classify(message: str) -> str | None:
    """The guideline a rejection cites, from its heading."""
    text = re.sub(r"<[^>]+>", "\n", message or "")
    for line in (l.strip() for l in text.split("\n")):
        if not line.lower().startswith("guideline"):
            continue
        for key in sorted(HOLD_GUIDELINES, key=len, reverse=True):
            if key in line:
                return key
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remediate", action="store_true")
    ap.add_argument("--clear-hold", metavar="APP")
    args = ap.parse_args()

    holds = json.loads(HOLDS.read_text()) if HOLDS.exists() else {}

    if args.clear_hold:
        if holds.pop(args.clear_hold, None) is None:
            print(f"  {args.clear_hold} was not on hold")
        else:
            HOLDS.write_text(json.dumps(holds, indent=1) + "\n")
            print(f"  hold cleared for {args.clear_hold} — it will be "
                  "submitted on the next pass if the gate passes")
        return 0

    now = datetime.datetime.now().isoformat(timespec="seconds")
    report = {"ran": now, "apple": {}, "play": {}, "holds": {}, "actions": []}

    # --- 1. live state --------------------------------------------------
    r = run(["bundle", "exec", "ruby", "scripts/asc_build_state.rb"])
    asc = json.loads((M / "docs/asc-build-state.json").read_text()) \
        if (M / "docs/asc-build-state.json").exists() else []
    states = {}
    for row in asc:
        states[row["repo"]] = row.get("review_state") or row.get("state")
    report["apple"] = {s: sum(1 for v in states.values() if v == s)
                       for s in set(states.values())}

    # --- 2. new rejections ----------------------------------------------
    rej_f = DIST / "rejections.json"
    before = set(holds)
    r = run(["bundle", "exec", "ruby", "scripts/testflight/rejection_reasons.rb"],
            timeout=3600)
    if rej_f.exists():
        for app, rec in json.loads(rej_f.read_text()).items():
            msgs = rec.get("messages") or []
            g = classify(msgs[-1] if msgs else "")
            if g:
                holds[app] = {"guideline": g, "why": HOLD_GUIDELINES[g],
                              "seen": now}
    else:
        report["actions"].append(
            "could not read Resolution Center — Apple ID session expired; "
            "holds left as they were")
    report["holds"] = {a: h["guideline"] for a, h in holds.items()}
    new = set(holds) - before
    if new:
        report["actions"].append(f"new holds: {', '.join(sorted(new))}")

    # --- 3. the gate ------------------------------------------------------
    # Re-measure the network first, so a host that went away since the last
    # pass fails the gate *before* anything is submitted.
    run(["python3", "scripts/verify_api_hosts.py"], timeout=1800)

    # Where production auth emails send people. A local site_url breaks
    # sign-up confirmation and password reset for every Supabase app at once.
    ac = run(["python3", "scripts/supabase_accounts.py", "--audit-config"],
             timeout=600)
    report["auth_config"] = (ac.stdout or "").strip().splitlines()

    # The marketing site's mobile pages are generated from store state. When
    # an app goes live (or is pulled), say so, so the site is regenerated
    # rather than left claiming the old state.
    ws = run(["python3", "scripts/website_apps.py", "--check"], timeout=900)
    if ws.returncode != 0:
        report["actions"].append(
            "website: app pages are out of date with store state — run "
            "scripts/website_apps.py and deploy www.safecodeg.com")
    if ac.returncode != 0:
        report["actions"].append(
            "auth config: production redirect is a LOCAL address (MA-042)")
    run(["python3", "scripts/store_checklist.py"], timeout=3600)
    gate = json.loads((M / "docs/store-checklist.json").read_text())
    gate = gate.get("apps", gate) if isinstance(gate, dict) and "apps" in gate else gate
    failing = {}
    for repo, a in (gate or {}).items():
        ch = a.get("checks") or a
        if not isinstance(ch, dict):
            continue
        bad = [k for k, v in ch.items() if str(v).startswith("FAIL")]
        if bad:
            failing[repo] = bad

    # --- 4. remediation that is safe to repeat ---------------------------
    if args.remediate and not args.dry_run:
        for cmd, label in [
            (["bundle", "exec", "ruby", "scripts/testflight/asc_readiness.rb", "--fix"],
             "store metadata"),
            (["bundle", "exec", "ruby", "scripts/testflight/review_notes.rb"],
             "review notes"),
            (["bundle", "exec", "ruby", "scripts/testflight/sync_age_rating.rb"],
             "age ratings"),
        ]:
            res = run(cmd)
            report["actions"].append(
                f"{label}: {'ok' if res.returncode == 0 else 'failed'}")

    # --- 5. submit only what is ready and unheld -------------------------
    ready = [r for r, s in states.items()
             if s in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED")
             and r not in holds and r not in failing]
    held_back = sorted(set(states) & set(holds))
    report["ready_to_submit"] = sorted(ready)
    report["held_back"] = held_back
    report["gate_failures"] = {k: v for k, v in sorted(failing.items())}

    if ready and not args.dry_run:
        res = run(["bundle", "exec", "ruby",
                   "scripts/testflight/submit_production.rb", *ready])
        report["actions"].append(
            f"submitted {len(ready)}: {'ok' if res.returncode == 0 else 'see log'}")
    elif ready:
        report["actions"].append(f"would submit {len(ready)}: {', '.join(ready)}")

    HOLDS.write_text(json.dumps(holds, indent=1) + "\n")
    STATE.write_text(json.dumps(report, indent=1) + "\n")

    print(f"  apple: {report['apple']}")
    print(f"  on hold (not resubmitted): {len(holds)}")
    for a, h in sorted(holds.items()):
        print(f"   {a:18} {h['guideline']:6} {h['why']}")
    print(f"  failing the gate: {len(failing)}")
    print(f"  submitted/ready : {len(ready)}")
    for a in report["actions"]:
        print(f"  - {a}")
    print(f"  -> {STATE.relative_to(M)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
