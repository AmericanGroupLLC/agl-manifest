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

## The sign-up worklist — `store/vendors/signups.csv`

One row per vendor (100 today): every vendor in the founder's directory
(`store/vendors/directory.csv`) plus the ones the code needs that it does not
list. `needed_by_apps` comes from the code; `suits_apps` is only a suggestion.
Fill `signup_status`, `account_owner`, `applied_on`, `approved_on`,
`id_or_vault_ref`, `notes` — they survive every regeneration
(`python3 scripts/vendor_registry.py --from-code --export-signups`). The export
refuses to run while any of those cells looks like a real secret.

## The one file to use — `store/vendors/AGL_Vendor_Signup_Playbook.xlsx` (in this repo)

Founder decision 2026-10-13: a single tracker. Edit status, owner, dates,
vault references and notes directly in the workbook. A refresh
(`.venv/bin/python3 scripts/signup_playbook.py`) keeps those columns, refuses to
run while the workbook is open in Excel, and backs the old copy up to
`~/agl/.dist/backups/`. The CSVs in this folder are inputs and history
snapshots — nobody needs to open them. Before committing your edits: `.venv/bin/python3 scripts/signup_playbook.py --check` (refuses anything that looks like a key).
