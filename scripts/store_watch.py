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
While any app holds a 5.6 finding it submits nothing at all (ACCOUNT_FREEZE).
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
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M, DIST  # noqa: E402

STATE = M / "docs/store-watch.json"
HOLDS = M / "docs/store-holds.json"

# A rejection citing any of these is a product problem, not a pipeline one.
# Resubmitting without a real change makes it worse.
HOLD_GUIDELINES = {
    # Sixteen apps received this on 2026-10-08 within the same minute, each on
    # its first review, three days after 26 apps were rejected under 4.3.
    # Identical text across 16 apps at once is a judgment about the account's
    # submission pattern, not about one binary. See ACCOUNT_FREEZE below.
    "5.6": "Developer Code of Conduct — 'features intentionally hidden during review'",
    "4.3": "Spam — duplicate or templated app",
    "4.2.6": "App generation service",
    "2.1": "Information needed — screen recording on a physical device",
    "5.1.1": "Privacy — data collection and storage",
    "4.2": "Minimum functionality",
}


# Every step of the pass, in order, with how it ended. A step that times out
# or cannot start used to raise out of main(): the 03:17 and 15:17 passes on
# 2026-10-13 died that way and never wrote a report (issue #32). Now the step
# is recorded as FAILED with its reason and the pass carries on.
STEPS: list[dict] = []


def run(cmd, timeout=3600, cwd=M, expect=(0,)):
    """Run one step; never raise. A failure comes back as a nonzero returncode.

    `expect` lists exit codes that are a finding the caller handles (e.g.
    website_apps.py --check exits 1 when the site would change), not a
    failure of the step.
    """
    name = " ".join(str(c) for c in cmd if c not in ("bundle", "exec", "ruby", "python3"))
    print(f"  [{datetime.datetime.now():%H:%M:%S}] start  {name}", flush=True)
    t0 = time.monotonic()
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                             timeout=timeout)
        status = "OK" if res.returncode in expect else "FAILED"
        reason = "" if res.returncode == 0 else f"exit {res.returncode}"
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        res = subprocess.CompletedProcess(cmd, 124, out, err)
        status, reason = "FAILED", f"timed out after {timeout} s"
    except OSError as e:  # the program is missing or cannot be executed
        res = subprocess.CompletedProcess(cmd, 127, "", "")
        status, reason = "FAILED", f"could not start: {e}"
    secs = round(time.monotonic() - t0, 1)
    if status != "OK":
        tail = (res.stderr or res.stdout or "").strip().splitlines()[-1:]
        if tail:
            reason += f" — {tail[0][:200]}"
    STEPS.append({"step": name, "status": status, "seconds": secs, "reason": reason})
    print(f"  [{datetime.datetime.now():%H:%M:%S}] {status:6} {name} ({secs} s)"
          + (f": {reason}" if reason else ""), flush=True)
    return res



# Guidelines that are about the account, not the app. While any app holds
# one, no app is submitted automatically: more submissions are more of the
# pattern Apple objected to, and the next step after 5.6 can be termination
# of the developer account.
ACCOUNT_FREEZE = {"5.6"}


def classify(message: str) -> str | None:
    """The guideline a rejection cites, from its heading."""
    text = re.sub(r"<[^>]+>", "\n", message or "")
    for line in (l.strip() for l in text.split("\n")):
        if not line.lower().startswith("guideline"):
            continue
        for key in sorted(HOLD_GUIDELINES, key=len, reverse=True):
            if re.search(rf"(?<![\d.]){re.escape(key)}(?![\d])", line):
                return key
    return None


def classify_thread(messages: list[str]) -> str | None:
    """The most serious guideline anywhere in the thread.

    Reading one message missed findings: the thread mixes Apple's messages
    with our replies, and its order was never guaranteed.
    """
    found = {g for g in (classify(m) for m in messages) if g}
    for key in HOLD_GUIDELINES:  # dict order is severity order
        if key in found:
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
    # --session-only: never fall back to a password sign-in from a schedule;
    # that pushes a 2FA code to the owner's devices on every pass.
    r = run(["bundle", "exec", "ruby", "scripts/testflight/rejection_reasons.rb",
             "--session-only"],
            timeout=3600, expect=(0, 3))  # 3: no Apple ID session, reported below
    if rej_f.exists():
        for app, rec in json.loads(rej_f.read_text()).items():
            msgs = rec.get("messages") or []
            g = classify_thread(msgs)
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
             timeout=600, expect=(0, 1))  # 1: local redirect, reported below
    report["auth_config"] = (ac.stdout or "").strip().splitlines()

    # The marketing site's mobile pages are generated from store state. When
    # an app goes live (or is pulled), say so, so the site is regenerated
    # rather than left claiming the old state.
    ws = run(["python3", "scripts/website_apps.py", "--check"], timeout=900,
             expect=(0, 1))  # 1: the site would change, reported below
    # Only the finding code means what the message says; a timeout or crash
    # is reported as a FAILED step instead.
    if ws.returncode == 1:
        report["actions"].append(
            "website: app pages are out of date with store state — run "
            "scripts/website_apps.py and deploy www.americangroup.ai")
    if ac.returncode == 1:
        report["actions"].append(
            "auth config: production redirect is a LOCAL address (MA-042)")
    run(["python3", "scripts/store_checklist.py"], timeout=3600)
    try:
        gate = json.loads((M / "docs/store-checklist.json").read_text())
    except (OSError, ValueError) as e:
        gate = {}
        STEPS.append({"step": "read docs/store-checklist.json", "status": "FAILED",
                      "seconds": 0, "reason": str(e)[:200]})
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
    frozen = sorted(a for a, h in holds.items() if h["guideline"] in ACCOUNT_FREEZE)
    report["account_freeze"] = frozen
    if frozen and ready:
        report["actions"].append(
            f"ACCOUNT FREEZE: {len(frozen)} app(s) hold a 5.6 finding, so none of "
            f"{len(ready)} ready app(s) were submitted: {', '.join(sorted(ready))}")
        ready = []
    # A step the submission decision rests on did not finish, so the state it
    # would have refreshed (store state, rejections, hosts, the gate) may be
    # stale. Submit nothing on stale evidence.
    gate_steps = ("asc_build_state", "rejection_reasons", "verify_api_hosts",
                  "store_checklist", "store-checklist.json")
    blind = [s["step"] for s in STEPS
             if s["status"] != "OK" and any(g in s["step"] for g in gate_steps)]
    if blind and ready:
        report["actions"].append(
            f"NOT SUBMITTING {len(ready)} ready app(s): a gate step failed "
            f"({'; '.join(blind)})")
        ready = []
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

    report["steps"] = STEPS
    bad = [st for st in STEPS if st["status"] != "OK"]
    for st in bad:
        report["actions"].append(f"FAILED step: {st['step']} — {st['reason']}")

    HOLDS.write_text(json.dumps(holds, indent=1) + "\n")
    STATE.write_text(json.dumps(report, indent=1) + "\n")

    print(f"  apple: {report['apple']}")
    print(f"  on hold (not resubmitted): {len(holds)}")
    for a, h in sorted(holds.items()):
        print(f"   {a:18} {h['guideline']:6} {h['why']}")
    if frozen:
        print(f"  ACCOUNT FREEZE (5.6 on {len(frozen)} apps): no automatic submissions")
    print(f"  failing the gate: {len(failing)}")
    print(f"  submitted/ready : {len(ready)}")
    for a in report["actions"]:
        print(f"  - {a}")
    print(f"  steps: {len(STEPS) - len(bad)} ok, {len(bad)} failed")
    print(f"  -> {STATE.relative_to(M)}")
    # 0: every step ran. 2: the pass finished and wrote its report, but a
    # step failed (listed above). A crash would be 1 with a traceback.
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
