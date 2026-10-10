#!/usr/bin/env python3
"""Prove every host each app calls actually exists.

    python3 scripts/verify_api_hosts.py            # -> docs/api-hosts.json
    python3 scripts/verify_api_hosts.py --print

Twenty of the 288 hosts the apps call did not resolve when this was first
run, and seven of those were *our own* backends that were never deployed:

    api.americangroupllc.com         7 apps, including GroceryMatch's sign-in
    api.americangroup.ai                CalcMaster's AI chat, profile, analytics
    api.verba.americangroupllc.com   api.myhealth.app   photriya.cloud
    grocerymatch.app                 uscis-case94.manus.app

The org has no API server. Every app talks to Supabase directly (project
`smvvjivvlprjhzhoizym`), so a first-party API hostname in an app is a
placeholder that shipped — and a sign-in that posts to a name with no DNS
record is a Guideline 2.1 rejection that analyze, tests and the simulator all
pass straight through, because none of them leave the laptop.

Resolution uses Google's DNS-over-HTTPS rather than the system resolver: this
machine reaches the internet through a proxy and plain DNS is blocked, so
`dig` times out on every name and proves nothing. NXDOMAIN from DoH is a
definitive answer; anything else short of an address is recorded as
`unverified`, not as dead, because the proxy filters some hosts.

Only *code* lines count. A host named in a `//` comment or a doc link is
reported separately and does not fail the gate.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import pathlib
import re
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import ROOT, MANIFEST as M  # noqa: E402

OUT = M / "docs/api-hosts.json"
HOST = re.compile(r"https://([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
# Hosts that are hostnames-by-convention rather than endpoints: XML
# namespaces, schema ids. They never resolve and are never fetched.
# Well-known third-party APIs: resolving is enough; their "/" is not ours to judge.
THIRD_PARTY = (".openai.com", ".google.com", ".googleapis.com", ".apple.com", ".supabase.co",
               ".github.com", ".radio-browser.info", ".opensky-network.org", ".finnhub.io",
               ".alphavantage.co", ".nasa.gov", ".openfoodfacts.org", ".spotify.com",
               ".yahoo.com", ".sec.gov", ".nytimes.com", ".npr.org", ".bbci.co.uk")
IGNORE = {"www.w3.org", "schemas.android.com", "xmlns.com", "example.com",
          "www.example.com"}


def doh(host: str) -> str:
    """'ok', 'NXDOMAIN', or 'unverified …' — never a guess."""
    try:
        for rtype in ("A", "AAAA", "CNAME"):
            url = f"https://dns.google/resolve?name={host}&type={rtype}"
            with urllib.request.urlopen(url, timeout=20) as r:
                d = json.load(r)
            if d.get("Status") == 3:
                return "NXDOMAIN"
            if d.get("Answer"):
                return "ok"
        return "unverified: no address record"
    except Exception as e:  # network, proxy, timeout
        return f"unverified: {type(e).__name__}"


PARKING = ("/lander", "parked", "domain is for sale", "buy this domain", "afternic",
           "sedoparking", "parkingcrew", "bodis.com", "hugedomains")


def http_probe(host: str) -> str:
    """'ok', 'PARKED', or 'unverified: no HTTP response' for a host that resolves.

    DNS answering proves nothing about who is there. api.codedeal.com
    resolves — to the AWS Global Accelerator pair parked domains sit on — and
    answers no HTTP at all, while codedeal.com serves a 114-byte page whose
    only content is a redirect to a parking "lander". CodeDeal's whole tRPC
    backend pointed at it. A parked domain is worse than a dead one: whoever
    buys it receives the app's requests, sign-in tokens included.
    """
    import subprocess as sp
    out = sp.run(["curl", "-s", "-m", "15", "-L", "-o", "-", "-w", "\n%{http_code}",
                  f"https://{host}/"], capture_output=True, text=True)
    body, _, code = out.stdout.rpartition("\n")
    # A parking page can sit on the apex while the api subdomain is silent,
    # so check the registrable domain too.
    apex = ".".join(host.split(".")[-2:])
    if apex != host:
        a = sp.run(["curl", "-s", "-m", "15", "-L", "-o", "-", f"https://{apex}/"],
                   capture_output=True, text=True).stdout
        if len(a) < 4000 and any(m in a.lower() for m in PARKING):
            return "PARKED"
    if len(body) < 4000 and any(m in body.lower() for m in PARKING):
        return "PARKED"
    if code.strip() in ("", "000"):
        return "unverified: no HTTP response"
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()

    apps = json.loads((M / "apps.json").read_text())["apps"]
    sites: dict[str, dict[str, list[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    comments: dict[str, set[str]] = collections.defaultdict(set)
    for a in apps:
        repo = a["repo"]
        d = ROOT / repo / (a.get("dir") or ".")
        for f in sorted((d / "lib").rglob("*.dart")):
            if "/generated/" in str(f):
                continue
            for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                s = line.strip()
                for h in HOST.findall(line):
                    if h in IGNORE:
                        continue
                    if s.startswith(("//", "*", "///", "/*")):
                        comments[repo].add(h)
                    else:
                        sites[repo][h].append(f"{f.relative_to(d)}:{n}")

    hosts = sorted({h for r in sites.values() for h in r})
    with cf.ThreadPoolExecutor(16) as ex:
        status = dict(zip(hosts, ex.map(doh, hosts)))
        # Only our own-looking API hosts get the HTTP probe: third-party APIs
        # often answer nothing at "/" and are not ours to judge.
        ours = [h for h in hosts if status[h] == "ok" and h.split(".")[0] in ("api", "gateway", "backend")
                and not any(h.endswith(t) for t in THIRD_PARTY)]
        for h, st in zip(ours, ex.map(http_probe, ours)):
            if st != "ok":
                status[h] = st

    report = {}
    for a in apps:
        repo = a["repo"]
        calls = sites.get(repo, {})
        dead = {h: v for h, v in calls.items() if status[h] in ("NXDOMAIN", "PARKED")}
        unv = {h: v for h, v in calls.items() if status[h].startswith("unverified")}
        report[repo] = {
            "hosts": len(calls),
            "dead": dead,
            "unverified": {h: {"why": status[h], "sites": v} for h, v in unv.items()},
            "comment_only": sorted(comments.get(repo, set()) - set(calls)),
        }
    OUT.write_text(json.dumps({"hosts": status, "apps": report}, indent=1) + "\n")

    n_dead = sum(1 for s in status.values() if s in ("NXDOMAIN", "PARKED"))
    n_unv = sum(1 for s in status.values() if s.startswith("unverified"))
    bad = [r for r, v in report.items() if v["dead"]]
    print(f"  {len(hosts)} hosts called from code: {len(hosts) - n_dead - n_unv} "
          f"resolve, {n_dead} dead (NXDOMAIN or parked), {n_unv} unverified")
    print(f"  apps calling a host that does not exist: {len(bad)}")
    if args.print:
        for r in bad:
            for h, v in report[r]["dead"].items():
                print(f"   {r:16} {h:40} {v[0]}" + (f" (+{len(v)-1})" if len(v) > 1 else ""))
    print(f"  -> {OUT.relative_to(M)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
