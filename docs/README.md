# Documentation

Everything about the 43 mobile apps now lives here rather than in the private
backend repository, so working on delivery needs access to one repo.

Control-plane data layers:

- `../manifest/` = desired state
- `../generated/` = measured state (reserved)
- `../apps.json` = measured compatibility manifest currently used by CI

| Start here | |
| --- | --- |
| [DELIVERY_ARCHITECTURE.md](DELIVERY_ARCHITECTURE.md) | who owns what, what runs where, where the CI minutes go |
| `status.csv` | the full release runbook, prioritised issues, per-platform steps |
| [FIREBASE_REGISTRATION.md](FIREBASE_REGISTRATION.md) | one-pass console list: every package name and where each config file goes |
| [RELEASE_PIPELINE.md](RELEASE_PIPELINE.md) | the delivery path and the store accounts behind it |

| Reference | |
| --- | --- |
| [app-identifiers.json](app-identifiers.json) | bundle ids and package names — also carried per app in [`status.csv`](../status.csv) |
| [admob-ids.json](admob-ids.json) | the AdMob console record |
| [CRASHLYTICS.md](CRASHLYTICS.md) | how crash reporting is wired, and why it is guarded |
| [I18N.md](I18N.md) | the twelve languages, the rollout state, and the traps |
| [STORE_METADATA.md](STORE_METADATA.md) | how listing copy is held and rendered |
| `status.csv` · [PUBLIC_API_ACCOUNTS.md](PUBLIC_API_ACCOUNTS.md) | what exists, what you must create |
| [release-readiness.json](release-readiness.json) | the measured per-app audit — the `measured: *` columns of [`status.csv`](../status.csv) |
| [quality-audit.json](quality-audit.json) | product-quality scorecard — the `quality: *` columns of [`status.csv`](../status.csv). Generated; re-run `scripts/audit_product_quality.py` |

| Everything else | |
| --- | --- |
| [MANUAL_ACTIONS.md](MANUAL_ACTIONS.md) | the only list that matters day to day: what a person must do, verified as still outstanding |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | what is broken right now |
| [DECISIONS.md](DECISIONS.md) | why it is built this way |
| [API_ACTIONS.md](API_ACTIONS.md) | every script that talks to an external API, and what each API refuses |
| [asc-build-state.json](asc-build-state.json) | what Apple holds per app — build and review state. The `apple: *` columns of [`status.csv`](../status.csv) |
| [store-checklist-detail.json](store-checklist-detail.json) | every per-app check with its detail string. The `check: *` columns carry the state |
| [deletion-urls.json](deletion-urls.json) | the account-deletion URL per app, each verified against a control path |
| [DATA_SAFETY_DELETION_URLS.md](DATA_SAFETY_DELETION_URLS.md) | how to paste those into Play, and the slug trap |
| [ASC_NEW_APP_RECORDS.md](ASC_NEW_APP_RECORDS.md) · [APPS_TO_CREATE.md](APPS_TO_CREATE.md) | the store records a person still has to create |
| [ADMOB_GAP.md](ADMOB_GAP.md) | why the ad units are still Google's test ids |
| [FIELD_COVERAGE.md](FIELD_COVERAGE.md) | which store fields are answered, and which are not |
| [BRANCH_CONSOLIDATION.md](BRANCH_CONSOLIDATION.md) | one branch per repo, and the three deliberate exceptions |
| [SECRET_SWEEP.md](SECRET_SWEEP.md) | what leaked, what was rotated, what is still fetchable |

This table is meant to list every file in `docs/`. If you add one, add it here —
twelve were missing when this was last checked, which makes the index worse than
no index, because it reads as complete.

## Not here, deliberately

No credential is in this repository, and none should be.

| | Where it lives |
| --- | --- |
| `AuthKey_UV8NYF9767.p8` | untracked on the build machine; loaded into `ASC_KEY_CONTENT` |
| Upload keystores (43) | `~/agl/.secrets/`; loaded into `KEYSTORE_<APP>_BASE64` |
| Keystore passwords | `~/agl/.secrets/keystores.json`; loaded into `ANDROID_KEYSTORE_CONFIG` |
| The planning workbook | the build machine only — it carries live credentials |

GitHub secrets are the destination for all of these. A repository is not.
