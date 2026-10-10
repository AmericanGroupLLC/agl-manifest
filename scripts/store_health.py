#!/usr/bin/env python3
"""Daily store health: everything the stores and reviewers see, checked from CI.

    python3 scripts/store_health.py            # exit 1 if any check fails
    python3 scripts/store_health.py --markdown # also write store-health.md (the CI issue body)

Run by .github/workflows/store-health.yml so none of this depends on the
laptop. Each check is an existing script; this only runs them and decides
pass/fail from their own summary line.

  asc state        scripts/asc_build_state.rb           (App Store Connect API key)
  policy pages     scripts/verify_policy_urls.py         147 privacy/support/terms/delete URLs
  deletion pages   scripts/verify_deletion_urls.py       43 account-deletion pages
  App Store URLs   scripts/testflight/asc_urls.rb --check  every app's privacy/support/marketing URL
  Play contact     scripts/play_gap_audit.py --domain    contact email/website not on the old domain
  version codes    scripts/preflight_version_codes.py    informational — ship.yml bumps automatically
  requirements     scripts/apple_requirements.py         informational — known product gaps, tracked in the stand-up
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

M = pathlib.Path(__file__).resolve().parents[1]


def run(cmd: list[str], timeout=1800) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=M, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def last(text: str, pattern: str) -> str:
    hits = [l.strip() for l in text.splitlines() if re.search(pattern, l)]
    return hits[-1] if hits else (text.strip().splitlines() or ["no output"])[-1][:200]


def main() -> int:
    rows: list[tuple[str, str, str]] = []

    rc, out = run(["bundle", "exec", "ruby", "scripts/asc_build_state.rb"])
    rows.append(("App Store Connect state refreshed", "PASS" if rc == 0 else "FAIL", last(out, r"apps|->|error")))

    for attempt in (1, 2):   # one retry: a single unreachable fetch is not an outage
        rc, out = run(["python3", "scripts/verify_policy_urls.py"])
        m = re.search(r"(\d+)/(\d+) URLs serve the right page; (\d+) app", out)
        if m and m.group(3) == "0":
            break
    rows.append(("Policy pages (privacy, support, terms, delete)",
                 "PASS" if m and m.group(3) == "0" else "FAIL", last(out, r"URLs serve")))

    rc, out = run(["python3", "scripts/verify_deletion_urls.py"])
    m = re.search(r"BROKEN: (\d+)", out)
    rows.append(("Account-deletion pages", "PASS" if m and m.group(1) == "0" else "FAIL", last(out, r"BROKEN")))

    rc, out = run(["bundle", "exec", "ruby", "scripts/testflight/asc_urls.rb", "--check"])
    m = re.search(r"(\d+) app\(s\) need changes", out)
    rows.append(("App Store privacy/support/marketing URLs", "PASS" if m and m.group(1) == "0" else "FAIL",
                 last(out, r"need changes|FAILED")))

    rc, out = run(["python3", "scripts/play_gap_audit.py", "--domain"])
    stale = [l.split()[0] for l in out.splitlines() if re.search(r"contactEmail|contactWebsite", l)]
    rows.append(("Play contact email/website on americangroup.ai", "PASS" if rc == 0 and not stale else "FAIL",
                 ", ".join(stale) or last(out, r"apps|error")))

    run(["python3", "scripts/play_version_codes.py"])
    rc, out = run(["python3", "scripts/preflight_version_codes.py", "--check"])
    rows.append(("Version codes ahead of Play (info; ship.yml bumps)", "INFO", last(out, r"past what Play|would be rejected")))

    rc, out = run(["python3", "scripts/apple_requirements.py"])
    rows.append(("Apple requirements (info; see stand-up)", "INFO", last(out, r"requirements:")))

    for name, state, detail in rows:
        print(f"  {state:4} {name:52} {detail}")
    fails = [r for r in rows if r[1] == "FAIL"]
    print(f"\n  {len(rows)} checks, {len(fails)} failing")
    if "--markdown" in sys.argv:
        md = ["| State | Check | Detail |", "| --- | --- | --- |"] + [f"| {s} | {n} | {d} |" for n, s, d in rows]
        (M / "store-health.md").write_text("\n".join(md) + "\n")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
