#!/usr/bin/env python3
"""GET each URL and record what really answers. Read-only.

    python3 scripts/probe_urls.py URL [URL ...]
    python3 scripts/probe_urls.py --head URL      # status + headers only
    python3 scripts/probe_urls.py --find 'AIRPORT DIAGRAM' URL   # count + snippets

For deciding whether a data source an app is about to depend on exists and
returns what the code expects: HTTP status, final URL after redirects,
content type, size and the first bytes of the body. `verify_api_hosts.py`
answers "does the host resolve"; this answers "does this endpoint return
JSON/PDF/XML or an HTML shell". www.aviationapi.com/v1/... answers 200 with
the site's HTML, which is exactly what a resolve-only check cannot see.

Uses curl because this machine reaches the internet through a proxy that the
shell honours. Writes <DIST>/url-probe.json; nothing in docs/ changes.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess as sp
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import DIST  # noqa: E402

OUT = DIST / "url-probe.json"
SAMPLE = 600


def probe(url: str, head: bool, find: list[str]) -> dict:
    fmt = "\n%{http_code} %{size_download} %{url_effective} %{content_type}"
    cmd = ["curl", "-s", "-L", "-m", "40", "-A", "agl-probe/1.0"]
    if head:
        cmd += ["-I"]
    out = sp.run(cmd + ["-o", "-", "-w", fmt, url], capture_output=True)
    raw = out.stdout
    body, _, tail = raw.rpartition(b"\n")
    parts = tail.decode(errors="replace").split(" ", 3) + ["", "", "", ""]
    text = body.decode(errors="replace")
    found = {}
    for pat in find:
        hits = [m.start() for m in re.finditer(pat, text)]
        found[pat] = {"count": len(hits),
                      "snippets": [text[max(0, i - 80):i + 160] for i in hits[:3]]}
    return {
        "url": url,
        "http": parts[0],
        "bytes": parts[1],
        "final_url": parts[2],
        "content_type": parts[3].strip(),
        "curl_exit": out.returncode,
        "sample": body[:SAMPLE].decode(errors="replace"),
        "found": found,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--head", action="store_true")
    ap.add_argument("--find", action="append", default=[],
                    help="regex to count in the body; repeatable")
    args = ap.parse_args()

    results = [probe(u, args.head, args.find) for u in args.urls]
    for r in results:
        print(f"{r['http']:>3} {r['bytes']:>9}B {r['content_type'] or '-':30} {r['url']}")
        if r["final_url"] and r["final_url"] != r["url"]:
            print(f"      -> {r['final_url']}")
        if r["found"]:
            for pat, f in r["found"].items():
                print(f"      find {pat!r}: {f['count']}")
                for snip in f["snippets"]:
                    print("        | " + " ".join(snip.split()))
        else:
            print("      " + r["sample"][:SAMPLE].replace("\n", "\n      "))
    DIST.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1) + "\n")
    print(f"  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
