#!/usr/bin/env python3
"""Move every store listing to americangroup.ai the moment the domain serves the site.

    python3 scripts/domain_cutover.py --check     # report only
    python3 scripts/domain_cutover.py             # run each step whose precondition holds
    python3 scripts/domain_cutover.py --watch     # poll every 10 min until done

The code moved on 2026-10-09: every repo, the store copy and the fastlane
metadata say americangroup.ai, and the website branch domain/americangroup-ai
301-redirects safecodeg.com to it. What could not move with the code:

  americangroup.ai served a HostGator WordPress "Coming Soon" page from its own
  docroot. Merging the website branch before that changes would redirect the
  live site, and the privacy URL of every store listing, to the placeholder.

So the steps run in order, each only when the previous one is proven live:

  1. americangroup.ai serves this site        (owner: cPanel docroot -> public_html)
  2. merge domain/americangroup-ai to main     (the website's workflow deploys it)
  3. safecodeg.com answers 301 -> americangroup.ai, policy pages load there
  4. App Store Connect: deliver_metadata.py    (support / privacy / marketing URLs + copy)
  5. Google Play: play_gap_audit.py --fix --domain   (contact email + website)

Play's privacy-policy URL has no API; once step 3 holds, the old URL already
redirects to the same page on americangroup.ai, so nothing breaks while a
person updates it in Play Console (MA-045).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M, DIST  # noqa: E402

SITE = ROOT / "americangroup.ai"
BRANCH = "domain/americangroup-ai"
STATE = DIST / "domain-cutover.json"
TITLE = "American Group LLC"
PROBE = "/policy/virtuband/delete-account.html"


def fetch(url: str, follow=True) -> tuple[str, str, str]:
    """(http code, final/redirect url, body)."""
    args = ["curl", "-s", "-m", "25", "-o", "-", "-w", "\n%{http_code} %{redirect_url}"]
    if follow:
        args.insert(1, "-L")
    r = subprocess.run(args + [url], capture_output=True, text=True)
    body, _, tail = r.stdout.rpartition("\n")
    code, _, redir = tail.partition(" ")
    return code, redir, body


def serves_site() -> tuple[bool, str]:
    code, _, body = fetch("https://americangroup.ai/")
    m = re.search(r"<title>([^<]*)</title>", body, re.I)
    title = m.group(1) if m else ""
    return (code == "200" and TITLE in title), f"{code} '{title[:60]}'"


def policy_live(host: str) -> tuple[bool, str]:
    code, _, body = fetch(f"https://{host}{PROBE}")
    ok = code == "200" and "delete" in body.lower() and "Enterprise Technology & Mobile Apps" not in body
    return ok, f"{code} {len(body)} bytes"


def redirects() -> tuple[bool, str]:
    code, redir, _ = fetch(f"https://safecodeg.com{PROBE}", follow=False)
    return (code == "301" and redir.startswith("https://www.americangroup.ai/")), f"{code} -> {redir}"


def merged() -> bool:
    """The domain move is in main. The site repo has one branch since
    2026-10-09; the move branch was merged and deleted (tag
    archive/domain-americangroup-ai), so check main's .htaccess instead."""
    r = subprocess.run(["git", "-C", str(SITE), "show", "origin/main:.htaccess"],
                       capture_output=True, text=True)
    return re.search(r"Canonical host: (www\.)?americangroup\.ai", r.stdout) is not None


def run(cmd, timeout=7200):
    r = subprocess.run(cmd, cwd=M, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def step(state: dict, check_only: bool) -> dict:
    ok, why = serves_site()
    state["1_serves_site"] = why
    if not ok:
        state["next"] = "owner: cPanel -> Domains -> americangroup.ai -> document root /home2/safecode/americangroup.ai (the site is already deployed there; it currently points at public_html/website_d85c586d, a Coming Soon page)"
        return state
    subprocess.run(["git", "-C", str(SITE), "fetch", "-q", "origin"])
    if not merged():
        if check_only:
            state["next"] = f"merge {BRANCH} to main"
            return state
        cmds = [["git", "-C", str(SITE), "checkout", "-q", "main"],
                ["git", "-C", str(SITE), "pull", "-q", "--ff-only"],
                ["git", "-C", str(SITE), "merge", "-q", "--no-edit", f"origin/{BRANCH}"],
                ["git", "-C", str(SITE), "push", "-q", "origin", "main"]]
        for c in cmds:
            r = subprocess.run(c, capture_output=True, text=True)
            if r.returncode:
                state["2_merge"] = f"failed: {' '.join(c[3:])}: {r.stderr.strip()[:200]}"
                return state
        state["2_merge"] = "merged and pushed; waiting for the website workflow to deploy"
        return state
    state["2_merge"] = "merged"
    ok3, why3 = redirects()
    okp, whyp = policy_live("www.americangroup.ai")
    state["3_redirect"], state["3_policy"] = why3, whyp
    # safecodeg.com redirects only once public_html carries the new .htaccess;
    # a push deploys americangroup.ai alone, so ask for the both-folders run
    # (no --delete) once, when americangroup.ai is proven live.
    if okp and not ok3 and not state.get("2b_public_html_deploy") and not check_only:
        r = subprocess.run(["gh", "workflow", "run", "deploy.yml", "-R", "AmericanGroupLLC/americangroup.ai",
                            "--ref", "main", "-f", "target=both"], capture_output=True, text=True)
        state["2b_public_html_deploy"] = "requested" if r.returncode == 0 else f"failed: {r.stderr.strip()[:160]}"
    if not (ok3 and okp):
        state["next"] = "waiting for the deploy (redirect + policy page on americangroup.ai)"
        return state
    if check_only:
        state["next"] = "push store metadata"
        return state
    if not state.get("4_app_store"):
        rc, out = run(["python3", "scripts/deliver_metadata.py"])
        state["4_app_store"] = "ok" if rc == 0 else f"rc={rc}: {out[-300:]}"
    if not state.get("5_play"):
        rc, out = run(["python3", "scripts/play_gap_audit.py", "--fix", "--domain"])
        state["5_play"] = "ok" if rc == 0 else f"rc={rc}: {out[-300:]}"
    rc, out = run(["python3", "scripts/verify_policy_urls.py"])
    state["6_verify_policy_urls"] = out[-300:]
    state["next"] = "done — update Play privacy-policy URLs in Console (MA-045)"
    state["done"] = True
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--watch", action="store_true")
    args = ap.parse_args()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    while True:
        state = step(state, args.check)
        state["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STATE.write_text(json.dumps(state, indent=1) + "\n")
        for k, v in state.items():
            print(f"  {k}: {v}")
        if not args.watch or state.get("done"):
            return 0
        time.sleep(600)


if __name__ == "__main__":
    raise SystemExit(main())
