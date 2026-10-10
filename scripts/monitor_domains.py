#!/usr/bin/env python3
"""Watch everything that lives on americangroup.ai, and the old domain that redirects to it.

    python3 scripts/monitor_domains.py            # -> docs/domain-health.json, exit 1 on any FAIL
    python3 scripts/monitor_domains.py --markdown # also print a Markdown table (for the CI issue)

Run every 30 minutes by .github/workflows/domain-monitor.yml, which opens a
GitHub issue when something fails and closes it when everything is green.

What is checked, and why each is here:
  website      www.americangroup.ai serves the site; every other host 301s to it
               (the URLs printed in 43 store listings depend on those redirects)
  policy       a privacy, support and account-deletion page per run — store
               reviewers open these; scripts/verify_policy_urls.py does all 147
  ads          app-ads.txt carries the AdMob publisher line (AdMob verifies it)
  cpanel       webmail, cPanel, webdisk, calendars/contacts, autodiscover answer
  mail         SMTP/IMAP/POP ports accept TLS for sales@, support@, contact@;
               MX, SPF, DKIM and DMARC records exist
  tls          certificate days left on every HTTPS host and mail port (< 14 = FAIL)
  backend      the Supabase project the apps call is healthy

A port this machine cannot reach (outbound blocked, as on the dev laptop
behind its proxy) is reported SKIP, never PASS.
"""

from __future__ import annotations

import datetime as dt
import errno
import json
import pathlib
import socket
import ssl
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M  # noqa: E402

OUT = M / "docs/domain-health.json"
D = "americangroup.ai"
WWW = f"https://www.{D}"
PUB = "pub-8528784688453695"
SUPABASE = "https://smvvjivvlprjhzhoizym.supabase.co/auth/v1/health"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def http(url: str, follow=False, timeout=20):
    """(status, location, body[:200k]) — never raises."""
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "agl-domain-monitor/1.0"})
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.headers.get("Location", ""), r.read(200_000).decode(errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", ""), (e.read(20_000) or b"").decode(errors="ignore")
    except Exception as e:  # DNS, TLS, timeout
        return 0, "", f"{type(e).__name__}: {e}"


def tls_days(host: str, port: int = 443, starttls: str | None = None) -> tuple[str, str]:
    """('PASS'|'FAIL'|'SKIP', detail) for the certificate on host:port."""
    ctx = ssl.create_default_context()
    try:
        raw = socket.create_connection((host, port), timeout=15)
    except OSError as e:
        if e.errno in (errno.EPERM, errno.EACCES):
            return "SKIP", f"outbound :{port} blocked here"
        return "FAIL", f"cannot connect :{port} ({e})"
    try:
        with raw:
            if starttls == "smtp":
                raw.recv(1024); raw.sendall(b"EHLO monitor\r\n"); raw.recv(4096)
                raw.sendall(b"STARTTLS\r\n"); raw.recv(1024)
            with ctx.wrap_socket(raw, server_hostname=host) as s:
                exp = dt.datetime.strptime(s.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z")
        left = (exp - dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)).days
        return ("PASS" if left >= 14 else "FAIL"), f"certificate valid {left} more days"
    except Exception as e:
        return "FAIL", f"TLS on :{port} failed ({type(e).__name__}: {str(e)[:80]})"


def dns(name: str, rtype: str) -> list[str]:
    s, _, body = http(f"https://dns.google/resolve?name={name}&type={rtype}", follow=True)
    try:
        return [a["data"] for a in json.loads(body).get("Answer", [])]
    except Exception:
        return []


def main() -> int:
    rows: list[tuple[str, str, str, str]] = []

    def add(group, name, state, detail):
        rows.append((group, name, state, detail))

    # --- website and redirects ------------------------------------------
    s, _, body = http(f"{WWW}/", follow=True)
    add("website", f"{WWW}/", "PASS" if s == 200 and "American Group LLC" in body else "FAIL", f"HTTP {s}")
    for src in (f"https://{D}/", "https://safecodeg.com/", "https://www.safecodeg.com/policy/kinnav/privacy.html"):
        s, loc, _ = http(src)
        ok = s == 301 and loc.startswith(f"{WWW}/")
        add("website", f"{src} -> www", "PASS" if ok else "FAIL", f"HTTP {s} -> {loc or '-'}")

    # --- store-facing pages (one app per kind each run) -------------------
    for path, needle in (("/policy/kinnav/privacy.html", "privacy"),
                         ("/policy/calcmaster/support.html", "support"),
                         ("/policy/virtuband/delete-account.html", "delete")):
        s, _, body = http(WWW + path, follow=True)
        ok = s == 200 and needle in body.lower() and "Enterprise Technology & Mobile Apps" not in body
        add("policy", path, "PASS" if ok else "FAIL", f"HTTP {s}")
    s, _, body = http(f"{WWW}/app-ads.txt", follow=True)
    add("ads", "app-ads.txt", "PASS" if s == 200 and PUB in body else "FAIL", f"HTTP {s}")

    # --- cPanel services (status codes that mean "up") --------------------
    for host, up in (("webmail", {200, 301, 302, 307, 308}), ("cpanel", {200, 301, 302}),
                     ("webdisk", {200, 401}), ("cpcalendars", {200, 401}), ("cpcontacts", {200, 401}),
                     ("autodiscover", {200, 400, 401, 405}), ("autoconfig", {200, 404})):
        s, _, _ = http(f"https://{host}.{D}/")
        add("cpanel", f"{host}.{D}", "PASS" if s in up else "FAIL", f"HTTP {s}")

    # --- mail -------------------------------------------------------------
    for port, starttls, label in ((465, None, "SMTPS"), (587, "smtp", "Submission"),
                                  (993, None, "IMAPS"), (995, None, "POP3S")):
        st, det = tls_days(f"mail.{D}", port, starttls)
        add("mail", f"mail.{D}:{port} {label}", st, det)
    mx = dns(D, "MX")
    add("mail", "MX", "PASS" if any(f"mail.{D}" in m for m in mx) else "FAIL", ", ".join(mx) or "none")
    txt = dns(D, "TXT")
    add("mail", "SPF", "PASS" if any("v=spf1" in t for t in txt) else "FAIL", next((t for t in txt if "spf1" in t), "none")[:80])
    dk = dns(f"default._domainkey.{D}", "TXT")
    add("mail", "DKIM", "PASS" if any("v=DKIM1" in t for t in dk) else "FAIL", "present" if dk else "none")
    dm = dns(f"_dmarc.{D}", "TXT")
    add("mail", "DMARC", "PASS" if any("v=DMARC1" in t for t in dm) else "FAIL", (dm or ["none"])[0][:60])

    # --- certificates on the web hosts ------------------------------------
    for host in (f"www.{D}", D, f"webmail.{D}", f"cpanel.{D}"):
        st, det = tls_days(host)
        add("tls", host, st, det)

    # --- other cPanel ports (TCP only) ------------------------------------
    for host, port, label in ((f"ftp.{D}", 21, "FTP"), (f"ssh.{D}", 22, "SSH"), (f"whm.{D}", 2087, "WHM")):
        try:
            socket.create_connection((host, port), timeout=10).close()
            add("cpanel", f"{label} {host}:{port}", "PASS", "accepts connections")
        except OSError as e:
            blocked = e.errno in (errno.EPERM, errno.EACCES)
            add("cpanel", f"{label} {host}:{port}", "SKIP" if blocked else "FAIL",
                "outbound blocked here" if blocked else str(e)[:80])

    # --- backend ----------------------------------------------------------
    s, _, _ = http(SUPABASE)
    add("backend", "Supabase auth health", "PASS" if s in (200, 401) else "FAIL", f"HTTP {s}")

    fails = [r for r in rows if r[2] == "FAIL"]
    OUT.write_text(json.dumps({"checked_at": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
                               "fail": len(fails), "rows": [dict(zip(("group", "check", "state", "detail"), r))
                                                             for r in rows]}, indent=1) + "\n")
    for g, n, st, det in rows:
        print(f"  {st:4} {g:8} {n:52} {det}")
    print(f"\n  {len(rows)} checks: {sum(r[2] == 'PASS' for r in rows)} pass, {len(fails)} fail, "
          f"{sum(r[2] == 'SKIP' for r in rows)} skipped -> {OUT.relative_to(M)}")
    if "--markdown" in sys.argv:
        md = ["| State | Group | Check | Detail |", "| --- | --- | --- | --- |"]
        md += [f"| {st} | {g} | {n} | {det} |" for g, n, st, det in rows if st != "PASS"] or ["| PASS | all | everything | — |"]
        (M / "domain-health.md").write_text("\n".join(md) + "\n")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
