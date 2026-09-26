# Documentation

Everything about the 42 mobile apps now lives here rather than in the private
backend repository, so working on delivery needs access to one repo.

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

## Not here, deliberately

No credential is in this repository, and none should be.

| | Where it lives |
| --- | --- |
| `AuthKey_UV8NYF9767.p8` | untracked on the build machine; loaded into `ASC_KEY_CONTENT` |
| Upload keystores (30) | `~/agl/.secrets/`; loaded into `KEYSTORE_<APP>_BASE64` |
| Keystore passwords | `~/agl/.secrets/keystores.json`; loaded into `ANDROID_KEYSTORE_CONFIG` |
| The planning workbook | the build machine only — it carries live credentials |

GitHub secrets are the destination for all of these. A repository is not.
