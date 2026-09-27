#!/usr/bin/env python3
"""Check that every store policy URL serves that app's own page.

    python3 scripts/verify_policy_urls.py            # -> ~/agl/.dist/policy-urls.json
    python3 scripts/verify_policy_urls.py CalcMaster

**A 200 is not evidence.** www.safecodeg.com is a single-page app and answers
every unmatched path with its own index, so a policy URL for an app that does
not exist returns 200 with ~369 KB of SPA shell. An earlier sweep recorded 131
URLs as passing while none of the pages was actually published.

So each URL has to prove three things:

  * it is not the SPA fallback — compared against a deliberately nonsense
    control path fetched in the same run, rather than a hardcoded size;
  * its <title> names the app it belongs to, which catches a page that is real
    but wired to the wrong slug;
  * it is not an error page.

Apple and Google both reject a listing whose privacy URL does not resolve, and
Play additionally requires the account-deletion URL for any app with accounts.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import html
import re
import sys
import urllib.error
import urllib.request

import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST  # noqa: E402
M = MANIFEST
OUT = ROOT / ".dist/policy-urls.json"
BASE = "https://www.safecodeg.com/policy"
CONTROL = f"{BASE}/definitely-not-an-app-control/"

TITLE = re.compile(r"<title>([^<]*)</title>", re.I)


def _norm(s: str) -> str:
    """Lowercase, alphanumerics only - so "Radio Tune", "ratiotune" and
    "Uscis-Case" all compare on equal terms. Entities are decoded first, or
    "Support &middot; Radio Tune" contributes a literal "middot".
    """
    return re.sub(r"[^a-z0-9]", "", html.unescape(s).lower())


def _same_app(identities: set[str], title: str) -> bool:
    """Whether a page title belongs to one of this app's names.

    Containment alone is not enough. The store name is "Radio Tune: Live Radio"
    and the page is titled "Radio Tune - Privacy Policy" — neither contains the
    other, but they share a leading name. So accept containment either way, or
    a common prefix long enough not to collide across a 43-app portfolio.
    """
    page = _norm(title)
    if not page:
        return False
    for ident in identities:
        if not ident:
            continue
        if ident in page or page.startswith(ident):
            return True
        # The name often sits at the end: "Support - Radio Tune". The store
        # name is longer ("Radio Tune: Live Radio"), so look for its leading
        # name inside the title too.
        if len(ident) >= 9 and ident[:9] in page:
            return True
        common = 0
        for a, b in zip(ident, page):
            if a != b:
                break
            common += 1
        if common >= 8:
            return True
    return False


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "agl-policy-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001 - network, reported not raised
        return 0, f"__error__ {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apps", nargs="*")
    args = ap.parse_args()

    apps = json.loads((M / "apps.json").read_text())["apps"]
    if args.apps:
        apps = [a for a in apps if a["repo"] in args.apps]

    control_status, control_body = fetch(CONTROL)
    control_len = len(control_body)
    print(f"SPA control: HTTP {control_status}, {control_len} bytes "
          f"({CONTROL})\n")

    jobs = []
    for a in apps:
        repo = a["repo"]
        meta = M / f"store/apps/{repo}.json"
        m = json.loads(meta.read_text()) if meta.exists() else {}
        slug = m.get("slug", repo.lower())
        # Match the page against every name this app is known by, not just the
        # slug. Uscis-Case ships as "Case Tracker for USCIS" and radiotune as
        # "Radio Tune", so a slug-only comparison called four correct pages
        # wrong.
        en = (m.get("copy") or {}).get("en") or {}
        names = {slug, repo, en.get("name") or "", en.get("title") or ""}
        identities = {_norm(n) for n in names if n}
        needs_delete = bool((a.get("auth") or {}).get("providers"))
        pages = {"privacy": "", "support": "support.html", "terms": "terms.html"}
        if needs_delete:
            pages["delete_account"] = "delete-account.html"
        for kind, leaf in pages.items():
            jobs.append((repo, slug, identities, kind, f"{BASE}/{slug}/{leaf}"))

    results: dict[str, dict] = {}

    def check(job):
        repo, slug, identities, kind, url = job
        status, body = fetch(url)
        if body.startswith("__error__"):
            return repo, kind, {"url": url, "state": "UNREACHABLE",
                                "detail": body[:120]}
        title = (TITLE.search(body).group(1).strip()
                 if TITLE.search(body) else "")
        # The SPA shell is one specific document; matching its length within a
        # small margin is what identifies the fallback.
        is_spa = control_len and abs(len(body) - control_len) < 2048
        if status != 200:
            state = f"HTTP_{status}"
        elif is_spa:
            state = "SPA_FALLBACK"
        elif not _same_app(identities, title):
            # The page is real but belongs to a different app.
            state = "WRONG_PAGE"
        else:
            state = "OK"
        return repo, kind, {"url": url, "state": state, "bytes": len(body),
                            "title": title[:90]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for repo, kind, rec in pool.map(check, jobs):
            results.setdefault(repo, {})[kind] = rec

    bad = 0
    for repo in sorted(results):
        states = {k: v["state"] for k, v in results[repo].items()}
        problems = {k: v for k, v in states.items() if v != "OK"}
        if problems:
            bad += 1
            print(f"{repo:18} {problems}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1) + "\n")
    total = sum(len(v) for v in results.values())
    print(f"\n{total - sum(1 for r in results.values() for x in r.values() if x['state'] != 'OK')}"
          f"/{total} URLs serve the right page; {bad} app(s) with a problem -> {OUT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
