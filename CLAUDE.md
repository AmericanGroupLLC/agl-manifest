# CLAUDE.md — American Group LLC mobile ecosystem

Entry point for an agent session. This file is an **index, not a description**:
it says where the answer lives so a session does not have to rediscover the
organisation. Read this, read what it points you at, and nothing else.

## What this is

| | |
| --- | --- |
| Org | `AmericanGroupLLC` (42 mobile apps, 1 backend, 1 website) |
| Control plane | this repo, `agl-manifest` |
| Backend | `AmericanGroupLLC-Backend` |
| Website | `https://www.safecodeg.com` |
| Stack | Flutter / Dart, targeting iOS and Android |
| Local mirror | `/Users/spatchava/agl/<repo>` — all org repos are cloned here |

Only `agl-manifest` runs CI. Per-repo Actions are deliberately disabled so the
org is not paying 37× for the same validation; see `docs/DELIVERY_ARCHITECTURE.md`.

## Where to look

| Question | File |
| --- | --- |
| What is the state of every app? | `STATUS.md` / `status.csv` (generated) |
| Which apps have a signed binary, and is it really signed? | `docs/build-evidence.json` (generated) |
| What must a human do that I cannot? | `docs/MANUAL_ACTIONS.md` |
| What is broken right now? | `docs/KNOWN_ISSUES.md` |
| Why is it built this way? | `docs/DECISIONS.md` |
| How does delivery work? | `docs/DELIVERY_ARCHITECTURE.md`, `docs/RELEASE_PIPELINE.md` |
| Package names, bundle ids, AdMob ids | `docs/APP_IDENTIFIERS.md`, `docs/admob-ids.json` |
| Store metadata and requirements | `docs/STORE_METADATA.md`, `docs/STORE_RELEASE_PLAYBOOK.md` |
| Crash reporting | `docs/CRASHLYTICS.md` |
| Translations | `docs/I18N.md` |
| Per-app measured facts (63 fields × 43 rows) | `docs/release-readiness.json` |

`STATUS.md`, `status.csv`, `apps.json` and `docs/release-readiness.json` are
**measured, not maintained**. Do not hand-edit them — change the measuring
script and re-run it, or the file starts lying.

## Regenerating

```bash
python3 scripts/audit_release_readiness.py   # measures every repo -> release-readiness.json
python3 scripts/generate_manifest.py --out apps.json
python3 scripts/status.py                    # -> STATUS.md + status.csv  (needs GH_TOKEN)
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

## Rules that have already cost something

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
  Check `docs/APP_IDENTIFIERS.md` before renaming anything.

## Working set

The Flutter SDK to use is `/Users/spatchava/agl/.flutter-sdk/bin/flutter`
(3.44.2) — not the one on `PATH`. Shared packages live in `packages/`
(`agl_i18n`, `agl_observability`, `agl_ads`) and are consumed by apps as git
dependencies, which is why CI needs `AGL_PACKAGES_TOKEN` before anything builds.
