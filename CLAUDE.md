# CLAUDE.md — American Group LLC mobile ecosystem

Entry point for an agent session. This file is an **index, not a description**:
it says where the answer lives so a session does not have to rediscover the
organisation. Read this, read what it points you at, and nothing else.

## What this is

| | |
| --- | --- |
| Org | `AmericanGroupLLC` (43 mobile apps, 1 backend, 1 website) |
| Control plane | this repo, `agl-manifest` |
| Backend | `AmericanGroupLLC-Backend` |
| Website | `https://www.americangroup.ai` |
| Stack | Flutter / Dart, targeting iOS and Android |
| Local mirror | `/Users/spatchava/agl/<repo>` — all org repos are cloned here |

Only `agl-manifest` runs CI. Per-repo Actions are deliberately disabled so the
org is not paying 37× for the same validation; see `docs/DELIVERY_ARCHITECTURE.md`.

## Where to look

| Question | File |
| --- | --- |
| **How do I do anything that calls an API?** | **`docs/API_ACTIONS.md`** — every script, and what the APIs refuse |
| What is the state of every app? | **`status.csv`** — the single sheet: one row per app, and column groups `check:`, `measured:`, `gate:`, `quality:`, `i18n:`, `apple:` alongside the store fields. Counts go stale, so it does not quote one. Every identifier, artefact, store state, store gate, measured fact, quality signal and per-app check. `STATUS.md` is a rendering of it |
| Which apps have a signed binary, and is it really signed? | `docs/build-evidence.json` (generated) |
| **What must pass before an app is submitted?** | **`docs/SUBMISSION_CHECKLIST.md`** — the gate, and why each row exists |
| **Can this build go to TestFlight?** | **`python3 scripts/predelivery.py <App>`** → `docs/predelivery/<App>.md`: 46 checks, 5 gates, release record. The upload gate refuses any IPA without a PASS for that exact file |
| **Will Apple or Google reject it? (every store rule, per app)** | **`python3 scripts/store_policy_audit.py [App …]`** → `docs/store-policy/<App>.md` and `docs/STORE_POLICY.md`: each catalogue rule (`store/policy/catalogue.json`) with applies?, PASS/FAIL/HUMAN/FOUNDER/n-a, evidence and owner. predelivery check 2.8 refuses delivery on any FAIL |
| **A rejection or upload warning arrived** | **`docs/REJECTION_PLAYBOOK.md`** — capture, make it a check, sweep all 43, fix, rebuild |
| What must a human do that I cannot? | `docs/MANUAL_ACTIONS.md` |
| What is broken right now? | `docs/KNOWN_ISSUES.md` |
| Why is it built this way? | `docs/DECISIONS.md` |
| How does delivery work? | `docs/DELIVERY_ARCHITECTURE.md`, `docs/RELEASE_PIPELINE.md` |
| Package names, bundle ids, AdMob ids | `status.csv`, `docs/app-identifiers.json`, `docs/admob-ids.json` |
| Store metadata and requirements | `docs/STORE_METADATA.md`, `status.csv` |
| Crash reporting | `docs/CRASHLYTICS.md` |
| Test file counts per app | the `measured: test_files` column of `status.csv` |
| Translations | `docs/I18N.md`, `docs/i18n-audit.json` (generated) |
| Per-app measured facts (67 fields × 43 rows) | `docs/release-readiness.json` |
| Per-app store checks, with each check's detail | `docs/store-checklist-detail.json` |
| What Apple holds: build and review state, per app | `docs/asc-build-state.json`, and the `apple: *` columns of `status.csv` |
| Verified account-deletion URLs | `docs/deletion-urls.json` |

`STATUS.md`, `status.csv`, `apps.json` and `docs/release-readiness.json` are
**measured, not maintained**. Do not hand-edit them — change the measuring
script and re-run it, or the file starts lying.

## Regenerating

```bash
python3 scripts/audit_release_readiness.py   # measures every repo -> release-readiness.json
python3 scripts/generate_manifest.py --out apps.json
python3 scripts/status.py                    # -> STATUS.md + status.csv  (needs GH_TOKEN)
python3 scripts/audit_i18n.py --print        # -> docs/i18n-audit.json (the table in docs/I18N.md)
```

## Building a signed Android release locally

```bash
python3 scripts/build_release.py            # every app
python3 scripts/build_release.py BodyQuest  # one app
```

Bundles land in `<app>/build/app/outputs/bundle/<flavour>Release/`, and every
one has its signing certificate compared against the upload keystore it was
supposed to use — a release build with a broken `signingConfig` silently falls
back to the debug key and only fails at upload.

**This build machine needs three things that are not obvious**, all handled by
that script; if you invoke Gradle by hand you must reproduce them:

1. The JVM's IPv6 `connect()` is denied with `EPERM`. Without
   `-Djava.net.preferIPv4Stack=true` Gradle reports *"Could not connect to the
   Gradle daemon"* and no build starts. Verified: a plain JVM loopback connect
   fails, the same connect with the flag succeeds.
2. Direct egress is blocked; the machine reaches the internet through a proxy on
   `127.0.0.1:10054`. The shell honours `HTTP_PROXY`, the JVM does not — it
   reads only `http.proxyHost`/`https.proxyHost` system properties.
3. Both the Gradle client and the Gradle daemon are separate JVMs and both need
   the above. `JAVA_TOOL_OPTIONS` is the only channel that reaches both;
   a project's `org.gradle.jvmargs` does not, and setting it also silently
   replaces the global `~/.gradle` value instead of merging with it.

None of this belongs in an app repository — it is true of this machine, not of
the app.

## Installing on the simulators

```bash
python3 scripts/sim_install.py CalcMaster          # build + install + launch, iOS and Android
python3 scripts/sim_install.py --all --android     # every app, one platform
python3 scripts/sim_install.py CalcMaster --skip-build --android-serial emulator-5560
```

Debug builds on a booted iPhone simulator and a running emulator (one is booted
if none is up). Another session may be using an emulator — pin yours with
`--android-serial`. Logs, screenshots and the JSON report go to
`<DIST>/sim-install/`.

For a sweep use `--all --clean-after`: each app's build output is 1.5-4 GB and
the disk filled during the first one. The script stops below `--min-free-gb`,
waits for other processes building in an app's folder (and takes a per-app
lock against other runs), makes room on a full emulator by uninstalling what
it installed earlier, and skips iOS for the rest of the run if the simulator
stops answering. Apps whose debug build adds `.debug` to the package need that
client in Firebase: `firebase_register.py --debug-variant`.

## Rules that have already cost something

- **Every action that talks to an external API belongs in `agl-manifest/scripts/`.**
  App Store Connect, Google Play, Firebase, AdMob, GitHub — all of it, committed
  and listed in `docs/API_ACTIONS.md`. Scripts once accumulated in an untracked
  `~/agl/.sweep/`: 27 of them, including the only working iOS IPA builder, none
  version-controlled and several duplicating something that already existed here.
  Run artifacts go to `~/agl/.dist/`; measured facts go to `docs/` and are
  committed. Before writing a new one, read `docs/API_ACTIONS.md` — extend the
  existing script rather than adding a second.

- **Never commit credentials.** `SFG-AGL-MobileApp_Devlopment-Tools.xlsx`,
  `*.p8`, keystores and `keystores.json` are gitignored and must stay that way.
  One of them reached GitHub once and is *still* fetchable at a dangling commit
  — see `docs/MANUAL_ACTIONS.md`. Never `git add -A` in this repo without
  reading `git status` first.
- **Do not run `dart format` as part of an unrelated change.** These repos do
  not enforce formatting, so it rewrites whole files: one pass buried 216 real
  changes under 5,048 lines of churn and had to be reverted.
- **Do not claim a build, test or upload happened without the output.** See
  `docs/DECISIONS.md` ADR-008.
- Bundle ids and package names are **permanent** once a store record exists.
  Check `status.csv` before renaming anything.

## Working set

The Flutter SDK to use is `/Users/spatchava/agl/.flutter-sdk/bin/flutter`
(3.44.2) — not the one on `PATH`. Shared packages live in `packages/`
(`agl_i18n`, `agl_observability`, `agl_ads`) and are consumed by apps as git
dependencies, which is why CI needs `AGL_PACKAGES_TOKEN` before anything builds.

## AI office

`ai-office/` is the AI organisation that runs this repo day to day: 41 roles
(`ai-office/.claude/agents/`), standing procedures (skills and workflows), the
charter of founder-only decisions, runbooks and reports. Open Claude Code in
`ai-office/` to work as the office; start with `ai-office/README.md`.
