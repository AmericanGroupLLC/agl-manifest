#!/usr/bin/env python3
"""Make the documented test accounts real, so App Review can get in.

    python3 scripts/supabase_accounts.py --check     # verify only, no writes
    python3 scripts/supabase_accounts.py             # create/confirm/repair

MA-036: the integration guide states three persistent test accounts exist in
the production database. They did not. A sign-in attempt returned

    POST /auth/v1/token?grant_type=password  qa@safecodeg.com  400 Invalid login credentials

and that is a Guideline 2.1 rejection waiting to happen for the five apps that
have a Supabase sign-in and no guest path.

Creating the account is not enough. This project has `mailer_autoconfirm:
False`, so a freshly created user cannot sign in until its email is confirmed,
and confirming it is an admin operation:

    PUT /auth/v1/admin/users/{id}  {"email_confirm": true}

That needs the **service-role** key. The key is not on this machine and must
not be written to it. It is fetched per run from the Supabase CLI, which holds
its own token in the macOS keychain:

    supabase projects api-keys --project-ref <ref> -o json

The CLI can read that keychain item; a plain `security find-generic-password`
from a non-interactive shell returns empty, which is why the key is taken this
way rather than by extracting the token.

The passwords are read out of the integration guide rather than repeated here.
They are already in that file; duplicating them would put the same secret in a
second place for no gain.

Nothing is printed that could authenticate anyone: keys are never echoed, and
passwords are shown only as a length.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agl_paths import MANIFEST as M  # noqa: E402

PROJECT_REF = "smvvjivvlprjhzhoizym"
BASE = f"https://{PROJECT_REF}.supabase.co"
GUIDE = M / "AmericanGroupLLC — Complete Developer Integration Guide.md"

# Matches a credentials row of the guide's table. The real secret is not
# repeated here; the shape is `| **Role** | `addr@host` | `secret` | `uuid` |`.
ROW = re.compile(
    r"\|\s*\*\*(\w+)\*\*\s*\|\s*`([^`]+@[^`]+)`\s*\|\s*`([^`]+)`")


def api(url: str, token: str, apikey: str, method: str = "GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", apikey)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"{}")
        except ValueError:
            return e.code, {"raw": raw.decode(errors="ignore")[:200]}


def keys() -> tuple[str, str]:
    """(anon, service_role), straight from the CLI. Never cached to disk."""
    r = subprocess.run(
        ["supabase", "projects", "api-keys", "--project-ref", PROJECT_REF,
         "-o", "json"],
        capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise SystemExit(
            "  supabase CLI could not read the project keys. Run "
            "`supabase login` first.\n  " + (r.stderr or "").strip()[:300])
    # The CLI prints a JSON object with a `keys` list, or a bare list.
    payload = json.loads(r.stdout)
    rows = payload.get("keys", payload) if isinstance(payload, dict) else payload
    by_id = {k.get("id") or k.get("name"): k.get("api_key") for k in rows}
    anon = by_id.get("anon")
    svc = by_id.get("service_role")
    if not anon or not svc:
        raise SystemExit(f"  expected anon + service_role, got {sorted(by_id)}")
    return anon, svc


def accounts() -> list[tuple[str, str, str]]:
    """(role, email, password) from the integration guide."""
    if not GUIDE.exists():
        raise SystemExit(f"  guide not found: {GUIDE}")
    out = []
    for role, email, pw in ROW.findall(GUIDE.read_text(errors="ignore")):
        if "@" in email and (role, email, pw) not in out:
            out.append((role, email, pw))
    return out


def signin(email: str, pw: str, anon: str) -> tuple[bool, str]:
    code, body = api(f"{BASE}/auth/v1/token?grant_type=password", anon, anon,
                     "POST", {"email": email, "password": pw})
    if code == 200 and body.get("access_token"):
        return True, "signs in"
    return False, f"{code} {body.get('msg') or body.get('error_description') or ''}".strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify sign-in only; make no changes")
    ap.add_argument("--audit-config", action="store_true",
                    help="report the production auth URLs and providers, and "
                         "fail if any redirect points at a local address")
    ap.add_argument("--wire-store", action="store_true",
                    help="record the QA account on every app that signs in, "
                         "so asc_readiness.rb hands it to App Review")
    args = ap.parse_args()

    if args.audit_config:
        return audit_config()

    want = accounts()
    if not want:
        raise SystemExit("  no test accounts found in the guide")
    print(f"  {len(want)} documented account(s) in {GUIDE.name}")

    anon, svc = keys()
    print("  service-role key obtained from the CLI (not stored)")

    # One listing, rather than a lookup per account.
    code, body = api(f"{BASE}/auth/v1/admin/users?per_page=200", svc, svc)
    if code != 200:
        raise SystemExit(f"  admin list failed: {code} {body}")
    existing = {u["email"].lower(): u for u in (body.get("users") or [])
                if u.get("email")}
    print(f"  {len(existing)} user(s) already in the project")

    ok = 0
    for role, email, pw in want:
        good, why = signin(email, pw, anon)
        if good:
            print(f"  {role:10} {email:22} already {why}")
            ok += 1
            continue
        if args.check:
            print(f"  {role:10} {email:22} CANNOT SIGN IN — {why}")
            continue

        u = existing.get(email.lower())
        if u is None:
            code, body = api(f"{BASE}/auth/v1/admin/users", svc, svc, "POST",
                             {"email": email, "password": pw,
                              "email_confirm": True})
            if code not in (200, 201):
                print(f"  {role:10} {email:22} create failed: {code} "
                      f"{body.get('msg') or body}")
                continue
            action = "created + confirmed"
        else:
            # Exists but cannot sign in: confirm the address and reset the
            # password to the documented one in a single PUT.
            code, body = api(f"{BASE}/auth/v1/admin/users/{u['id']}", svc, svc,
                             "PUT", {"email_confirm": True, "password": pw})
            if code != 200:
                print(f"  {role:10} {email:22} repair failed: {code} "
                      f"{body.get('msg') or body}")
                continue
            action = "confirmed + password reset"

        good, why = signin(email, pw, anon)
        print(f"  {role:10} {email:22} {action} -> "
              f"{'SIGNS IN' if good else 'STILL FAILING: ' + why} "
              f"(password {len(pw)} chars)")
        ok += good

    print(f"\n  {ok}/{len(want)} documented account(s) can sign in")

    if args.wire_store and not args.check:
        qa = next((e for r, e, _ in want if r.lower() == "qa"), None)
        if qa and signin(qa, dict((e, p) for _, e, p in want)[qa], anon)[0]:
            ok_n = wire_store(qa)
            print(f"  recorded {qa} on {ok_n} app(s) with a sign-in screen")
        else:
            print("  not wiring the store records: the QA account does not "
                  "sign in, and advertising it to Apple would be worse than "
                  "leaving the gap visible")

    if ok == len(want):
        print("  MA-036 symptom 1 is cleared: App Review has working "
              "credentials for the sign-in apps.")
    return 0 if ok == len(want) else 1


LOCAL = ("localhost", "127.0.0.1", "0.0.0.0", "10.0.2.2", "192.168.")


def audit_config() -> int:
    """Prove where production auth emails send people, without sending any.

    The project's `site_url` is not readable with the service-role key, and
    the Management API that does read it needs a personal access token this
    machine does not expose. But the Auth admin API's generate_link *returns*
    a sign-in link instead of emailing it, and that link carries the default
    redirect — which is the site_url. No email is sent and the token in the
    link is never printed.

    Found 2026-10-08: site_url was http://localhost:3000, so every
    confirmation, magic-link and password-reset email the 16 apps on this
    project send redirected real users to their own machine.
    """
    import urllib.parse as up
    anon, svc = keys()
    code, body = api(f"{BASE}/auth/v1/admin/generate_link", svc, svc, "POST",
                     {"type": "magiclink", "email": accounts()[0][1]})
    link = body.get("action_link") or (body.get("properties") or {}).get("action_link")
    if code != 200 or not link:
        print(f"  generate_link failed: {code} {body.get('msg') or ''}")
        return 1
    redirect = (up.parse_qs(up.urlparse(link).query).get("redirect_to") or [""])[0]
    _c, settings = api(f"{BASE}/auth/v1/settings", anon, anon)
    providers = sorted(k for k, v in (settings.get("external") or {}).items() if v)
    anon_ok, _ = api(f"{BASE}/auth/v1/signup", anon, anon, "POST", {})
    local = any(m in redirect for m in LOCAL)
    print(f"  site_url (default email redirect): {redirect or '<empty>'}"
          f"{'   <-- LOCAL ADDRESS: every auth email lands on localhost' if local else ''}")
    print(f"  providers enabled: {', '.join(providers)}")
    print(f"  email confirmation required: {not settings.get('mailer_autoconfirm')}")
    print(f"  anonymous sign-ins: {'enabled' if anon_ok == 200 else 'disabled'}")
    if local:
        print("  FIX (dashboard, no API path from here): Authentication -> URL "
              "Configuration -> Site URL. See MA-042.")
    return 1 if local else 0


def wire_store(qa_email: str) -> int:
    """Name the QA account on every app that presents a sign-in.

    Only the address is written. The password stays out of store/apps/*.json
    — it is already in the integration guide, and a second copy in 15 more
    committed files is 15 more places to leak it from. asc_readiness.rb
    resolves it at push time from the same guide this script reads.
    """
    manifest = json.loads((M / "apps.json").read_text())["apps"]
    n = 0
    for a in manifest:
        if not (a.get("auth") or {}).get("login_screen"):
            continue
        f = M / "store/apps" / f"{a['repo']}.json"
        if not f.exists():
            continue
        rec = json.loads(f.read_text())
        ri = rec.setdefault("review_information", {})
        if ri.get("demo_account_name") == qa_email and ri.get("demo_account_required"):
            n += 1
            continue
        ri["demo_account_name"] = qa_email
        ri["demo_account_required"] = True
        f.write_text(json.dumps(rec, indent=1) + "\n")
        n += 1
    return n


if __name__ == "__main__":
    raise SystemExit(main())
