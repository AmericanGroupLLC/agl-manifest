# Delivery path audit — 43 app repos

Measured **2026-09-13** against the working copies in `/Users/spatchava/agl`, driven by the 43 entries in
`agl-manifest/apps.json`. Every cell below was produced by parsing the actual files (GitHub Actions
YAML, Fastfiles, `build.gradle[.kts]`, `pubspec.yaml`). Nothing here is taken from a repo's prose.
The commands used are listed under *Method* at the end.

## Headline

| Question | Answer |
| --- | --- |
| Every app repo has a CI workflow? | **No.** 37/43 have a real Flutter sanity gate. `AeroSwift` and `PlantPulse` have no `ci.yml` at all. `AGStudio`, `ApexMarketWatch`, `BuddyPlay`, `MyCard` have a legacy Expo/Jest `ci.yml` that runs no Flutter and ends every test step with `\|\| true`, so it cannot fail. |
| Every app repo has a release workflow? | A `release.yml` file exists in 43/43. 39 drive the app's own Fastlane lanes, 2 (`CalcMaster`, `Kinnav`) build directly with `flutter build` and no Fastlane, 2 (`BuddyPlay`, `MyCard`) are native Gradle/xcodegen leftovers that never touch the Flutter app. |
| **The `ruby/setup-ruby` trap** — subdirectory apps | 17 apps live in a subdirectory. 15 of their `release.yml` files use `ruby/setup-ruby`; **14 already carry their own `working-directory`** matching `apps.json`. The one that does not (`AGStudio`) is a wholesale-wrong workflow, not a missing input. **The trap is closed everywhere the standard workflow is installed.** |
| Second-Fastfile trap | 8 of the 17 subdirectory repos keep an extra `fastlane/Fastfile` at the repo root. 2 are the `cd ..` kind that cannot build (`CodeDeal`, `NexusTransferPay`); 6 are shadows that the delivery path never reaches. |
| `google-services.json` at `<dir>/android/app/` | **0 / 43** |
| `GoogleService-Info.plist` at `<dir>/ios/Runner/` | **0 / 43** |
| Firebase Gradle plugins guarded by `if (file("google-services.json").exists())` | **42 / 42 that apply them. Zero unguarded.** `FashionFactory` applies none, per its own no-crash-SDK policy. |

## Per-app table

Legend

- **CI** — `flutter`: real gate (`flutter analyze` + `flutter test`). `legacy`: Expo/Jest leftover, no Flutter step. `absent`: no `ci.yml`.
- **Rel** — `fastlane`: runs the app's own lanes. `flutter-direct`: `flutter build` with no Fastlane. `legacy`: native Gradle/xcodegen leftover.
- **wd ok** — job-level `defaults.run.working-directory` equals the app's `dir` in `apps.json`.
- **setup-ruby wd** — the `ruby/setup-ruby` step carries `with.working-directory` equal to `dir`.
- **root Fastfile** (subdirectory apps only) — `cd ..`: a root Fastfile whose lanes `cd ..` into a directory with no `pubspec.yaml`. `shadow`: a root Fastfile that the delivery path never invokes.
- `—` means the check does not apply.

| App | dir | CI | CI wd | Rel | Rel wd | setup-ruby wd | Fastfile at dir | Gemfile at dir | root Fastfile | g-s.json | GSI.plist | gradle guard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AeroSwift` | `mobile` | **absent** | — | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `AGCleaner` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `AGrammarly` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | shadow | **no** | **no** | yes |
| `AGRecorder` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `AGStudio` | `mobile` | **legacy** | — | fastlane | **no** | **no** | **no** | **no** | shadow | **no** | **no** | yes |
| `ApexMarketWatch` | `mobile` | **legacy** | — | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `BodyQuest` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `BuddyPlay` | `mobile` | **legacy** | — | **legacy** | — | — | **no** | **no** | shadow | **no** | **no** | yes |
| `CalcMaster` | `.` | flutter | yes | flutter-direct | — | — | yes | yes | — | **no** | **no** | yes |
| `CarDeal` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `ChefCount` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `CodeDeal` | `mobile/codedeal_app` | flutter | yes | fastlane | yes | yes | **no** | **no** | **cd ..** | **no** | **no** | yes |
| `daily-pulse` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `DriftDate` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `EventSpark` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `FashionFactory` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | — |
| `GadgetNest` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `GroceryMatch` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `HerJourney` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `HomeWise` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `iMaps` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `iMeasure` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `Kinnav` | `.` | flutter | yes | flutter-direct | — | — | yes | yes | — | **no** | **no** | yes |
| `MileMaster` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `MyCard` | `mobile` | **legacy** | — | **legacy** | — | — | **no** | **no** | shadow | **no** | **no** | yes |
| `MyFinance` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `MyHealth` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `NearServe` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | shadow | **no** | **no** | yes |
| `NewsBoard` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | shadow | **no** | **no** | yes |
| `NexusTransferPay` | `flutter-mobile-app` | flutter | yes | fastlane | yes | yes | yes | yes | **cd ..** | **no** | **no** | yes |
| `Photriya` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `PilotEnRoute` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `PlantPulse` | `mobile` | **absent** | — | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `portfolio-board` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `radiotune` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `RideZap` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `RoomCraft` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `TripNest` | `mobile` | flutter | yes | fastlane | yes | yes | yes | yes | none | **no** | **no** | yes |
| `Uscis-Case` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `Verba` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `VirtuBand` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `WiFiTrail` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |
| `yourtube` | `.` | flutter | yes | fastlane | yes | yes | yes | yes | — | **no** | **no** | yes |

## What is actually broken, ranked

### 1. Nothing in the portfolio can report a crash — 43 apps

`google-services.json` exists at `<dir>/android/app/` in **0 of 43** apps.
`GoogleService-Info.plist` exists at `<dir>/ios/Runner/` in **0 of 43** apps.

The only two files of either name anywhere in any repo are in `MyHealth`, and neither is
in a location any tool reads:

```
MyHealth/google-services.json                       (repo root, not android/app/)
MyHealth/expo_legacy/android/app/google-services.json
```

`MyHealth/google-services.json` is a placeholder, not a real config:
`"project_number": "000000000000"`, `"project_id": "myhealth-local-dev"`,
`"current_key": "AIzaSyDUMMYKEYFORLOCALDEVELOPMENTONLY00000"`.

**Consequence, stated plainly.** Every downstream piece of the crash-reporting chain is
correctly built and every one of them silently does nothing:

- **Android.** The `com.google.gms.google-services` and `com.google.firebase.crashlytics`
  plugins sit inside `if (file("google-services.json").exists())`. The file is absent, so
  the block never runs: no Firebase project is linked into the APK, and the Crashlytics
  Gradle plugin — the thing that uploads the R8 `mapping.txt` — is never applied. A
  release AAB therefore ships with no Firebase config and no deobfuscation mapping.
- **iOS.** The standard Fastfile's `upload_dsyms` lane begins with
  `unless File.exist?(plist) ... UI.important("No GoogleService-Info.plist — skipping dSYM upload.")`
  (`TripNest/mobile/fastlane/Fastfile:146-150`, and the same in every standard Fastfile).
  So the dSYM upload is skipped on every single build. It does not fail; it prints an
  informational line and moves on.
- **Dart.** Only 7 of 43 apps even declare `firebase_crashlytics` in `pubspec.yaml`
  (`ApexMarketWatch`, `CarDeal`, `GadgetNest`, `MyHealth`, `RoomCraft`, `Verba`,
  `WiFiTrail`). Two more declare `firebase_core` alone (`GroceryMatch`, `Photriya`).
  Two use Sentry instead (`DriftDate`, `NexusTransferPay`) and so do not need these files —
  `NexusTransferPay/flutter-mobile-app/lib/main.dart:55` reads the DSN from
  `String.fromEnvironment('SENTRY_DSN', defaultValue: '')` and skips init when empty.

Net: **0 apps can deliver a crash report to Firebase, and 0 apps would produce a readable
stack trace if they could.** The wiring is not the problem. The 86 missing files are.
Nothing in the release path will tell you this — every check degrades quietly.

### 2. Four apps cannot be delivered at all — `AGStudio`, `BuddyPlay`, `CodeDeal`, `MyCard`

These four have their Flutter project in a subdirectory and **no `fastlane/Fastfile` and no
`Gemfile` at that directory**:

| App | dir | Fastfile at dir | Gemfile at dir | Where the only Fastfile is |
| --- | --- | --- | --- | --- |
| `AGStudio` | `mobile` | no | no | `AGStudio/fastlane/Fastfile` (React Native, `aQuantum`/`iQuantum`) |
| `BuddyPlay` | `mobile` | no | no | `BuddyPlay/fastlane/Fastfile` (native `ios/BuddyPlay.xcodeproj`, `android/`) |
| `CodeDeal` | `mobile/codedeal_app` | no | no | `CodeDeal/fastlane/Fastfile` (`sh("cd .. && flutter …")`) |
| `MyCard` | `mobile` | no | no | `MyCard/fastlane/Fastfile` (native `Card/ios/Card.xcodeproj`) |

Fastlane does **not** search parent directories. `FastlaneCore::FastlaneFolder.path`
(`fastlane-2.239.0/fastlane_core/lib/fastlane_core/fastlane_folder.rb:8-16`) checks only
`./fastlane/` and `./.fastlane/` in the current working directory. Reproduced in an empty
directory:

```
$ cd /tmp/aglaudit/nofast && BUNDLE_GEMFILE=.../agl-manifest/Gemfile bundle exec fastlane android beta
Could not find fastlane in current directory. Make sure to have your fastlane
configuration files inside a folder called "fastlane".
EXIT=1
```

So both delivery routes fail for these four:

- **Manifest batch.** `agl-manifest/fastlane/Fastfile` `in_app` does
  `cd work/<repo>/<dir> && … bundle exec fastlane <platform> <lane>`. That directory has no
  `fastlane/`, so `batch` fails with the error above. `validate` still works for them —
  it only runs `flutter pub get/analyze/test`, and `pubspec.yaml` is there.
- **Per-repo `release.yml`.** `CodeDeal`'s is the correct standard workflow with
  `working-directory: mobile/codedeal_app` on both the job and `ruby/setup-ruby` — and it
  fails one step earlier, at `setup-ruby` with `bundler-cache: true`, because there is no
  `Gemfile` there either. `AGStudio`'s `release.yml` is a leftover React Native pipeline
  (`pnpm install --frozen-lockfile`, `cd ios && pod install`, no `working-directory`
  anywhere) and its `ruby/setup-ruby` has no Gemfile at the repo root to cache.
  `BuddyPlay`'s and `MyCard`'s `release.yml` are 12-job native Gradle/xcodegen pipelines
  with no Fastlane step at all.

`MyCard`'s is the worst of the four: its `release.yml` drives `android/`, `ios/`,
`watchos/` and `release.config.json` at the repo root, and **none of those exist** — only
`desktop/` does.

**Not mechanical. Left alone.** Each needs a standard Fastfile + Gemfile generated into
the app directory and the legacy workflow replaced — that is a generation decision for
`AmericanGroupLLC-Backend`, not a YAML tweak.

### 3. Six apps have no working PR sanity gate

| App | Problem |
| --- | --- |
| `AeroSwift` | No `ci.yml`. Only `release.yml` exists. |
| `PlantPulse` | No `ci.yml`. Only `release.yml` exists. |
| `AGStudio` | `ci.yml` is Expo/Jest: `npm test -- --passWithNoTests --forceExit 2>&1 \|\| true`. No Flutter. Cannot fail. |
| `ApexMarketWatch` | Same file, same `\|\| true`. Its `release.yml` *is* correct — only CI is stale. |
| `BuddyPlay` | Same. |
| `MyCard` | Same. |

The four `legacy` files are byte-for-byte the same template with the app name substituted.
Their "Platform simulation summary" step just `echo`s a bundle id. A green check on these
four means nothing was tested.

### 4. Two root Fastfiles that `cd ..` into a directory with no `pubspec.yaml`

- `CodeDeal/fastlane/Fastfile:5,9,33,37` — `sh("cd .. && flutter test --coverage")`,
  `sh("cd .. && flutter build ipa --release")`, etc. `fastlane`'s `sh` runs from the
  `fastlane/` directory, so `cd ..` lands on the repo root. `CodeDeal`'s `pubspec.yaml` is
  at `mobile/codedeal_app/pubspec.yaml`. Every lane fails. This is also the *only*
  Fastfile in the repo (see finding 2).
- `NexusTransferPay/fastlane/Fastfile:5,9,27` — same `cd ..` pattern landing on the repo
  root while `pubspec.yaml` is at `flutter-mobile-app/`. It additionally still contains
  unsubstituted template placeholders: `ipa: "../build/ios/ipa/{{APP_NAME}}.ipa"` and
  `groups: ["{{TESTFLIGHT_GROUP}}"]`. **The delivery path does not reach it** —
  `flutter-mobile-app/fastlane/Fastfile` is the standard one and both the workflow and the
  manifest `cd` there — so this is a trap for a human running `bundle exec fastlane` from
  the repo root, not a live break.

### 5. Six shadow Fastfiles at the root of subdirectory repos

`AGrammarly`, `AGStudio`, `BuddyPlay`, `MyCard`, `NearServe`, `NewsBoard` each keep a root
`fastlane/Fastfile` that the delivery path never invokes. They are not `cd ..` Fastfiles;
they use Fastlane's native actions with repo-root-relative paths. Three of them point at
paths that do not exist:

- `NearServe/fastlane/Fastfile:11,19` — `ios/urbanapp.xcworkspace`; `:45` — `project_dir: "android/"`. Neither exists; `NearServe`'s Flutter app is in `mobile/`.
- `BuddyPlay/fastlane/Fastfile:11,22` — `ios/BuddyPlay.xcodeproj` (a legacy native project, not the Flutter app).
- `MyCard/fastlane/Fastfile:11,22,39` — `Card/ios/Card.xcodeproj`, `Card/android/`.

`AGrammarly` and `NewsBoard` root Fastfiles use `mobile/...` paths that do resolve, so they
are merely duplicates drifting out of sync with the real `mobile/fastlane/Fastfile`.

For `AGStudio`, `BuddyPlay` and `MyCard` this shadow is not harmless — it is the *only*
Fastfile, so anything that finds it builds the wrong app (see finding 2).

### 6. Two invalid workflow YAML files — FIXED

Both files failed to parse at all, which means GitHub would reject the workflow outright.
Fixed, because each is a one-character mechanical syntax repair:

| Repo | File | Cause | Commit |
| --- | --- | --- | --- |
| `NearServe` | `.github/workflows/ios-build.yml:50` | `APP_STORE_CONNECT_API_KEY_ISSUER_ID:${{ … }}` — no space after the colon, so YAML reads the line as a plain scalar, not a mapping entry | `9ae3d91` on `production-readiness-2026-09-12` |
| `portfolio-board` | `.github/workflows/refresh-dashboard.yml:91` | `- name: Tear down Z: drive mapping` — the unquoted second colon gives `mapping values are not allowed in this context` | `71c6997` on `production-readiness-2026-09-12` |

After the fixes, **all 138 workflow YAML files across the 43 repos parse.** Neither file is
in the delivery path; both are legacy workflows in repos where Actions is disabled.

### 7. 41 of 43 apps have a `Gemfile` with no `Gemfile.lock`

Only `CalcMaster` and `Kinnav` have a lockfile at the app directory. `ruby/setup-ruby` with
`bundler-cache: true` will still resolve and install, so this is not a break — but the
Fastlane version each app repo installs is unpinned and can drift from the `~> 2.230` the
manifest pins in `agl-manifest/Gemfile`. Low severity, worth closing when the Fastfiles
are next regenerated.

## Things that are genuinely intact

Recording these so nobody re-opens them:

- **The `ruby/setup-ruby` `working-directory` trap is closed.** All 14 subdirectory apps
  running the standard `deliver` workflow carry `with.working-directory: <dir>` on the
  `ruby/setup-ruby` step *and* `defaults.run.working-directory: <dir>` on the job. There
  were no instances of the classic "job default set, action input forgotten" failure to fix.
- **Action inputs that take paths are repo-root-relative and written that way.**
  `CodeDeal/.github/workflows/release.yml` uploads
  `path: mobile/codedeal_app/build/app/outputs/mapping/release/mapping.txt`, and
  `NexusTransferPay/.github/workflows/release-mobile.yml` uses
  `flutter-mobile-app/build/...`. Correct idiom.
- **Every Firebase Gradle plugin application is guarded.** 42 apps apply
  `com.google.gms.google-services` and `com.google.firebase.crashlytics`, and in all 42 the
  `apply` sits inside `if (file("google-services.json").exists())`. Zero unguarded
  applications anywhere, in either Groovy or Kotlin DSL. No app-level `plugins { id(...) }`
  block applies them without `apply false`. This is exactly why the absent config files
  cause silence rather than a red build.
- **38 of 43 release workflows are correctly pointed at the app.** Job `working-directory`,
  `setup-ruby` `working-directory`, and an existing standard Fastfile with
  `test`/`build`/`beta`/`release`/`production` lanes.
- **The manifest side is consistent.** `agl-manifest/fastlane/Fastfile` `app_path` derives
  the app directory from `apps.json`, `in_app` strips the bundler env for Flutter and
  reapplies it for Fastlane, and `run_batch` collects every failure instead of stopping at
  the first. `agl-manifest/.github/workflows/` has `validate.yml`, `deliver.yml`,
  `artifacts.yml`, `status.yml`, `sync-manifest.yml`, all parsing.

## Caveat on the whole audit

Every app-repo `ci.yml` and `release.yml` except the four legacy ones opens with:

```
# GitHub Actions is DISABLED for this repository.
```

**I could not verify the actual Actions-enabled state on GitHub** — that requires a network
call and this audit was done entirely against local working copies. If Actions really is
disabled org-wide for the app repos, then the "short sanity gate on pull requests" is not
running anywhere today, and findings 3 and 6 are latent rather than active. Findings 1, 2,
4 and 5 are unaffected: they break the `agl-manifest` batch path too, which is the path
that is supposed to be running.

## Method

Everything above came from these, run on 2026-09-13 against `/Users/spatchava/agl`:

- Workflow YAML parsed with Ruby's `YAML.safe_load` (138 files across 43 repos), extracting
  per job: `runs-on`, `defaults.run.working-directory`, every step's `uses`/`with`/`run`,
  and every action input whose name matches `path|file|dir|gemfile|cache-dependency`.
- `apps.json` is the source of truth for each app's `dir`; every `working-directory` was
  compared against it rather than against a guess.
- Fastfile locations by `find`; `cd ..` lanes by reading each root Fastfile in full.
- Firebase config presence tested at the two canonical paths
  (`<dir>/android/app/google-services.json`, `<dir>/ios/Runner/GoogleService-Info.plist`)
  and, separately, by a recursive glob over each whole repo so nothing in a non-standard
  location was missed.
- Gradle guard checked by locating every line matching
  `^apply\s*\(?\s*plugin\s*[=:].*(com\.google\.gms\.google-services|com\.google\.firebase\.crashlytics)`
  and requiring `exists()` in the six lines above it; separately, every
  `id("com.google.…")` in a `plugins` block was checked for `apply false`.
- Fastlane's directory resolution read from the installed gem source at
  `fastlane-2.239.0/fastlane_core/lib/fastlane_core/fastlane_folder.rb` and confirmed by
  running `bundle exec fastlane android beta` in an empty directory (exit 1).

No Flutter analyze or test run was part of this audit; `analyzeExit` and `testExit` are
reported as not-run.
