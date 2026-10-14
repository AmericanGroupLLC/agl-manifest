#!/usr/bin/env python3
"""End-to-end test of the deployed `uscis-case-status` Edge Function against the USCIS sandbox.

    python3 scripts/uscis_sandbox_test.py

Signs in as the QA test account (credentials read by supabase_accounts.py from
the integration guide — never printed), then calls the function with USCIS's
published sandbox receipts and one malformed receipt:

    EAC9999103403  expect 200 with history
    EAC9999103400  expect 200 without history
    EAC123         expect 422, USCIS not called
    EAC9999103403  again: "cached": true only with USCIS_STORE=db (the
                   in-memory store lasts one function instance)

Prints status codes and the normalised fields only — no token, no password.
The USCIS sandbox answers Monday–Friday 7 AM–8 PM US Eastern; outside those
hours a 503 is expected and is not a function failure. Each run uses 2–3 of
the sandbox's 1,000 daily calls and counts toward the 5 consecutive days of
traffic USCIS asks for before production access.
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import supabase_accounts as sa  # noqa: E402

FN = f"{sa.BASE}/functions/v1/uscis-case-status"


def call(receipt: str, jwt: str, anon: str) -> tuple[int, dict]:
    req = urllib.request.Request(FN, data=json.dumps({"receipt": receipt}).encode(), method="POST", headers={
        "Authorization": f"Bearer {jwt}", "apikey": anon, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or "{}")
        except ValueError:
            return e.code, {}


def main() -> int:
    anon, _svc = sa.keys()
    qa = next((a for a in sa.accounts() if a[0].lower().startswith("qa") or a[1].startswith("qa@")), None)
    if not qa:
        print("no QA account in the integration guide")
        return 1
    _role, email, pw = qa
    code, body = sa.api(f"{sa.BASE}/auth/v1/token?grant_type=password", anon, anon, "POST",
                        {"email": email, "password": pw})
    jwt = (body or {}).get("access_token") if code == 200 else None
    print(f"  sign-in {email}: HTTP {code}")
    if not jwt:
        return 1
    ok = True
    for receipt, want in [("EAC9999103403", 200), ("EAC9999103400", 200), ("EAC123", 422), ("EAC9999103403", 200)]:
        code, b = call(receipt, jwt, anon)
        snap = b.get("snapshot") or {}
        shown = {k: snap.get(k) for k in ("form_type", "status_title", "last_updated") if k in snap}
        shown.update({k: b[k] for k in ("cached", "error") if k in b})
        if "history" in snap:
            shown["history_items"] = len(snap.get("history") or [])
        if snap and not shown.keys() & {"form_type", "status_title"}:
            shown["snapshot_keys"] = sorted(snap)
        print(f"  {receipt:14} HTTP {code} (want {want})  {json.dumps(shown)[:300]}")
        ok &= code == want
    print("PASS" if ok else "NOT ALL AS EXPECTED")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
