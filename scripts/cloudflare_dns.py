#!/usr/bin/env python3
"""Keep the americangroup.ai Cloudflare zone safe for the website AND the mail on it.

    python3 scripts/cloudflare_dns.py            # report only
    python3 scripts/cloudflare_dns.py --apply    # fix what the report finds

Token: ~/agl/.secrets/cloudflare-token (or CLOUDFLARE_API_TOKEN), scoped to
the americangroup.ai zone (DNS edit; Zone Settings edit for the SSL part).

Cloudflare imported the HostGator records on 2026-10-09 and set every A and
CNAME to "proxied". Its proxy carries HTTP(S) only, so once the nameservers
moved, mail (SMTP/IMAP/POP for sales@, support@, contact@), FTP, SSH and the
cPanel/WHM/webmail ports would all have stopped answering, and the backup MX
pointed at the proxied apex. The rule this enforces:

  proxied   americangroup.ai, www.americangroup.ai          (the website)
  DNS-only  every other A/CNAME (mail, imap, pop, smtp, ftp, ssh, cpanel, whm,
            webmail, webdisk, cpcalendars, cpcontacts, autodiscover, ...)
  MX        must point at a DNS-only name (mail.americangroup.ai)
  SSL       Full (strict) — HostGator serves a valid certificate; "Flexible"
            would loop with the site's own HTTPS rule. Always Use HTTPS on.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.request

ZONE_NAME = "americangroup.ai"
WEB = {"americangroup.ai", "www.americangroup.ai"}
MAIL_HOST = "mail.americangroup.ai"
API = "https://api.cloudflare.com/client/v4"


def token() -> str:
    t = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not t:
        p = pathlib.Path.home() / "agl/.secrets/cloudflare-token"
        t = p.read_text().strip() if p.exists() else ""
    if not t:
        sys.exit("no Cloudflare token (~/agl/.secrets/cloudflare-token or CLOUDFLARE_API_TOKEN)")
    return t


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(f"{API}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token()}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}") | {"success": False, "http": e.code}


def main() -> int:
    apply = "--apply" in sys.argv
    zones = call("GET", f"/zones?name={ZONE_NAME}").get("result") or []
    if not zones:
        sys.exit(f"zone {ZONE_NAME} not visible to this token")
    z = zones[0]
    print(f"  zone {z['name']} status={z['status']} nameservers={z.get('name_servers')}")
    recs = call("GET", f"/zones/{z['id']}/dns_records?per_page=500").get("result") or []
    names = {r["name"]: r for r in recs}
    todo = []
    for r in recs:
        if r["type"] in ("A", "AAAA", "CNAME"):
            want = r["name"] in WEB
            if bool(r.get("proxied")) != want:
                todo.append((r, {"proxied": want}, f"{r['type']} {r['name']}: proxied -> {want}"))
        if r["type"] == "MX":
            tgt = names.get(r["content"])
            if r["content"] != MAIL_HOST and (tgt is None or tgt.get("proxied") or r["content"] in WEB):
                todo.append((r, {"content": MAIL_HOST},
                             f"MX {r['name']} -> {r['content']} (prio {r.get('priority')}): content -> {MAIL_HOST}"))
    for r, change, why in todo:
        if apply:
            body = {k: r[k] for k in ("type", "name", "content", "ttl") if k in r} | change
            if r["type"] == "MX":
                body["priority"] = r.get("priority", 10)
            res = call("PUT", f"/zones/{z['id']}/dns_records/{r['id']}", body)
            print(f"  {'ok ' if res.get('success') else 'ERR'} {why}"
                  + ("" if res.get("success") else f"  {res.get('errors')}"))
        else:
            print(f"  would {why}")
    settings = {"ssl": "strict", "always_use_https": "on"}
    for k, v in settings.items():
        cur = call("GET", f"/zones/{z['id']}/settings/{k}")
        now = (cur.get("result") or {}).get("value")
        if now == v:
            print(f"  {k} = {v} (ok)")
        elif apply:
            res = call("PATCH", f"/zones/{z['id']}/settings/{k}", {"value": v})
            print(f"  {'ok ' if res.get('success') else 'ERR'} {k}: {now} -> {v}"
                  + ("" if res.get("success") else f"  {res.get('errors')}"))
        else:
            print(f"  would set {k}: {now} -> {v}")
    if not todo:
        print("  records: website proxied, everything else DNS-only, MX on DNS-only names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
