# Per-app vendor trackers — one CSV per app

Each `<App>.csv` lists every vendor that app needs: platforms (App Store
Connect, Google Play, AdMob, Google Sign-In), affiliate programmes and data
APIs, with what is measured about each and the founder's working status.

**You edit:** `signup_status` (Not started · Applied · Approved · Rejected ·
Done · Not needed), `api_access` (e.g. Not requested · Sandbox · Production ·
n/a), `token_vault_ref`, `owner`, `next_action`, `notes`.

**Never put a real key, token or password in any cell.** `token_vault_ref` is
the *name* of where the secret lives — "GitHub secret AMAZON_TAG_BODYQUEST",
"1Password: AGL / Travelpayouts". The importer refuses anything that looks like
a secret, and imports nothing until it is fixed.

**Measured, regenerated every export (don't edit):** `priority`, `kind`,
`money`, `what_it_does`, `signup_url`, `commission`, `credential_names` (the
build-time keys the app's code reads), `token_in_build` (whether each is EMPTY
in the shipped build, hard-coded, or a placeholder), `code_evidence`
(file:line), `registry_status`.

Priority: **P0** platform · **P1** affiliate programme already wired in code,
or a sign-in client id missing — sign up first · **P2** API in code whose key is
empty in the build · **P3** working / no key needed · **P4** proposed, or
removed from code.

```bash
python3 scripts/vendor_registry.py --import-apps   # after editing: pull your edits into the registry
python3 scripts/api_vendor_audit.py && python3 scripts/vendor_registry.py --from-code --export-apps   # refresh
.venv/bin/python3 scripts/vendor_registry.py --workbook   # one sheet per app in the measured workbook
```

When a status reaches Approved/Done the registry marks the pair `signed-up`;
wiring the ID into the build comes next (public IDs as `--dart-define`,
secret keys behind a Supabase Edge Function — never inside the app).
