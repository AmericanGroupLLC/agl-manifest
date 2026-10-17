# PilotEnRoute: spec SHOULD items, verify script and CI (2026-10-17)

Chain: founder request → software-developer (main session) → qa-reviewer
(independent agent; 10 findings, all addressed) → this report.

## Shipped (PilotEnRoute master)
| Commit | What |
|---|---|
| d076a5d | S1 61.109(a) student progress · S2 on-device night window · S3 Paste CSV (own export only) · Kit "About" sheets · `tools/verify.sh` · `.github/workflows/ci.yml` · `tools/ci_status.sh` · docs |
| 99db6bc | `ci_status.sh` prints only the failing step's messages |

Not built: S4 (Supabase backup; needs a migration, accounts and MA-044). See
decision-log 2026-10-17 entries.

## Evidence (run on this Mac)
- `flutter analyze`: "No issues found!"
- `flutter test`: "+819: All tests passed!" (baseline today 768, 0 skipped).
- `tools/verify.sh`: all 9 steps PASS. iOS: iPhone 18 Pro Max, iOS 27.0
  (24A434). Android: Pixel 8 API 34 emulator. The emulator has no internet
  here, so its on-device run skips only the live-weather step
  (`VERIFY_OFFLINE`). The night window was checked on iOS against live KPAO.
- Solar times: within 2 min of US Naval Observatory at KPAO, KACK and YSSY.
  Above 66° no window is shown, because the series drifts there (24 min at 78°N).
- 61.109(a) text: matches the eCFR 2026-10-01 version word for word.
- One existing test changed: `logbook_depth_test.dart` CSV precision (export
  rounding lost data on round trip). It is named in the commit message.

## QA findings and outcome
| # | Finding | Outcome |
|---|---|---|
| 1 | identical flights collapsed on import | fixed: matched per existing copy |
| 2 | export rounding lost precision / rejected rows | fixed: exact export |
| 3 | short rows imported as zeros | fixed: field-count check |
| 4 | inverted night window near polar day | fixed: <2 h / no sunrise / >66° say so |
| 5 | early-morning departure showed the next night | fixed: previous evening's window |
| 6 | 20 h / 10 h counted non-airplane time | fixed: ASEL/ASES only |
| 7 | split entries' night landings not reported | fixed |
| 8 | double import during an import; silent insert failure | fixed: busy guard + error snackbar |
| 9 | error line numbers were record numbers | fixed: physical lines |
| 10 | dead ProviderNotFoundException catch | removed |

## CI
GitHub Actions is re-enabled on PilotEnRoute (public repo, so minutes are
not billed). Run 39024328662 (workflow_dispatch, d076a5d) stopped as designed
at its first step: "AGL_PACKAGES_TOKEN is not set". It needs one founder step:

1. Open https://github.com/organizations/AmericanGroupLLC/settings/secrets/actions
2. If `AGL_PACKAGES_TOKEN` is listed, open it → Repository access → add
   `PilotEnRoute` → Save.
3. If it is not listed, create a fine-grained token with Contents: Read on
   `AmericanGroupLLC-Backend`, then run
   `gh secret set AGL_PACKAGES_TOKEN -R AmericanGroupLLC/PilotEnRoute`
   and paste the token when prompted.
4. Check: `gh workflow run ci.yml -R AmericanGroupLLC/PilotEnRoute`, then
   `tools/ci_status.sh --watch`. Success is three PASS jobs.

## Also today
- The office daily pass ran. The stand-up commit 1bf6efc is local only: the
  push fails on the existing `docs/store-checklist.json` conflict (#61). This
  report and the decision-log entries are uncommitted for the same reason.
- The `claude -p` step of `office_run.sh` cannot run from an interactive
  sandboxed session (`sandbox-exec: Operation not permitted`, exit 71). The
  chief-of-staff ran it as an agent instead (#61 and #60 commented).

## Conflicts with existing agl-manifest rules (for the office to settle)
- `agl-manifest/CLAUDE.md` says "Only agl-manifest runs CI. Per-repo Actions
  are deliberately disabled", and `docs/DELIVERY_ARCHITECTURE.md` explains why
  (cost). PilotEnRoute now has its own CI. The reason it does (public repo, so
  no billed minutes; founder request) is in the decision log, but those two
  docs have not been updated. They wait for #61.
- `scripts/sim_install.py` already builds, installs and launches apps on the
  simulators. `tools/verify.sh` repeats that for one app and adds analyze,
  tests and on-device integration tests, and it runs in CI. The rule "extend
  the existing script rather than adding a second" argues for folding the
  integration-test steps into sim_install.py (or calling verify.sh from it).
- `tools/ci_status.sh` calls the GitHub API from an app repo. The rule says
  external-API actions belong in `agl-manifest/scripts/`.

## Not verified
- The CI Android and iOS jobs have not run on GitHub yet (blocked on the secret).
- The on-device night window on Android (no emulator internet here).
- Release-signed Android/iOS builds of this commit. Delivery is ship.yml's
  job, under the 2026-10-15 submission hold.
