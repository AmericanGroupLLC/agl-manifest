# Delivery architecture

Two repositories run the portfolio. Everything else is an app.

```
AmericanGroupLLC-Backend            agl-manifest                 37 app repos
─────────────────────────           ────────────────             ─────────────
the source of truth                 the delivery engine          the code

  packages/agl_i18n         ──┐       apps.json  ◄── generated     pubspec.yaml
  packages/agl_observability  ├─ git ─►                            lib/
  packages/agl_ads          ──┘       fastlane/Fastfile            fastlane/Fastfile
                                        validate                   .github/workflows/
  store/apps/<repo>.json ── renders ──►  batch                       ci.yml  (sanity only)
  store/defaults.json          into      publish_artifacts
                                                                   test/
  scripts/                            .github/workflows/             release_sanity_test.dart
    audit_release_readiness.py          validate.yml    nightly      ads_consent_test.dart
    generate_manifest.py     ─────────► deliver.yml     manual       i18n_test.dart
    store_metadata.py        ─────────► artifacts.yml   weekly
    agl_rollout.py                      sync-manifest.yml
```

## Who owns what

**The backend is the source of truth.** Not a document about the apps — a
measurement of them. `audit_release_readiness.py` reads all 42 repositories and
records what is actually there: where each Flutter project lives, its
application id, whether its release build has a real signing config, how many
locales it ships, whether its Fastlane uploads a mapping file. Everything
downstream is generated from that file, so a new app or a moved directory
reaches delivery by re-running the audit rather than by someone remembering to
edit a list.

It also holds the three shared Flutter packages and every word of store copy.

**The manifest is the delivery engine.** It owns no app and no identifier. It
checks apps out, runs their own Fastlane lanes, and publishes what comes out.

**The app repos hold code.** Their CI is one fast job on pull requests.

## The flow

```
  edit an app  ──►  pull request  ──►  sanity gate (~2 min, ubuntu)
                                         analyze --no-fatal-infos
                                         flutter test --tags sanity
                                            │
                                          merge
                                            │
                          nightly 06:00 UTC ▼
                    agl-manifest validate.yml
                      one ubuntu job: pub get + analyze + full suite × 37
                      one macOS job:  flutter build ios × 37
                                            │
                              when you want a build in someone's hands
                                            ▼
                    agl-manifest artifacts.yml
                      APK (sideloadable) + AAB → each app's GitHub Releases
                      simulator .app.zip for iOS
                                            │
                                  when you want to ship
                                            ▼
                    agl-manifest deliver.yml
                      beta    → TestFlight / Play internal   (no approval)
                      release → App Store / Play production  (production
                                environment → required reviewers)
```

## Where the CI minutes go, and why this is cheaper

The analyzing and testing is the same work wherever it runs. The saving is in
the fixed costs, which used to be paid 37 times per push:

| Paid per job | Before | Now |
| --- | --- | --- |
| Runner boot + checkout | 37× per push | 1× nightly |
| Flutter SDK download | 37× | 1× per runner, cached |
| Cold pub cache | 37× | 1 shared cache |
| CocoaPods spec fetch | 37× | 1 shared cache |
| **macOS runner (bills at 10×)** | **37 jobs** | **1 job** |

Three structural choices do the work:

1. **No `push` trigger in the app repos.** A pull request gets a two-minute
   ubuntu job. Merging costs nothing; the nightly batch covers the branch.
2. **One macOS job for the whole portfolio.** This is the largest single change.
   A macOS minute costs ten, so 37 macOS jobs dominated everything else
   combined.
3. **One `bundle install`.** The batch runs each app's lanes with
   `BUNDLE_GEMFILE` pointing at the manifest, so fastlane and its 94 gems are
   installed once.

The sanity gate is what makes dropping per-push builds safe. It is fast because
it reads files instead of pumping widgets, and it checks the things that a
green build does not: a missing `GADApplicationIdentifier` (iOS terminates the
app on every launch), a release buildType still on the debug key (Play rejects
the upload), a version with no `+N` (Play has nothing to increment), a privacy
manifest that exists but is not in the Runner target (never reaches the `.app`).

## Legacy workflows still on `push`

Five repositories carried a second Flutter pipeline that duplicated the standard
one — DriftDate, GroceryMatch, Kinnav, PilotEnRoute and yourtube — three of them
booting a macOS runner on every push. They are now `workflow_dispatch` only,
left in place rather than deleted in case one carries a step the standard
pipeline does not.

**27 other push-triggered workflows remain, and are deliberately untouched.**
They are separate deliverables, not duplicates, and deleting them is a product
decision rather than a pipeline one:

| Repo | Workflows |
| --- | --- |
| MyHealth | `android.yml`, `ios.yml`, `backend.yml`, `deploy.yml`, `desktop.yml`, `eas-build.yml`, `expo.yml`, `marketing.yml` |
| DriftDate | `android.yml`, `ios.yml`, `backend.yml`, `desktop.yml`, `pwa.yml`, `web-release.yml`, `marketing.yml`, `i18n-gate.yml`, `secret-scan.yml` |
| NearServe | `android-build.yml`, `ios-build.yml`, `server-deploy.yml`, `web-deploy.yml` |
| CalcMaster | `deploy.yml`, `pages.yml` |
| Uscis-Case | `release-android.yml` |
| NexusTransferPay | `release-web.yml` |
| iMeasure | `web-deploy.yml` |
| PilotEnRoute | `deploy-website.yml` |

Worth a look: MyHealth's `expo.yml` and `eas-build.yml`, and the `desktop.yml`
and `pwa.yml` pairs, date from before those apps were Flutter. If those trees
are gone the jobs are burning minutes to fail.

## Builds people can actually run

`artifacts.yml` attaches to each app's GitHub Releases:

- **`app-release.apk`** — installs on a device. A `.aab` cannot be sideloaded;
  it is a Play upload format, which is why both are published.
- **`<App>-simulator.app.zip`** — unsigned, so it will not run on a phone.
  Unzip and drag onto a running iOS Simulator. TestFlight is the only route to
  real hardware.

Releases are drafts and marked pre-release. Nothing there is a store
submission.

## Secrets

One organization secret carries most of it:

| Secret | Used for | Scope |
| --- | --- | --- |
| `AGL_PACKAGES_TOKEN` | cloning app repos; `flutter pub get` reaching the shared packages in the **private** backend | read on all app repos + the backend; **write** as well if you publish releases |

Without it, every job fails at `flutter pub get` with `could not read Username
for 'https://github.com'` — which is exactly what took 35 of 37 repos red. Each
workflow checks for it in its **first** step and says so, before spending two
minutes installing a toolchain it is about to waste.

Store credentials (`ASC_*`, `PLAY_SERVICE_ACCOUNT_JSON`, `ANDROID_KEYSTORE_*`,
`MATCH_*`, `ADMOB_*`) are listed in
`status.csv` §7.

## Keeping it honest

```sh
python3 scripts/audit_release_readiness.py                       # measure
python3 scripts/generate_manifest.py --out ../agl-manifest/apps.json
python3 scripts/store_metadata.py generate                       # listings
```

`sync-manifest.yml` runs weekly and fails if `apps.json` names a repository the
org no longer has, warning if the org has one the manifest does not — which is
how a newly ported app announces itself.

## Automatic tester sync and build distribution (2026-09-22)

Three workflows, each with one job:

| Workflow | Runs when | Does |
| --- | --- | --- |
| `distribute-on-tag.yml` | a `v*` tag is pushed, or on demand | calls `deliver.yml` for android and ios on the `beta` lane, then `sync-testers.yml` |
| `deliver.yml` | on demand, or called | builds and ships the selected apps; `release` still sits behind the `production` environment |
| `sync-testers.yml` | every six hours, on demand, called, or after a Deliver run | puts every App Store Connect account user in every tester list |

Nothing on the tag path reaches App Store review or a Play production release.
A tagged build goes to TestFlight and Play's internal track, and the tester sync
puts it in front of everyone on the account.

The roster is `GET /v1/users` merged with the existing beta testers. It is
written to `.dist/tester-roster.json` and applied by
`scripts/testflight/distribute.rb --sync` on Apple and
`scripts/sync_play_testers.py` on Play. Both are idempotent, so a run that
changes nothing says so.

Two platform limits shape the design, measured on 2026-09-22 rather than assumed:
TestFlight internal groups refuse API tester assignment even for the account
holder, so an external group carries the roster and Apple reviews each build
before testers get it; and Play's internal track accepts Google Groups rather
than individual addresses. MA-018 lists the secrets that finish the Android half.
